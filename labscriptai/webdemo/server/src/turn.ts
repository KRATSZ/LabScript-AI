import { assumedCapacityLine } from "./devices.ts";
import { animationAllowed, compactChecks } from "./gate.ts";
import { SYSTEM_PROMPT } from "./prompt.ts";
import { isOpentrons, snapshot, type SessionState } from "./session.ts";

export const CONTINUE_STEER =
  "Continue from LIVE SESSION. Run next_tool. Ask only for volumes, wells, sample counts, or labware the assumed deck does not have. Never ask which robot.";

export function nextToolHint(session: SessionState): string {
  const snap = snapshot(session);
  if (snap.phase !== "ready") return "ask_user";
  if (!snap.sop.trim()) return "generate_sop";
  if (isOpentrons(session) && !snap.code.trim()) {
    if (snap.code_service === "down") return "emit_plan";
    if (
      session.lastChecks &&
      compactChecks(session.lastChecks, session.patchesUsed ?? 0).next === "patch"
    ) {
      return "emit_plan";
    }
    return "generate_code";
  }
  if (!isOpentrons(session) && !snap.plan) return "emit_plan";
  if (!session.lastChecks) return "run_checks";
  const next = compactChecks(session.lastChecks, session.patchesUsed ?? 0).next;
  if (next === "patch") {
    if (isOpentrons(session) && snap.code.trim()) return "generate_code";
    return "emit_plan";
  }
  const commands = Array.isArray(session.analyze?.commands) ? session.analyze.commands.length : 0;
  if (animationAllowed(session.lastChecks, commands)) return "open_animation";
  return "done";
}

export function liveSessionBlock(session: SessionState): string {
  const snap = snapshot(session);
  const checks = snap.checks;
  const compact = checks ? compactChecks(checks, session.patchesUsed ?? 0) : null;
  const reviewLabel = !compact
    ? "none"
    : compact.review.status === "unavailable"
      ? "unavailable"
      : typeof compact.review.match === "boolean"
        ? String(compact.review.match)
        : "none";
  const last = compact
    ? `{sim.ok=${checks!.sim.ok}, logicpass.outcome=${checks!.logicpass.outcome}, review.match=${reviewLabel}, fab.lit=${checks!.fab.lit}, next=${compact.next}}`
    : "none";
  const doc = !snap.doc || snap.doc === "none" ? "none" : "draft";
  const capacity =
    snap.deck_assumed ? assumedCapacityLine(session.robot, session.hardware.deck) : "";
  return [
    "LIVE SESSION",
    `phase: ${snap.phase}`,
    `missing: ${snap.missing.join(", ") || "none"}`,
    `doc: ${doc}`,
    `sop_chars: ${snap.sop.length}`,
    `plan_steps: ${Array.isArray(snap.plan?.steps) ? snap.plan.steps.length : 0}`,
    `deck_assumed: ${Boolean(snap.deck_assumed)}`,
    ...(capacity ? [`assumed_capacity: ${capacity}`] : []),
    `code_service: ${snap.code_service}`,
    `code_chars: ${snap.code.length}`,
    `analyze_commands: ${Array.isArray(snap.analyze?.commands) ? snap.analyze.commands.length : 0}`,
    `next_tool: ${nextToolHint(session)}`,
    `last_checks: ${last}`,
    "hardware_config:",
    snap.hardware_config,
  ].join("\n");
}

export function composeSystemPrompt(session: SessionState): string {
  return `${SYSTEM_PROMPT}\n\n${liveSessionBlock(session)}`;
}

export function nextUserMessage(session: SessionState, text: string): string {
  if (text.trim()) return text;
  const history = Array.isArray(session.messages) ? session.messages.length : 0;
  if (history > 0) return CONTINUE_STEER;
  const capacity = session.deckAssumed
    ? assumedCapacityLine(session.robot, session.hardware.deck)
    : "";
  return [
    `Goal: ${session.goal ?? ""}`,
    `Doc: ${session.doc === "none" || !session.doc ? "none (agent should write SOP later)" : "SOP draft provided"}`,
    `Robot: ${session.robot ?? "unset"}`,
    capacity ? `Assumed deck: ${capacity}` : "",
    session.doc && session.doc !== "none" ? `\nSOP draft:\n${session.doc}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}
