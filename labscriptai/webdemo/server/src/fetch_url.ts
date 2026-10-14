import http from "node:http";
import https from "node:https";
import { lookup } from "node:dns/promises";
import { isIP } from "node:net";
import { URL } from "node:url";

export const FETCH_URL_MS = 20_000;
export const FETCH_URL_BODY_CAP = 80_000;
export const FETCHED_PAGE_PROMPT_CAP = 12_000;
export const BLOCKED_PORTS = new Set([8010, 31950, 4880, 3190, 8787]);

export type FetchUrlOk = { ok: true; url: string; chars: number; body: string };
export type FetchUrlFail = { ok: false; blocked?: boolean; error: string; hint: string };
export type FetchUrlResult = FetchUrlOk | FetchUrlFail;

export type SearchHit = { title: string; url: string; snippet: string };
export type WebSearchOk = { ok: true; query: string; hits: SearchHit[] };
export type WebSearchResult = WebSearchOk | FetchUrlFail;

export type FetchedPage = { url: string; chars: number; body: string };

const PRIVATE_V4 = /^(0\.|10\.|127\.|169\.254\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)/;
const SEARCH_UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36";

export function ipv4Private(address: string): boolean {
  return PRIVATE_V4.test(address);
}

export function ipv6Private(address: string): boolean {
  const host = address.toLowerCase().replace(/^\[|\]$/g, "");
  if (host === "::1" || host === "0:0:0:0:0:0:0:1") return true;
  if (host.startsWith("fe80:") || host.startsWith("fc") || host.startsWith("fd")) return true;
  const mapped = host.match(/::ffff:(\d+\.\d+\.\d+\.\d+)$/i);
  return Boolean(mapped && ipv4Private(mapped[1]));
}

export function hostnameLooksLocal(hostname: string): boolean {
  const host = hostname.replace(/^\[|\]$/g, "").toLowerCase();
  if (!host || host === "localhost" || host === "::1" || host === "0.0.0.0") return true;
  if (host.endsWith(".local") || host.endsWith(".localhost") || host.endsWith(".internal")) return true;
  const ip = isIP(host);
  if (ip === 4) return ipv4Private(host);
  if (ip === 6) return ipv6Private(host);
  return false;
}

function envProxy(): URL | null {
  const raw = (
    process.env.HTTPS_PROXY ||
    process.env.https_proxy ||
    process.env.ALL_PROXY ||
    process.env.all_proxy ||
    process.env.HTTP_PROXY ||
    process.env.http_proxy ||
    ""
  ).trim();
  if (!raw) return null;
  try {
    const url = new URL(raw);
    if (url.protocol !== "http:" && url.protocol !== "https:") return null;
    return url;
  } catch {
    return null;
  }
}

export async function assertPublicHttpUrl(raw: string): Promise<{ url: URL } | FetchUrlFail> {
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    return { ok: false, blocked: true, error: "invalid_url", hint: "Pass a full http(s) URL." };
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    return { ok: false, blocked: true, error: "scheme_blocked", hint: "Only http and https are allowed." };
  }
  const port = url.port ? Number(url.port) : url.protocol === "https:" ? 443 : 80;
  if (BLOCKED_PORTS.has(port)) {
    return {
      ok: false,
      blocked: true,
      error: "port_blocked",
      hint: `Port ${port} is reserved for local robots and backends. Use public pages only.`,
    };
  }
  if (hostnameLooksLocal(url.hostname)) {
    return {
      ok: false,
      blocked: true,
      error: "host_blocked",
      hint: "Localhost, private, and link-local addresses are blocked.",
    };
  }
  try {
    const answers = await lookup(url.hostname, { all: true });
    if (answers.some((row) => hostnameLooksLocal(row.address))) {
      return {
        ok: false,
        blocked: true,
        error: "host_blocked",
        hint: "That hostname resolves to a private or loopback address.",
      };
    }
  } catch {
    return { ok: false, blocked: true, error: "unresolved", hint: "Could not resolve the hostname." };
  }
  return { url };
}

export function stripHtml(text: string): string {
  return text
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
    .replace(/\s+/g, " ")
    .trim();
}

function decodeDuckHref(href: string, base: string): string {
  try {
    const abs = new URL(href, base);
    const uddg = abs.searchParams.get("uddg");
    return uddg ? uddg : abs.href;
  } catch {
    return href;
  }
}

