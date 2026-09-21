import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  applyForm,
  createSession,
  getSession,
  setSessionLanguage,
  snapshot,
} from "./session.ts";
import { DEVICE_REGISTRY, deviceFor } from "./devices.ts";
import { createSseWriter } from "./sse.ts";
import { runChatTurn } from "./agent.ts";
import { checkCodeService } from "./backend.ts";
import { loadDemoEnv } from "./env.ts";

const HOST = "127.0.0.1";
const PORT = Number(process.env.WEBDEMO_PORT || 8787);

function json(res: ServerResponse, code: number, body: unknown): void {
  res.writeHead(code, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(body));
}

async function readBody(req: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(Buffer.from(chunk));
  return Buffer.concat(chunks).toString("utf8");
}

/** Empty body → {}. Garbage JSON → null (never throws). */
function parseJsonObject(raw: string): Record<string, unknown> | null {
  if (!raw.trim()) return {};
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
    return parsed as Record<string, unknown>;
  } catch {
    return null;
  }
}

function notFound(res: ServerResponse): void {
  json(res, 404, { error: "not_found" });
}

export async function handleRequest(
  req: IncomingMessage,
  res: ServerResponse
): Promise<void> {
  const url = new URL(req.url || "/", `http://${HOST}:${PORT}`);
  const path = url.pathname;

  if (req.method === "GET" && (path === "/" || path === "/index.html")) {
    res.writeHead(302, { Location: "http://127.0.0.1:5173/" });
    res.end();
    return;
  }

  if (req.method === "GET" && path === "/api/health") {
    const env = loadDemoEnv();
    json(res, 200, {
      ok: true,
      bind: `${HOST}:${PORT}`,
      backend: env.backend,
      model: env.model,
      hasKey: Boolean(env.apiKey),
      code_service: await checkCodeService(),
    });
    return;
  }

  if (req.method === "GET" && path === "/api/devices") {
    json(
      res,
      200,
      DEVICE_REGISTRY.map((device) => ({
        id: device.id,
        label: device.label,
        capabilities: {
          codegen: device.codegen,
          planBackend: device.planBackend,
          checks: [...device.checks],
          animation: device.animation,
          artifactExt: device.artifactExt,
        },
      }))
    );
    return;
  }

  if (req.method === "POST" && path === "/api/session") {
    const body = parseJsonObject(await readBody(req));
    if (!body) {
      json(res, 400, { error: "invalid_json" });
      return;
    }
    const goal = String(body.goal ?? "").trim();
    if (!goal) {
      json(res, 400, { error: "goal is required" });
      return;
    }
    if (
      body.robot != null &&
      String(body.robot).trim() !== "" &&
      !deviceFor(String(body.robot).trim())
    ) {
      json(res, 400, { error: "invalid robot" });
      return;
    }
    const session = createSession();
    applyForm(session, {
      goal,
      doc: body.doc as string | undefined,
      robot: body.robot as string | undefined,
      language: body.language as string | undefined,
    });
    session.codeService = await checkCodeService();
    json(res, 200, snapshot(session));
    return;
  }

  const langMatch = path.match(/^\/api\/session\/([^/]+)\/language$/);
  if (req.method === "POST" && langMatch) {
    const session = getSession(langMatch[1]);
    if (!session) {
      json(res, 404, { error: "unknown_session" });
      return;
    }
    const body = parseJsonObject(await readBody(req)) ?? {};
    setSessionLanguage(session, body.language);
    json(res, 200, snapshot(session));
    return;
  }

  const sessionMatch = path.match(/^\/api\/session\/([^/]+)$/);
  if (req.method === "GET" && sessionMatch) {
    const session = getSession(sessionMatch[1]);
    if (!session) {
      json(res, 404, { error: "unknown_session" });
      return;
    }
    json(res, 200, snapshot(session));
    return;
  }

  if (
    (req.method === "POST" &&
      (path === "/api/plr/visualizer/start" || path === "/api/plr/visualizer/stop")) ||
    (req.method === "GET" && path === "/api/plr/visualizer/status")
  ) {
    const env = loadDemoEnv();
    const target = `${env.backend}${path}`;
    try {
      const body = req.method === "POST" ? await readBody(req) : undefined;
      const response = await fetch(target, {
        method: req.method,
        headers: req.method === "POST" ? { "Content-Type": "application/json" } : undefined,
        body,
        signal: AbortSignal.timeout(path.endsWith("/start") ? 60_000 : 8_000),
      });
      const text = await response.text();
      res.writeHead(response.status, { "Content-Type": "application/json; charset=utf-8" });
      res.end(text);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const down = /fetch failed|ECONNREFUSED|ECONNRESET|aborted|TimeoutError|UND_ERR/i.test(message);
      json(res, 502, {
        ok: false,
        error: down ? "Preview service down." : message,
      });
    }
    return;
  }

  if (req.method === "POST" && path === "/api/chat/stream") {
    const body = parseJsonObject(await readBody(req));
    if (!body) {
      json(res, 400, { error: "invalid_json" });
      return;
    }
    const sessionId = typeof body.sessionId === "string" ? body.sessionId : "";
    const message = typeof body.message === "string" ? body.message : "";
    const session = sessionId ? getSession(sessionId) : undefined;
    if (!session) {
      json(res, 404, { error: "unknown_session" });
      return;
    }
    const sse = createSseWriter(res);
    try {
      const ok = await runChatTurn(session, message, sse);
      sse.write("done", { ok });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      sse.write("error", { message });
      sse.write("done", { ok: false });
    } finally {
      sse.close();
    }
    return;
  }

  notFound(res);
}

export function createWebdemoServer() {
  return createServer((req, res) => {
    void handleRequest(req, res).catch((error) => {
      if (!res.headersSent) json(res, 500, { error: "internal_error" });
      else if (!res.writableEnded) res.end();
      console.error(error instanceof Error ? error.message : String(error));
    });
  });
}

const isMain =
  Boolean(process.argv[1]) &&
  path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url));

if (isMain) {
  const server = createWebdemoServer();
  server.on("error", (error: NodeJS.ErrnoException) => {
    if (error.code === "EADDRINUSE" || error.code === "EADDRNOTAVAIL") {
      console.error(`Cannot bind ${HOST}:${PORT}. Do not start.`);
      process.exit(1);
    }
    throw error;
  });

  try {
    loadDemoEnv();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }

  server.listen(PORT, HOST, () => {
    console.log(`webdemo server http://${HOST}:${PORT}`);
  });
}
