import { isPlayableAnalyze } from "./analysis";
import { isPlanCodegen, robotSupportsWatch } from "./devices";
import type { CheckStatus, ChecksResult, RobotModel, SessionSnapshot } from "./types";

export type StepState = "wait" | "run" | "ok" | "fail" | "uneval";
export type StatusTone = "pass" | "fail" | "uneval";

export const PIPELINE_HINTS: Record<string, string> = {
  ask_user: "Checking a couple of details…",
  generate_sop: "Writing the protocol…",
  generate_code: "Writing the script…",
  emit_plan: "Laying out the steps…",
  run_checks: "Checking bench constraints…",
  open_animation: "Putting the deck on Stage…",
};

const PYTHON_STEPS = ["Run", "Protocol", "Script", "Checks", "Deck"] as const;
const PLAN_STEPS = ["Run", "Protocol", "Steps", "Checks", "Files"] as const;

export function pipelineSteps(robot: RobotModel | null | undefined): readonly string[] {
  return isPlanCodegen(robot) ? PLAN_STEPS : PYTHON_STEPS;
}

export function preview(text: string, lines = 20): string {
  return text.split("\n").slice(0, lines).join("\n");
}

export function statusWord(status: CheckStatus): string {
  if (status === "pass") return "Passed";
  if (status === "unevaluable") return "Cannot verify";
  return "Failed";
}

export function statusTone(status: CheckStatus | null | undefined): StatusTone | null {
  if (status === "pass") return "pass";
  if (status === "fail") return "fail";
  if (status === "unevaluable") return "uneval";
  return null;
}

export function headerTone(
  status: CheckStatus | null | undefined,
  canWatch: boolean
): StatusTone | null {
  if (canWatch) return "pass";
  return statusTone(status);
}

/** First check consequence when unevaluable; otherwise empty. Never invents a reason. */
export function unevalDetail(checks: ChecksResult | null | undefined): string {
  if (!checks || checks.status !== "unevaluable") return "";
  const line = checks.consequences?.find((item) => typeof item === "string" && item.trim());
  return typeof line === "string" ? line.trim() : "";
}

export function phaseLabel(
  phase: string,
  status: CheckStatus | null | undefined,
  canWatch: boolean,
  planBackend = false,
  checks?: ChecksResult | null,
  intakeDone?: boolean,
  hasSop?: boolean,
  deckPreview = false,
  busy = false
): string {
  if ((canWatch || deckPreview) && !busy) return "Ready to watch";
  if (canWatch || deckPreview) return "In progress";
  if (status === "pass") return "Checks passed";
  if (status === "fail") return "Checks failed";
  if (status === "unevaluable") return unevalDetail(checks) || "Cannot verify";
  if (phase === "need_hw_slots") return "Missing deck details";
  if (phase === "ready") {
    if (!hasSop && intakeDone === false) return "Quick check";
    return "In progress";
  }
  return "Which robot — OT-2, Flex, Hamilton STAR, Hamilton Vantage, or Tecan Fluent?";
}

function goalState(goal: string): StepState {
  return goal.trim() ? "ok" : "wait";
}

function sopState(sop: string, running: string | null): StepState {
  if (running === "generate_sop") return "run";
  if (sop.trim()) return "ok";
  return "wait";
}

function codeState(
  code: string,
  plan: Record<string, unknown> | null,
  robot: string | null,
  running: string | null
): StepState {
  if (running === "generate_code" || running === "emit_plan") return "run";
  if (robot === "OT-2" || robot === "Flex") {
    return code.trim() ? "ok" : "wait";
  }
  if (plan && Array.isArray(plan.steps) && plan.steps.length) return "ok";
  if (code.trim()) return "ok";
  return "wait";
}

function checkState(checks: ChecksResult | null, running: string | null): StepState {
  if (running === "run_checks") return "run";
  if (!checks) return "wait";
  if (checks.status === "pass") return "ok";
  if (checks.status === "unevaluable") return "uneval";
  return "fail";
}

function finishState(session: SessionSnapshot, running: string | null): StepState {
  if (running === "open_animation") return "run";
  if (robotSupportsWatch(session.robot)) {
    if (session.checks?.status === "pass" && isPlayableAnalyze(session.analyze)) return "ok";
    return "wait";
  }
  if (!session.checks) return "wait";
  const hasExport = Boolean(session.sop?.trim() || session.plan);
  if (!hasExport) return "wait";
  if (session.checks.status === "unevaluable") return "uneval";
  return "ok";
}

export function pipelineStates(session: SessionSnapshot, runningTool: string | null): StepState[] {
  return [
    goalState(session.goal),
    sopState(session.sop, runningTool),
    codeState(session.code, session.plan, session.robot, runningTool),
    checkState(session.checks, runningTool),
    finishState(session, runningTool),
  ];
}
