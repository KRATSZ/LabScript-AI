import { afterEach, describe, it, mock } from "node:test";
import assert from "node:assert/strict";
import { createSession, streamChat, type StreamHandlers } from "../web/src/api.ts";
import { REQUEST_ERRORS, responseError, streamErrorMessage } from "../web/src/requestErrors.ts";

afterEach(() => mock.restoreAll());
const input = { goal: "Transfer 50 µL A1 to B1", doc: "", robot: "Flex" as const };
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json" } });
function handlers() {
  return {
    onThinking: mock.fn(), onText: mock.fn(), onTool: mock.fn(), onSnapshot: mock.fn(),
    onChecks: mock.fn(), onError: mock.fn(), onDone: mock.fn(),
  } satisfies StreamHandlers;
}

describe("Recoverable web request failures", () => {
  it("replaces an HTML proxy failure instead of exposing it in the create form", async () => {
    mock.method(globalThis, "fetch", async () => new Response("<html>upstream stack and internal host</html>", { status: 503 }));
    await assert.rejects(createSession(input), { message: REQUEST_ERRORS.unavailable });
  });

  it("identifies a stale saved session and a rate limit", async () => {
    assert.equal((await responseError(json({ error: "unknown_session" }, 404))).message, REQUEST_ERRORS.expired);
    assert.equal((await responseError(json({ error: "busy" }, 429))).message, REQUEST_ERRORS.limited);
  });

  it("maps unreachable servers and input errors without losing successful responses", async () => {
    mock.method(globalThis, "fetch", async () => { throw new TypeError("Failed to fetch"); });
    await assert.rejects(createSession(input), { message: REQUEST_ERRORS.network });
    assert.equal((await responseError(json({ error: "invalid robot" }, 400))).message, REQUEST_ERRORS.input);
    mock.restoreAll();
    mock.method(globalThis, "fetch", async () => json({ id: "new-session", ...input }));
    assert.equal((await createSession(input)).id, "new-session");
  });

  it("keeps actionable experiment errors, but replaces service credentials and stack traces", () => {
    assert.equal(streamErrorMessage("Well B1 exceeds its 200 µL capacity."), "Well B1 exceeds its 200 µL capacity.");
    assert.equal(streamErrorMessage("Missing DEEPSEEK_API_KEY"), REQUEST_ERRORS.unavailable);
    assert.equal(streamErrorMessage("Traceback: internal/path.py"), REQUEST_ERRORS.unavailable);
  });

  it("keeps streamed text and only reports completion once", async () => {
    mock.method(globalThis, "fetch", async () => new Response('event: text\ndata: {"token":"Review the plan"}\n\nevent: done\ndata: {}\n\n'));
    const h = handlers();
    await streamChat("session", "", h);
    assert.deepEqual(h.onText.mock.calls[0].arguments, ["Review the plan"]);
    assert.equal(h.onDone.mock.callCount(), 1);
  });

  it("reports a disconnected stream instead of silently treating it as complete", async () => {
    mock.method(globalThis, "fetch", async () => new Response('event: text\ndata: {"token":"Part of a plan"}\n\n'));
    const h = handlers();
    await assert.rejects(streamChat("session", "", h), { message: REQUEST_ERRORS.network });
    assert.equal(h.onDone.mock.callCount(), 0);
  });
});
