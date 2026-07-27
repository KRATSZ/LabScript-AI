import { appendRuntimeOutboxEvent } from "../runtime-outbox.js";

export function tickOutboxKind(status, goalStatus) {
  const normalizedStatus = String(status || "running").toLowerCase();
  if (normalizedStatus === "completed") {
    return "completed";
  }
  if (normalizedStatus === "hard_stop") {
    return "hard_stop";
  }
  if (normalizedStatus === "needs_user") {
    return "needs_user";
  }
  if (normalizedStatus === "unreachable") {
    return "blocked";
  }
  if (goalStatus === "blocked") {
    return "blocked";
  }
  return "heartbeat";
}

export function shouldWakeOnTick(status, goalStatus, zeroLlmWhenNoError) {
  if (!zeroLlmWhenNoError) {
    return true;
  }
  return tickOutboxKind(status, goalStatus) !== "heartbeat";
}

export function appendWatchLoopOutboxEntry(event = {}, { outboxDir = null, dedupe = true } = {}) {
  return appendRuntimeOutboxEvent(event, { outboxDir, dedupe });
}
