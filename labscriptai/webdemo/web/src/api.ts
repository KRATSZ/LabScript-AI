import type { SessionSnapshot, StartInput } from "./types";
import { request, REQUEST_ERRORS, streamErrorMessage } from "./requestErrors";

export interface StreamHandlers {
  onThinking: (token: string, source: string) => void;
  onText: (token: string) => void;
  onTool: (name: string, status: string) => void;
  onEvent?: (event: import("./types").AgentEvent) => void;
  onSnapshot: (snap: SessionSnapshot) => void;
  onChecks: (checks: SessionSnapshot["checks"]) => void;
  onAnimation?: (allowed: boolean) => void;
  onError: (message: string) => void;
  onDone: () => void;
}

function consumeFrames(buffer: string, onEvent: (event: string, data: unknown) => void): string {
  const frames = buffer.split("\n\n");
  const rest = frames.pop() ?? "";
  for (const frame of frames) {
    let event = "message";
    let data = "";
    for (const line of frame.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      if (line.startsWith("data:")) data += line.slice(5).trim();
    }
    if (!data) continue;
    try {
      onEvent(event, JSON.parse(data));
    } catch {
      onEvent(event, data);
    }
  }
  return rest;
}

export interface DemoHealth {
  ok: boolean;
  model: string;
  hasKey: boolean;
  code_service: "up" | "down";
  backend: string;
}

export async function fetchHealth(): Promise<DemoHealth> {
  const response = await request("/api/health");
  return response.json() as Promise<DemoHealth>;
}

export async function createSession(input: StartInput): Promise<SessionSnapshot> {
  const response = await request("/api/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return response.json();
}

export async function streamChat(
  sessionId: string,
  message: string,
  handlers: StreamHandlers
): Promise<void> {
  const response = await request("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ sessionId, message }),
  });
  if (!response.body) {
    throw new Error(REQUEST_ERRORS.unavailable);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed = false;
  let reportedError = false;
  const onEvent = (event: string, data: unknown) => {
    const rec = data && typeof data === "object" ? (data as Record<string, unknown>) : {};
    if (event === "thinking") {
      handlers.onThinking(String(rec.token || ""), String(rec.source || "agent"));
    } else if (event === "text") {
      handlers.onText(String(rec.token || ""));
    } else if (event === "tool") {
      handlers.onTool(String(rec.name || ""), String(rec.status || ""));
    } else if (event === "agent_event") {
      handlers.onEvent?.(data as import("./types").AgentEvent);
    } else if (event === "snapshot") {
      handlers.onSnapshot(data as SessionSnapshot);
    } else if (event === "checks") {
      handlers.onChecks(data as SessionSnapshot["checks"]);
    } else if (event === "animation") {
      handlers.onAnimation?.(rec.allowed === true);
    } else if (event === "error") {
      reportedError = true;
      handlers.onError(streamErrorMessage(String(rec.message || "")));
    } else if (event === "done") {
      if (!completed) handlers.onDone();
      completed = true;
    }
  };
  try {
    while (true) {
      const { done, value } = await reader.read().catch(() => { throw new Error(REQUEST_ERRORS.network); });
      if (done) {
        consumeFrames(buffer + decoder.decode() + "\n\n", onEvent);
        if (!completed && !reportedError) throw new Error(REQUEST_ERRORS.network);
        break;
      }
      buffer = consumeFrames(buffer + decoder.decode(value, { stream: true }), onEvent);
    }
  } finally {
    reader.releaseLock();
  }
}
