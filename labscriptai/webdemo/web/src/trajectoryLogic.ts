import type { AgentEvent } from "./types";

export function eventDetailText(event: AgentEvent): string {
  const detail = event.detail;
  if (!detail) return "";
  const bits: string[] = [];
  if (typeof detail.duration_ms === "number") bits.push(`${detail.duration_ms} ms`);
  if (detail.ok === true) bits.push("ok");
  if (detail.ok === false) bits.push("not ok");
  return bits.join(" · ");
}

export function eventClock(t: number): string {
  if (!Number.isFinite(t) || t <= 0) return "";
  const date = new Date(t);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
