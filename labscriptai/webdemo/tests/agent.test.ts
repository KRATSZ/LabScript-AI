import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { Type } from "typebox";
import type { AgentMessage, AgentTool } from "@earendil-works/pi-agent-core";
import type { AssistantMessage } from "@earendil-works/pi-ai";
import {
  afterWebdemoToolCall,
  DEEPSEEK_MAX_TOKENS,
  MAX_EXHAUSTED_MODEL_TURNS,
  MODEL_CONTINUE_MESSAGE,
  POST_EMIT_PLAN_HINT,
  POST_RUN_CHECKS_REVIEWER_UNAVAILABLE_HINT,
  promptWithAutoContinue,
  withToolEvents,
} from "../server/src/agent.ts";
import {
  reviewerProcessEnv,
  runLlmreviewCli,
  WEBDEMO_REVIEW_MAX_TOKENS,
} from "../server/src/backend.ts";
import { createSession } from "../server/src/session.ts";

const usage = {
  input: 1,
  output: 1,
  cacheRead: 0,
  cacheWrite: 0,
  totalTokens: 2,
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 },
};

function assistant(
  content: AssistantMessage["content"],
  stopReason: AssistantMessage["stopReason"] = "stop"
): AssistantMessage {
  return {
    role: "assistant",
    content,
    api: "openai-completions",
    provider: "deepseek",
    model: "fake",
    usage,
    stopReason,
    timestamp: 1,
  };
}

function fakeAgent(turns: AssistantMessage[]) {
  type PromptAgent = Parameters<typeof promptWithAutoContinue>[0];
  type Listener = Parameters<PromptAgent["subscribe"]>[0];
  const listeners: Listener[] = [];
  const queued: AgentMessage[] = [];
  const injected: AgentMessage[] = [];
  const messages: AgentMessage[] = [];
  const signal = new AbortController().signal;
  const fake = {
    state: { messages, errorMessage: undefined },
    subscribe(listener: Listener) {
      listeners.push(listener);
      return () => {};
    },
    followUp(message: AgentMessage) {
      queued.push(message);
    },
    async prompt() {
      for (let index = 0; index < turns.length; index += 1) {
        const turn = turns[index];
        messages.push(turn);
        for (const listener of listeners) {
          await listener({ type: "turn_end", message: turn, toolResults: [] }, signal);
        }
        const followUp = queued.shift();
        if (!followUp) break;
        injected.push(followUp);
        messages.push(followUp);
      }
      for (const listener of listeners) {
        await listener({ type: "agent_end", messages }, signal);
      }
    },
  } as unknown as PromptAgent;
  return { fake, injected };
}

describe("agent tool-result handling", () => {
  it("adds a run_checks system hint after successful emit_plan", () => {
    const update = afterWebdemoToolCall({
      toolCall: { name: "emit_plan" },
      result: {
        content: [{ type: "text", text: '{"ok":true}' }],
        details: { payload: { ok: true } },
      },
    });

    assert.ok(update?.content);
    assert.equal(update.content.at(-1)?.type, "text");
    assert.equal((update.content.at(-1) as { text: string }).text, POST_EMIT_PLAN_HINT);
    assert.match(JSON.stringify(update.content), /call run_checks now/i);
  });

  it("does not add the hint when emit_plan fails", () => {
    const update = afterWebdemoToolCall({
      toolCall: { name: "emit_plan" },
      result: {
        content: [{ type: "text", text: '{"ok":false}' }],
        details: { payload: { ok: false } },
      },
    });
    assert.equal(update, undefined);
  });

  it("adds the semantic-review disclosure after a pass with reviewer unavailable", () => {
    const update = afterWebdemoToolCall({
      toolCall: { name: "run_checks" },
      result: {
        content: [{ type: "text", text: '{"fab":{"lit":true}}' }],
        details: {
          payload: {
            fab: { lit: true },
            review: { status: "unavailable" },
          },
        },
      },
    });

    assert.ok(update?.content);
    assert.equal(
      (update.content.at(-1) as { text: string }).text,
      POST_RUN_CHECKS_REVIEWER_UNAVAILABLE_HINT
    );
    assert.match(JSON.stringify(update.content), /semantic review is unverified/i);
    assert.match(JSON.stringify(update.content), /not a mismatch/i);
    assert.match(JSON.stringify(update.content), /does not block/i);
  });

  it("emits tool done only after the handler resolves, with duration", async () => {
    const events: string[] = [];
    let release!: () => void;
    const barrier = new Promise<void>((resolve) => {
      release = resolve;
    });
    const fakeTool: AgentTool = {
      name: "slow_tool",
      label: "Slow tool",
      description: "test",
      parameters: Type.Object({}),
      execute: async () => {
        events.push("handler:start");
        await barrier;
        events.push("handler:end");
        return { content: [{ type: "text", text: "ok" }], details: {} };
      },
    };
    const times = [100, 145];
    const wrapped = withToolEvents(
      [fakeTool],
      {
        write(_event, data) {
          const payload = data as { status: string; duration_ms?: number };
          events.push(`sse:${payload.status}${payload.duration_ms == null ? "" : `:${payload.duration_ms}`}`);
        },
        close() {},
      },
      () => times.shift() ?? 145
    )[0];

    const pending = wrapped.execute("1", {});
    assert.deepEqual(events, ["sse:start", "handler:start"]);
    release();
    await pending;
    assert.deepEqual(events, ["sse:start", "handler:start", "handler:end", "sse:done:45"]);
  });
});

