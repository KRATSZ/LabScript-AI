import { compactChecks } from "./gate.ts";
import { SYSTEM_PROMPT } from "./prompt.ts";
import { snapshot, type SessionState } from "./session.ts";

export const CONTINUE_STEER =
  "Continue from LIVE SESSION. Ask missing hardware or run the next allowed tool.";

export function nextToolHint(session: SessionState): string {
  const snap = snapshot(session);
  if (snap.phase !== "ready") return "ask_user";
  if (!snap.sop.trim()) return "generate_sop";
  if (!snap.code.trim()) return "generate_code";
  if (!session.lastChecks) return "run_checks";
  const next = compactChecks(session.lastChecks, session.patchesUsed ?? 0).next;
  if (next === "patch") return "generate_code";
  const commands = Array.isArray(session.analyze?.commands) ? session.analyze.commands.length : 0;
  if (session.lastChecks.fab.lit && commands > 0) return "open_animation";
  return "done";
}

export function liveSessionBlock(session: SessionState): string {
  const snap = snapshot(session);
  const checks = snap.checks;
  const last = checks
    ? `{sim.ok=${checks.sim.ok}, logicpass.outcome=${checks.logicpass.outcome}, review.match=${
        typeof checks.llmreview?.match === "boolean" ? checks.llmreview.match : "none"
      }, fab.lit=${checks.fab.lit}, next=${compactChecks(checks, session.patchesUsed ?? 0).next}}`
    : "none";
  const doc = !snap.doc || snap.doc === "none" ? "none" : "draft";
  return [
    "LIVE SESSION",
    `phase: ${snap.phase}`,
    `missing: ${snap.missing.join(", ") || "none"}`,
    `doc: ${doc}`,
    `sop_chars: ${snap.sop.length}`,
    `deck_assumed: ${Boolean(snap.deck_assumed)}`,
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
  return [
    `Goal: ${session.goal ?? ""}`,
    `Doc: ${session.doc === "none" || !session.doc ? "none (agent should write SOP later)" : "SOP draft provided"}`,
    `Robot: ${session.robot ?? "unset"}`,
    session.doc && session.doc !== "none" ? `\nSOP draft:\n${session.doc}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}
