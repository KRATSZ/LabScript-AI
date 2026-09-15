import type { SessionSnapshot, StartInput } from "./types";

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

export async function createSession(input: StartInput): Promise<SessionSnapshot> {
  const response = await fetch("/api/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function streamChat(
  sessionId: string,
  message: string,
  handlers: StreamHandlers
): Promise<void> {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ sessionId, message }),
  });
  if (!response.ok || !response.body) {
    throw new Error(`chat stream failed: ${response.status}`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
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
      handlers.onError(String(rec.message || "error"));
    } else if (event === "done") {
      handlers.onDone();
    }
  };
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      consumeFrames(buffer + "\n\n", onEvent);
      handlers.onDone();
      break;
    }
    buffer = consumeFrames(buffer + decoder.decode(value, { stream: true }), onEvent);
  }
}