describe("agent model budget recovery", () => {
  it("sets the DeepSeek shared reasoning/output budget to at least 32768", () => {
    assert.ok(DEEPSEEK_MAX_TOKENS >= 32768);
  });

  it("injects a short continue user message after a thinking-only turn", async () => {
    const { fake, injected } = fakeAgent([
      assistant([{ type: "thinking", thinking: "still reasoning" }]),
      assistant([{ type: "text", text: "finished" }]),
    ]);
    const events: Array<{ event: string; data: unknown }> = [];
    const ok = await promptWithAutoContinue(
      fake,
      "start",
      createSession(),
      {
        write(event, data) {
          events.push({ event, data });
        },
        close() {},
      },
      undefined,
      () => 123
    );

    assert.equal(ok, true);
    assert.equal(injected.length, 1);
    assert.equal(injected[0]?.role, "user");
    assert.equal((injected[0] as { content?: unknown }).content, MODEL_CONTINUE_MESSAGE);
    assert.equal(events.some(({ event }) => event === "error"), false);
  });

  it("reports an error, never done-ok, after three exhausted turns", async () => {
    const exhausted = Array.from({ length: MAX_EXHAUSTED_MODEL_TURNS }, () =>
      assistant([{ type: "thinking", thinking: "budget spent" }], "length")
    );
    const { fake, injected } = fakeAgent(exhausted);
    const events: Array<{ event: string; data: unknown }> = [];
    const ok = await promptWithAutoContinue(fake, "start", createSession(), {
      write(event, data) {
        events.push({ event, data });
      },
      close() {},
    });

    assert.equal(ok, false);
    assert.equal(injected.length, MAX_EXHAUSTED_MODEL_TURNS - 1);
    const error = events.find(({ event }) => event === "error");
    assert.match(JSON.stringify(error?.data), /exhausted its budget 3 times/i);
    assert.equal(
      events.some(
        ({ event, data }) =>
          event === "done" && (data as { ok?: boolean } | undefined)?.ok === true
      ),
      false
    );
  });
});

describe("llmreview budget", () => {
  it("forces the webdemo reviewer max_tokens to match the 32768 agent budget", () => {
    const env = reviewerProcessEnv({
      LABSCRIPTAI_MAX_TOKENS: "1024",
      DEEPSEEK_REVIEW_MAX_TOKENS: "2048",
    });
    assert.ok(Number(env.LABSCRIPTAI_MAX_TOKENS) >= 32768);
    assert.equal(Number(env.LABSCRIPTAI_MAX_TOKENS), WEBDEMO_REVIEW_MAX_TOKENS);
    assert.equal(WEBDEMO_REVIEW_MAX_TOKENS, DEEPSEEK_MAX_TOKENS);
    assert.equal(env.DEEPSEEK_REVIEW_MAX_TOKENS, env.LABSCRIPTAI_MAX_TOKENS);
  });

  it("sends reviewer max_tokens >= 32768 in the completion request body", async () => {
    let requestBody: Record<string, unknown> | undefined;
    const fakeApi = createServer(async (req, res) => {
      const chunks: Buffer[] = [];
      for await (const chunk of req) chunks.push(Buffer.from(chunk));
      requestBody = JSON.parse(Buffer.concat(chunks).toString("utf8")) as Record<string, unknown>;
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          choices: [
            {
              finish_reason: "stop",
              message: { content: '{"match":true,"findings":[]}' },
            },
          ],
        })
      );
    });
    await new Promise<void>((resolve) => fakeApi.listen(0, "127.0.0.1", resolve));
    const address = fakeApi.address();
    assert.ok(address && typeof address === "object");
    const prior = {
      key: process.env.DEEPSEEK_REVIEW_API_KEY,
      baseUrl: process.env.DEEPSEEK_REVIEW_BASE_URL,
      model: process.env.DEEPSEEK_REVIEW_MODEL,
    };
    process.env.DEEPSEEK_REVIEW_API_KEY = "test-key";
    process.env.DEEPSEEK_REVIEW_BASE_URL = `http://127.0.0.1:${address.port}/v1`;
    process.env.DEEPSEEK_REVIEW_MODEL = "test-reviewer";

    try {
      const review = await runLlmreviewCli("transfer 50 uL", '{"steps":[]}');
      assert.equal(review.match, true);
      assert.ok(Number(requestBody?.max_tokens) >= 32768);
    } finally {
      for (const [key, value] of Object.entries({
        DEEPSEEK_REVIEW_API_KEY: prior.key,
        DEEPSEEK_REVIEW_BASE_URL: prior.baseUrl,
        DEEPSEEK_REVIEW_MODEL: prior.model,
      })) {
        if (value == null) delete process.env[key];
        else process.env[key] = value;
      }
      await new Promise<void>((resolve, reject) =>
        fakeApi.close((error) => (error ? reject(error) : resolve()))
      );
    }
  });
});
