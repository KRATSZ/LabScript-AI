import { afterEach, it } from "node:test";
import assert from "node:assert/strict";
import { getReplayJson, ReplayRequestError } from "../web/src/flex3dRequest.ts";

const originalFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = originalFetch; });

it("reports a live request's AbortError instead of silently abandoning preparation", async () => {
  globalThis.fetch = async () => { throw new DOMException("aborted by transport", "AbortError"); };
  await assert.rejects(getReplayJson("/view", new AbortController().signal), /请求中断或超时/);
});

it("preserves explicit revision cancellation for the caller to ignore", async () => {
  const controller = new AbortController();
  controller.abort();
  let called = false;
  globalThis.fetch = async () => { called = true; return new Response("{}"); };
  await assert.rejects(getReplayJson("/view", controller.signal), { name: "AbortError" });
  assert.equal(called, false);
});

it("reports timeout during response-body reading instead of accepting an empty view", async () => {
  globalThis.fetch = async (_url, init) => new Response(new ReadableStream({
    start(stream) {
      init?.signal?.addEventListener("abort", () => stream.error(new DOMException("body interrupted", "AbortError")), { once: true });
    },
  }));
  // Keep a normal timer alive: AbortSignal.timeout itself does not keep Node alive.
  const keepAlive = setTimeout(() => {}, 1000);
  try {
    await assert.rejects(getReplayJson("/view", new AbortController().signal, 10), /请求中断或超时/);
  } finally { clearTimeout(keepAlive); }
});

it("reports transport interruption during body reading before the deadline", async () => {
  globalThis.fetch = async () => new Response(new ReadableStream({
    start(stream) { stream.error(new DOMException("transport aborted body", "AbortError")); },
  }));
  await assert.rejects(getReplayJson("/view", new AbortController().signal), /请求中断或超时/);
});

it("retains readable server errors and status for bounded startup retries", async () => {
  globalThis.fetch = async () => Response.json({ message: "三维服务暂时不可用" }, { status: 503 });
  await assert.rejects(getReplayJson("/view", new AbortController().signal), (err: unknown) =>
    err instanceof ReplayRequestError && err.status === 503 && err.message === "三维服务暂时不可用");
});
