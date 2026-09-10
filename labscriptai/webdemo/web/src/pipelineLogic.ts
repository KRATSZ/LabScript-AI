import type { ChecksResult, SessionSnapshot } from "./types";

export type StepState = "wait" | "run" | "ok" | "fail";

export const PIPELINE_STEPS = ["Robot", "SOP", "Script", "Checks", "Review"] as const;

export const PIPELINE_HINTS: Record<string, string> = {
  ask_user: "Recording hardware…",
  generate_sop: "Writing SOP…",
  generate_code: "Writing script…",
  run_checks: "Checking…",
  open_animation: "Opening animation…",
};

export function preview(text: string, lines = 20): string {
  return text.split("\n").slice(0, lines).join("\n");
}

function hwState(phase: string, running: string | null): StepState {
  if (phase === "ready") return "ok";
  if (phase === "need_robot" || phase === "need_hw_slots") {
    return running === "ask_user" ? "run" : "wait";
  }
  return "wait";
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
  if (
    checks.sim.ok &&
    checks.logicpass.outcome === "pass" &&
    checks.logicpass.logic_pass === true &&
    checks.logicpass.final_pass_v2 === true
  ) {
    return "ok";
  }
  return "fail";
}

function reviewState(checks: ChecksResult | null, running: string | null): StepState {
  if (running === "run_checks") return "run";
  const review = checks?.llmreview;
  if (!review) return "wait";
  if (review.match === true) return "ok";
  if (review.match === false) return "fail";
  return "wait";
}

export function pipelineStates(
  session: SessionSnapshot,
  runningTool: string | null
): StepState[] {
  return [
    hwState(session.phase, runningTool),
    sopState(session.sop, runningTool),
    codeState(session.code, session.plan, session.robot, runningTool),
    checkState(session.checks, runningTool),
    reviewState(session.checks, runningTool),
  ];
}
