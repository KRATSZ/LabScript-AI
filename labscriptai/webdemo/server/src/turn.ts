import { assumedCapacityLine } from "./devices.ts";
import { animationAllowed, compactChecks } from "./gate.ts";
import { SYSTEM_PROMPT } from "./prompt.ts";
import {
  confirmGateOpen,
  deviceFor,
  intakeOpen,
  isOpentrons,
  sessionFillLine,
  sessionFillShortfall,
  snapshot,
  unresolvedGoalNotesConflict,
  type SessionState,
} from "./session.ts";

export const CONTINUE_STEER =
  "Continue from LIVE SESSION. If next_tool is ask_user, one short confirm naming the deck (Hamilton: tip carrier / plate carrier / trough, never slots 1/2/3) — never “nothing is written yet.” Then stop. Otherwise run next_tool. User-facing chat: volumes, wells, sample counts — never which robot, never tool names.";

export function continueSteer(session: SessionState): string {
  if (session.language === "zh") {
    return `用户可见回复必须用简体中文。${CONTINUE_STEER}`;
  }
  return CONTINUE_STEER;
}

export function userFacingLangLine(session: SessionState): string {
  return session.language === "zh"
    ? "User-facing reply MUST be Simplified Chinese (简体中文)."
    : "";
}

export function nextToolHint(session: SessionState): string {
  const snap = snapshot(session);
  if (snap.phase !== "ready") return "ask_user";
  if (unresolvedGoalNotesConflict(session)) return "ask_user";
  if (intakeOpen(session)) return "ask_user";
  if (confirmGateOpen(session)) return "ask_user";
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
  const conflict = unresolvedGoalNotesConflict(session);
  const capacity =
    snap.deck_assumed ? assumedCapacityLine(session.robot, session.hardware.deck) : "";
  return [
    "LIVE SESSION",
    `phase: ${snap.phase}`,
    `missing: ${snap.missing.join(", ") || "none"}`,
    `doc: ${doc}`,
    ...(conflict ? [`notes_conflict: ${conflict}`] : []),
    `intake: ${session.intakeDone ? "done" : "pending"}`,
    `sop_chars: ${snap.sop.length}`,
    `plan_steps: ${Array.isArray(snap.plan?.steps) ? snap.plan.steps.length : 0}`,
    `deck_assumed: ${Boolean(snap.deck_assumed)}`,
    `deck_confirmed: ${Boolean(snap.deck_confirmed)}`,
    `language: ${session.language === "zh" ? "zh (reply in Chinese)" : "en (reply in English)"}`,
    ...(session.removedLabware?.length
      ? [`removed_labware: ${session.removedLabware.join(", ")} (do not put it back)`]
      : []),
    ...(session.sourceFill
      ? [`confirmed_source_fill: ${session.sourceFill.well}=${session.sourceFill.ul} µL on hand, not tip capacity`]
      : []),
    ...(sessionFillShortfall(session) ? [`fill_shortfall: ${sessionFillShortfall(session)}`] : []),
    ...(sessionFillLine(session) ? [`checked_fill: ${sessionFillLine(session)}`] : []),
    ...(session.regenSop ? ["regen_sop: true"] : []),
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
  if (text.trim()) {
    const langLine = userFacingLangLine(session);
    return langLine ? `${langLine}\n${text}` : text;
  }
  const history = Array.isArray(session.messages) ? session.messages.length : 0;
  if (history > 0) return continueSteer(session);
  const capacity = session.deckAssumed
    ? assumedCapacityLine(session.robot, session.hardware.deck)
    : "";
  return [
    userFacingLangLine(session),
    `Goal: ${session.goal ?? ""}`,
    `Doc: ${session.doc === "none" || !session.doc ? "none (agent should write SOP later)" : "SOP draft provided"}`,
    `Robot: ${deviceFor(session.robot)?.label ?? session.robot ?? "unset"}`,
    capacity ? `Assumed deck: ${capacity}` : "",
    session.doc && session.doc !== "none" ? `\nSOP draft:\n${session.doc}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}
