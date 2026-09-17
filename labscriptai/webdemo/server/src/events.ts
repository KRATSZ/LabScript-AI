import type { SseWriter } from "./sse.ts";

export type AgentEventKind =
  | "turn/start"
  | "turn/end"
  | "step/start"
  | "step/end"
  | "tool/call"
  | "tool/result";

export interface AgentEvent {
  seq: number;
  t: number;
  kind: AgentEventKind;
  name?: string;
  detail?: Record<string, unknown>;
}

export const TOOL_STEP: Record<string, string> = {
  ask_user: "ask",
  generate_sop: "sop",
  generate_code: "code",
  emit_plan: "plan",
  run_checks: "checks",
  open_animation: "watch",
};

export interface EventSink {
  events?: AgentEvent[];
}

export function appendEvent(
  sink: EventSink,
  partial: Omit<AgentEvent, "seq" | "t"> & { t?: number }
): AgentEvent {
  if (!sink.events) sink.events = [];
  const event: AgentEvent = {
    seq: sink.events.length + 1,
    t: partial.t ?? Date.now(),
    kind: partial.kind,
    ...(partial.name ? { name: partial.name } : {}),
    ...(partial.detail ? { detail: partial.detail } : {}),
  };
  sink.events.push(event);
  return event;
}

export function emitAgentEvent(
  sink: EventSink,
  sse: SseWriter,
  partial: Omit<AgentEvent, "seq" | "t"> & { t?: number }
): AgentEvent {
  const event = appendEvent(sink, partial);
  sse.write("agent_event", event);
  return event;
}