/** Parse DuckDuckGo html.duckduckgo.com result cards. */
export function parseSearchHtml(html: string, base = "https://html.duckduckgo.com"): SearchHit[] {
  const hits: SearchHit[] = [];
  const seen = new Set<string>();
  const blockRe =
    /class="result__a"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>[\s\S]{0,1200}?class="result__snippet"[^>]*>([\s\S]*?)<\/a>/gi;
  let match: RegExpExecArray | null;
  while ((match = blockRe.exec(html)) && hits.length < 8) {
    const url = decodeDuckHref(match[1].replace(/&amp;/g, "&"), base);
    if (!url.startsWith("http") || seen.has(url)) continue;
    seen.add(url);
    hits.push({
      title: stripHtml(match[2]).slice(0, 200),
      url,
      snippet: stripHtml(match[3]).slice(0, 400),
    });
  }
  return hits;
}

type WireResponse = {
  status: number;
  header(name: string): string;
  text(): Promise<string>;
};

function headerValue(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return value ?? "";
}

function directRequest(
  target: URL,
  method: string,
  headers: Record<string, string>,
  body: string | undefined,
  signal: AbortSignal
): Promise<WireResponse> {
  return fetch(target, { method, headers, body, redirect: "manual", signal }).then((response) => ({
    status: response.status,
    header: (name: string) => response.headers.get(name) ?? "",
    text: () => response.text(),
  }));
}

function proxyRequest(
  proxy: URL,
  target: URL,
  method: string,
  headers: Record<string, string>,
  body: string | undefined,
  signal: AbortSignal
): Promise<WireResponse> {
  const port = target.port || (target.protocol === "https:" ? "443" : "80");
  const send = (socket: import("node:stream").Duplex | undefined) =>
    new Promise<WireResponse>((resolve, reject) => {
      const lib = target.protocol === "https:" ? https : http;
      const req = lib.request(
        {
          protocol: target.protocol,
          host: target.hostname,
          port,
          path: `${target.pathname}${target.search}` || "/",
          method,
          headers,
          agent: false,
          servername: target.hostname,
          socket,
          signal,
        } as http.RequestOptions,
        (response) => {
          const chunks: Buffer[] = [];
          response.on("data", (chunk: Buffer) => chunks.push(chunk));
          response.on("end", () => {
            const text = Buffer.concat(chunks).toString("utf8");
            resolve({
              status: response.statusCode || 0,
              header: (name: string) => headerValue(response.headers[name.toLowerCase()]),
              text: async () => text,
            });
          });
        }
      );
      req.on("error", reject);
      if (body) req.write(body);
      req.end();
    });

  if (target.protocol === "http:") {
    return new Promise((resolve, reject) => {
      const req = http.request(
        {
          host: proxy.hostname,
          port: proxy.port || 80,
          method,
          path: target.href,
          headers: { ...headers, Host: target.host },
          signal,
        },
        (response) => {
          const chunks: Buffer[] = [];
          response.on("data", (chunk: Buffer) => chunks.push(chunk));
          response.on("end", () => {
            const text = Buffer.concat(chunks).toString("utf8");
            resolve({
              status: response.statusCode || 0,
              header: (name: string) => headerValue(response.headers[name.toLowerCase()]),
              text: async () => text,
            });
          });
        }
      );
      req.on("error", reject);
      if (body) req.write(body);
      req.end();
    });
  }

  return new Promise((resolve, reject) => {
    const connect = http.request({
      host: proxy.hostname,
      port: proxy.port || 80,
      method: "CONNECT",
      path: `${target.hostname}:${port}`,
      headers: { Host: `${target.hostname}:${port}` },
      signal,
    });
    connect.on("error", reject);
    connect.on("connect", (res, socket, head) => {
      if (res.statusCode !== 200) {
        socket.destroy();
        reject(new Error(`proxy CONNECT ${res.statusCode ?? "failed"}`));
        return;
      }
      if (head.length) socket.unshift(head);
      send(socket).then(resolve, reject);
    });
    connect.end();
  });
}

async function requestPublic(
  target: URL,
  method: string,
  headers: Record<string, string>,
  body?: string,
  timeoutMs = FETCH_URL_MS
): Promise<WireResponse> {
  const signal = AbortSignal.timeout(timeoutMs);
  const proxy = envProxy();
  if (!proxy) return directRequest(target, method, headers, body, signal);
  return proxyRequest(proxy, target, method, headers, body, signal);
}

