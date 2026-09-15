import {
  Agent,
  type AfterToolCallContext,
  type AfterToolCallResult,
  type AgentMessage,
  type AgentTool,
} from "@earendil-works/pi-agent-core";
import type { AssistantMessage, AssistantMessageEvent, Model } from "@earendil-works/pi-ai";
import { streamSimple } from "@earendil-works/pi-ai/compat";
import { loadDemoEnv } from "./env.ts";
import {
  isPatchBudgetRefusal,
  REVIEWER_UNAVAILABLE_DISCLOSURE,
} from "./gate.ts";
import { emitAgentEvent, TOOL_STEP } from "./events.ts";
import { markConflictUserReply, markIntakeReply, snapshot, type SessionState } from "./session.ts";
import type { SseWriter } from "./sse.ts";
import { buildTools } from "./tools.ts";
import { composeSystemPrompt, nextUserMessage } from "./turn.ts";

/** DeepSeek reasoning and visible output share this pool, so leave ample room for both. */
export const DEEPSEEK_MAX_TOKENS = 32768;
export const MAX_EXHAUSTED_MODEL_TURNS = 3;
export const MODEL_CONTINUE_MESSAGE = "Continue.";

function deepseekModel(): Model<"openai-completions"> {
  const { model, baseUrl } = loadDemoEnv();
  return {
    id: model,
    name: model,
    api: "openai-completions",
    provider: "deepseek",
    baseUrl,
    reasoning: true,
    input: ["text"],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: 128000,
    maxTokens: DEEPSEEK_MAX_TOKENS,
    compat: {
      thinkingFormat: "deepseek",
      supportsDeveloperRole: false,
    },
  };
}

function thinkingFromEvent(event: AssistantMessageEvent | undefined): string {
  if (event?.type === "thinking_delta") return event.delta;
  return "";
}

function textFromEvent(event: AssistantMessageEvent | undefined): string {
  if (event?.type === "text_delta") return event.delta;
  return "";
}

export const POST_EMIT_PLAN_HINT =
  "SYSTEM HINT: emit_plan succeeded. Call run_checks now before any further planning or patching.";
export const POST_RUN_CHECKS_REVIEWER_UNAVAILABLE_HINT =
  `SYSTEM HINT: ${REVIEWER_UNAVAILABLE_DISCLOSURE} Disclose this in the final user-facing message.`;
export const POST_RUN_CHECKS_WITHHELD_HINT =
  "SYSTEM HINT: Checks did not pass, so .gwl / worklist / downloadable script is withheld. Do not tell the user those files are ready. Report the bench consequence and ask whether to adjust.";
export const POST_NOTES_CONFLICT_HINT =
  "SYSTEM HINT: Notes conflict with the goal. Call ask_user, tell the user both volumes, and STOP. Do not generate_sop, emit_plan, run_checks, or say a .gwl is ready until the user answers.";
export const POST_INTAKE_HINT =
  "SYSTEM HINT: Confirm volume, wells, mix, and the standard deck. Ask 1–2 short lab questions in chat, call ask_user, and STOP. Do not generate_sop, emit_plan, generate_code, or a .gwl until they reply. After they confirm the standard deck, do not ask pipette vs tip size. Do not mention liters unless they wrote liters. No tool names in the user-facing message.";

export function isNotesConflictWait(details: unknown): boolean {
  if (!details || typeof details !== "object") return false;
  const payload = (details as { payload?: { wait?: unknown } }).payload;
  return payload?.wait === true;
}

export function isIntakeWait(details: unknown): boolean {
  if (!details || typeof details !== "object") return false;
  const payload = (details as { payload?: { wait?: unknown; intake?: unknown } }).payload;
  return payload?.wait === true && payload?.intake === true;
}

export function isSuccessfulToolResult(result: { details?: unknown }): boolean {
  if (isPatchBudgetRefusal(result.details)) return false;
  const payload = (result.details as { payload?: Record<string, unknown> } | undefined)?.payload;
  if (!payload || typeof payload !== "object") return true;
  if (payload.wait === true) return false;
  if (payload.blocked === true) return false;
  if (payload.ok === false) return false;
  if (payload.allowed === false) return false;
  if (payload.status === "fail") return false;
  if (payload.download === "withheld") return false;
  return true;
}

