import { Agent } from "@earendil-works/pi-agent-core";
import type { AssistantMessageEvent, Model } from "@earendil-works/pi-ai";
import { streamSimple } from "@earendil-works/pi-ai/compat";
import { loadDemoEnv } from "./env.ts";
import { isPatchBudgetRefusal } from "./gate.ts";
import { snapshot, type SessionState } from "./session.ts";
import type { SseWriter } from "./sse.ts";
import { buildTools } from "./tools.ts";
import { composeSystemPrompt, nextUserMessage } from "./turn.ts";

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
    maxTokens: 8192,
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

export async function runChatTurn(
  session: SessionState,
  userText: string,
  sse: SseWriter
): Promise<void> {
  const env = loadDemoEnv();
  if (!env.apiKey) {
    sse.write("error", { message: "Missing LABSCRIPTAI_DEEPSEEK_API_KEY (env or cloud .env)." });
    return;
  }

  session.patchesUsed = 0;
  const tools = buildTools(session, sse);
  const prior = Array.isArray(session.messages) ? session.messages : [];
  const agent = new Agent({
    initialState: {
      systemPrompt: composeSystemPrompt(session),
      model: deepseekModel(),
      thinkingLevel: "medium",
      tools,
      messages: prior as never[],
    },
    streamFn: streamSimple,
    getApiKey: async () => env.apiKey,
    toolExecution: "sequential",
    sessionId: session.id,
    afterToolCall: async ({ result }) =>
      isPatchBudgetRefusal(result.details) ? { isError: true, terminate: true } : undefined,
    shouldStopAfterTurn: ({ toolResults }) =>
      toolResults.some((r) => isPatchBudgetRefusal(r.details)),
  });

  agent.subscribe((event) => {
    if (event.type === "message_update") {
      const think = thinkingFromEvent(event.assistantMessageEvent);
      if (think) sse.write("thinking", { token: think, source: "agent" });
      const text = textFromEvent(event.assistantMessageEvent);
      if (text) sse.write("text", { token: text });
    }
    if (event.type === "tool_execution_start") {
      sse.write("tool", { name: event.toolName, status: "start" });
    }
    if (event.type === "tool_execution_end") {
      sse.write("tool", { name: event.toolName, status: "done" });
    }
    if (event.type === "agent_end") {
      session.messages = agent.state.messages as unknown[];
      sse.write("snapshot", snapshot(session));
    }
  });

  try {
    await agent.prompt(nextUserMessage(session, userText));
    session.messages = agent.state.messages as unknown[];
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    sse.write("error", { message });
  }
}