function networkFail(error: unknown, hint: string): FetchUrlFail {
  const name = error instanceof Error ? error.name : "";
  if (name === "AbortError" || name === "TimeoutError") {
    return { ok: false, error: "timeout", hint };
  }
  return {
    ok: false,
    error: "network",
    hint: error instanceof Error ? error.message : hint,
  };
}

export async function searchPublicWeb(query: string): Promise<WebSearchResult> {
  const q = query.trim().slice(0, 300);
  if (!q) return { ok: false, error: "empty_query", hint: "Pass a search query." };
  const raw = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(q)}`;
  const checked = await assertPublicHttpUrl(raw);
  if (!("url" in checked)) return checked;
  try {
    const response = await requestPublic(checked.url, "GET", {
      Accept: "text/html",
      "Accept-Encoding": "identity",
      "User-Agent": SEARCH_UA,
    });
    const html = (await response.text()).slice(0, FETCH_URL_BODY_CAP);
    if (response.status === 202 || /bots use DuckDuckGo/i.test(html)) {
      return {
        ok: false,
        error: "search_blocked",
        hint: "DuckDuckGo asked for a human check. Try again, or pass a URL to fetch_url.",
      };
    }
    if (response.status < 200 || response.status >= 300) {
      return { ok: false, error: `http_${response.status}`, hint: `Search returned ${response.status}.` };
    }
    return { ok: true, query: q, hits: parseSearchHtml(html, checked.url.href) };
  } catch (error) {
    return networkFail(error, "DuckDuckGo search timed out.");
  }
}

function looksBinary(contentType: string, head: string): boolean {
  if (
    contentType.includes("pdf") ||
    contentType.includes("octet-stream") ||
    contentType.startsWith("image/") ||
    contentType.includes("zip")
  ) {
    return true;
  }
  return head.startsWith("%PDF") || head.startsWith("data:application/pdf");
}

function pageText(raw: string, contentType: string): string {
  const sliced = raw.slice(0, FETCH_URL_BODY_CAP);
  const html = contentType.includes("html") || /^\s*</.test(sliced);
  if (!html) return sliced;
  const paras = [...sliced.matchAll(/<p\b[^>]*>([\s\S]*?)<\/p>/gi)]
    .map((match) => stripHtml(match[1]))
    .filter((paragraph) => paragraph.length > 40);
  if (paras.length >= 2) return paras.join("\n\n").slice(0, FETCH_URL_BODY_CAP);
  return stripHtml(sliced).slice(0, FETCH_URL_BODY_CAP);
}

export async function fetchPublicUrl(raw: string, hops = 0): Promise<FetchUrlResult> {
  const checked = await assertPublicHttpUrl(raw);
  if (!("url" in checked)) return checked;
  if (hops > 4) {
    return { ok: false, blocked: true, error: "redirect_limit", hint: "Too many redirects." };
  }
  try {
    const response = await requestPublic(checked.url, "GET", {
      Accept: "text/html,text/plain,application/json,text/markdown,*/*",
      "Accept-Encoding": "identity",
      "User-Agent": SEARCH_UA,
    });
    const location = response.header("location");
    if (location && response.status >= 300 && response.status < 400) {
      return fetchPublicUrl(new URL(location, checked.url).href, hops + 1);
    }
    if (response.status < 200 || response.status >= 300) {
      return {
        ok: false,
        error: `http_${response.status}`,
        hint: `GET ${checked.url.href} returned ${response.status}.`,
      };
    }
    const contentType = response.header("content-type").toLowerCase();
    const rawBody = await response.text();
    if (looksBinary(contentType, rawBody.slice(0, 80))) {
      return {
        ok: false,
        error: "unsupported_type",
        hint: "That URL is not a text page. Open an HTML page instead of a PDF or other file.",
      };
    }
    const body = pageText(rawBody, contentType);
    return { ok: true, url: checked.url.href, chars: body.length, body };
  } catch (error) {
    return networkFail(error, "Public GET timed out (20 s).");
  }
}

export function formatFetchedPages(pages: FetchedPage[] | undefined, max = FETCHED_PAGE_PROMPT_CAP): string {
  const text = (pages ?? [])
    .map((page) => `URL: ${page.url}\n${page.body.trim()}`)
    .filter((block) => block.trim().length > 10)
    .join("\n\n")
    .trim();
  if (!text) return "";
  const clipped = text.length <= max ? text : `${text.slice(0, max)}\n[truncated]`;
  return `Opened pages (copy volumes, wells, and counts from these when they apply; do not invent a different series):\n${clipped}`;
}