export function afterWebdemoToolCall(
  context: {
    toolCall: { name: string };
    result: AfterToolCallContext["result"];
  }
): AfterToolCallResult | undefined {
  if (isPatchBudgetRefusal(context.result.details)) {
    return { isError: true, terminate: true };
  }
  const details = context.result.details as {
    payload?: {
      ok?: unknown;
      fab?: { lit?: unknown };
      review?: { status?: unknown };
      status?: unknown;
      download?: unknown;
      wait?: unknown;
      blocked?: unknown;
      conflict?: unknown;
      intake?: unknown;
      missing?: unknown;
    };
  } | undefined;
  if (context.toolCall.name === "emit_plan" && details?.payload?.ok === true) {
    return {
      content: [
        ...context.result.content,
        { type: "text", text: POST_EMIT_PLAN_HINT },
      ],
    };
  }
  if (
    details?.payload?.wait === true ||
    (details?.payload?.blocked === true &&
      (Boolean(details.payload.conflict) ||
        Boolean(details.payload.intake) ||
        (Array.isArray(details.payload.missing) &&
          details.payload.missing.some((item) => String(item).includes("ask_user")))))
  ) {
    const hint = details?.payload?.intake === true ? POST_INTAKE_HINT : POST_NOTES_CONFLICT_HINT;
    return {
      content: [
        ...context.result.content,
        { type: "text", text: hint },
      ],
      ...(details?.payload?.wait === true ? { terminate: true } : {}),
    };
  }
  if (
    context.toolCall.name === "run_checks" &&
    (details?.payload?.download === "withheld" || details?.payload?.status === "fail")
  ) {
    return {
      content: [
        ...context.result.content,
        { type: "text", text: POST_RUN_CHECKS_WITHHELD_HINT },
      ],
    };
  }
  if (
    context.toolCall.name === "run_checks" &&
    details?.payload?.fab?.lit === true &&
    details.payload.review?.status === "unavailable"
  ) {
    return {
      content: [
        ...context.result.content,
        { type: "text", text: POST_RUN_CHECKS_REVIEWER_UNAVAILABLE_HINT },
      ],
    };
  }
  return undefined;
}

export function withToolEvents(
  tools: AgentTool[],
  sse: SseWriter,
  now: () => number = Date.now,
  session?: SessionState
): AgentTool[] {
  const sink = session ?? { events: [] };
  return tools.map((tool) => ({
    ...tool,
    execute: async (...args: Parameters<AgentTool["execute"]>) => {
      const startedAt = now();
      const step = TOOL_STEP[tool.name];
      sse.write("tool", { name: tool.name, status: "start" });
      emitAgentEvent(sink, sse, { kind: "tool/call", name: tool.name, t: startedAt });
      if (step) emitAgentEvent(sink, sse, { kind: "step/start", name: step, t: startedAt });
      const finish = (ok: boolean) => {
        const duration_ms = Math.max(0, now() - startedAt);
        sse.write("tool", {
          name: tool.name,
          status: "done",
          duration_ms,
          ok,
        });
        emitAgentEvent(sink, sse, {
          kind: "tool/result",
          name: tool.name,
          t: now(),
          detail: { duration_ms, ok },
        });
        if (step) {
          emitAgentEvent(sink, sse, {
            kind: "step/end",
            name: step,
            t: now(),
            detail: { duration_ms, ok },
          });
        }
      };
      try {
        const result = await tool.execute(...args);
        finish(isSuccessfulToolResult(result));
        return result;
      } catch (error) {
        finish(false);
        throw error;
      }
    },
  }));
}

type ChatTurnAgent = Pick<Agent, "state" | "subscribe" | "prompt" | "followUp">;

export interface AutoContinueState {
  exhaustedTurns: number;
  error?: string;
}

export function createAutoContinueState(): AutoContinueState {
  return { exhaustedTurns: 0 };
}

