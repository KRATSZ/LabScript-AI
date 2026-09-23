import { isPlanCodegen } from "./devices";
import type { CheckStatus, ChecksResult, RobotModel, SessionSnapshot } from "./types";

export type AuditTone = "pass" | "fail" | "uneval" | "skip";

export interface AuditRow {
  key: string;
  label: string;
  result: string;
  tone: AuditTone;
}

export interface ChecksAuditModel {
  checks: AuditRow[];
  assumptions: string[];
  unverified: string[];
}

function outcomeTone(outcome: string | undefined): AuditTone {
  const raw = String(outcome || "").toLowerCase();
  if (raw === "pass" || raw === "true" || raw === "ok") return "pass";
  if (raw === "unevaluable" || raw === "unavailable") return "uneval";
  if (!raw) return "skip";
  return "fail";
}

function statusResult(status: CheckStatus | AuditTone, detail?: string): string {
  if (status === "pass") return detail ? `Passed — ${detail}` : "Passed";
  if (status === "fail") return detail ? `Failed — ${detail}` : "Failed";
  if (status === "uneval" || status === "unevaluable") return detail ? `Cannot verify — ${detail}` : "Cannot verify";
  return detail || "Did not run";
}

function stateOutcome(statepass: ChecksResult["statepass"]): AuditTone {
  if (!statepass || typeof statepass !== "object") return "skip";
  const issues = Array.isArray(statepass.issues) ? statepass.issues : [];
  if (issues.length) return "fail";
  if (statepass.reason) return outcomeTone(String(statepass.reason));
  if (Object.keys(statepass).length === 0) return "skip";
  return "pass";
}

export function checksAudit(
  checks: ChecksResult | null | undefined,
  session?: Pick<SessionSnapshot, "robot" | "goal" | "hardware" | "deck_assumed" | "checks"> | null
): ChecksAuditModel | null {
  if (!checks) return null;
  const robot = session?.robot as RobotModel | null | undefined;
  const simOk = checks.sim?.ok === true;
  const logic = String(checks.logicpass?.outcome || "");
  const state = stateOutcome(checks.statepass);
  const compile = checks.compile;
  const review = checks.llmreview;
  const rows: AuditRow[] = [
    {
      key: "sim",
      label: "Simulation",
      result: statusResult(simOk ? "pass" : "fail", checks.sim?.reason),
      tone: simOk ? "pass" : "fail",
    },
    {
      key: "logic",
      label: "Logic",
      result: statusResult(outcomeTone(logic), checks.logicpass?.reason),
      tone: outcomeTone(logic) === "skip" ? "uneval" : outcomeTone(logic),
    },
    {
      key: "state",
      label: "State",
      result: statusResult(state, typeof checks.statepass?.reason === "string" ? checks.statepass.reason : undefined),
      tone: state === "skip" ? "uneval" : state,
    },
  ];
  if (compile) {
    rows.push({
      key: "compile",
      label: "Compile",
      result: statusResult(compile.ok ? "pass" : "fail", compile.error || compile.hint),
      tone: compile.ok ? "pass" : "fail",
    });
  }
  if (review) {
    const tone: AuditTone =
      review.match === true ? "pass" : review.match === false ? "fail" : "uneval";
    rows.push({
      key: "review",
      label: "Review",
      result: statusResult(tone, review.reason),
      tone,
    });
  }

  const assumptions: string[] = [];
  const goal = (session?.goal || "").replace(/\s+/g, " ").trim();
  const vol = goal.match(/(\d+(?:\.\d+)?)\s*(?:µL|uL|ul)\b/i);
  const wells = goal.match(/from\s+(?:well\s+)?([A-H]\d+)\s+to\s+(?:well\s+)?([A-H]\d+)/i);
  if (session?.hardware?.deck && Object.keys(session.hardware.deck).length) {
    assumptions.push(session.deck_assumed ? "Standard deck (assumed, then confirmed in chat)" : "Deck as last confirmed");
  }
  if (vol && wells) assumptions.push(`Source ${wells[1]} holds at least ${vol[1]} µL; destination ${wells[2]} well state as confirmed`);
  else if (vol) assumptions.push(`Transfer volume ${vol[1]} µL as stated`);
  if (!assumptions.length) assumptions.push("Volumes, wells, and deck as confirmed in chat");

  const unverified = [
    "This is not a live-hardware safety clearance.",
  ];
  if (isPlanCodegen(robot)) {
    unverified.push("Hamilton STAR, Hamilton Vantage, and Tecan Fluent are authoring-only — nothing runs on the instrument from here.");
  } else {
    unverified.push("On-screen Watch is not a run on the robot.");
  }

  return { checks: rows, assumptions, unverified };
}