export function isExhaustedAssistantTurn(message: unknown): boolean {
  if (!message || typeof message !== "object") return false;
  const turn = message as Partial<AssistantMessage>;
  if (turn.role !== "assistant" || !Array.isArray(turn.content)) return false;
  if (turn.stopReason === "length") return true;
  if (turn.stopReason === "error" || turn.stopReason === "aborted") return false;
  const hasText = turn.content.some(
    (item) => item.type === "text" && item.text.trim().length > 0
  );
  const hasToolCall = turn.content.some((item) => item.type === "toolCall");
  const hasThinking = turn.content.some((item) => item.type === "thinking");
  return hasThinking && !hasText && !hasToolCall;
}

export async function promptWithAutoContinue(
  agent: ChatTurnAgent,
  initialMessage: string,
  session: SessionState,
  sse: SseWriter,
  autoContinue: AutoContinueState = createAutoContinueState(),
  now: () => number = Date.now
): Promise<boolean> {
  agent.subscribe((event) => {
    if (event.type === "message_update") {
      const think = thinkingFromEvent(event.assistantMessageEvent);
      if (think) sse.write("thinking", { token: think, source: "agent" });
      const text = textFromEvent(event.assistantMessageEvent);
      if (text) sse.write("text", { token: text });
    }
    if (
      event.type === "turn_end" &&
      !autoContinue.error &&
      isExhaustedAssistantTurn(event.message)
    ) {
      autoContinue.exhaustedTurns += 1;
      if (autoContinue.exhaustedTurns < MAX_EXHAUSTED_MODEL_TURNS) {
        const continuation: AgentMessage = {
          role: "user",
          content: MODEL_CONTINUE_MESSAGE,
          timestamp: now(),
        };
        agent.followUp(continuation);
      } else {
        autoContinue.error =
          `Model exhausted its budget ${autoContinue.exhaustedTurns} times. Please retry.`;
      }
    }
    if (event.type === "agent_end") {
      session.messages = agent.state.messages as unknown[];
      sse.write("snapshot", snapshot(session));
    }
  });

  try {
    await agent.prompt(initialMessage);
    session.messages = agent.state.messages as unknown[];
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    sse.write("error", { message });
    return false;
  }
  if (autoContinue.error) {
    sse.write("error", { message: autoContinue.error });
    return false;
  }
  if (agent.state.errorMessage) {
    sse.write("error", { message: agent.state.errorMessage });
    return false;
  }
  return true;
}

export async function runChatTurn(
  session: SessionState,
  userText: string,
  sse: SseWriter
): Promise<boolean> {
  const env = loadDemoEnv();
  if (!env.apiKey) {
    sse.write("error", { message: "Missing LABSCRIPTAI_DEEPSEEK_API_KEY (env or cloud .env)." });
    return false;
  }

  session.patchesUsed = 0;
  markConflictUserReply(session, userText);
  markIntakeReply(session, userText);
  emitAgentEvent(session, sse, { kind: "turn/start" });
  const tools = withToolEvents(buildTools(session, sse), sse, Date.now, session);
  const prior = Array.isArray(session.messages) ? session.messages : [];
  const autoContinue = createAutoContinueState();
  const agent = new Agent({
    initialState: {
      systemPrompt: composeSystemPrompt(session),
      model: deepseekModel(),
      thinkingLevel: "low",
      tools,
      messages: prior as never[],
    },
    streamFn: streamSimple,
    getApiKey: async () => env.apiKey,
    toolExecution: "sequential",
    sessionId: session.id,
    afterToolCall: async (context) => afterWebdemoToolCall(context),
    shouldStopAfterTurn: ({ toolResults }) =>
      Boolean(autoContinue.error) ||
      toolResults.some(
        (r) => isPatchBudgetRefusal(r.details) || isNotesConflictWait(r.details)
      ),
  });

  const ok = await promptWithAutoContinue(
    agent,
    nextUserMessage(session, userText),
    session,
    sse,
    autoContinue
  );
  emitAgentEvent(session, sse, { kind: "turn/end", detail: { ok } });
  return ok;
}
