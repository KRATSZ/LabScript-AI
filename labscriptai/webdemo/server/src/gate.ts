import { collectConsequences, formatIssue, formatReason, isUnevaluableCode } from "./consequences.ts";

export type LogicOutcome = "pass" | "fail" | "unevaluable" | string;

export interface SimResult {
  ok: boolean;
  reason?: string;
  errors?: string[];
}

export interface LogicPassResult {
  outcome: LogicOutcome;
  logic_pass: boolean;
  final_pass_v2?: boolean;
  issues?: unknown[];
  coverage?: unknown;
  reason?: string;
}

export interface StatePassResult {
  issues?: unknown[];
  coverage?: unknown;
  input_conflicts?: unknown[];
  ledger_event_count?: number;
  ledger_well_count?: number;
  ledger_tip_count?: number;
  ledger_reagent_count?: number;
  reason?: string;
  [key: string]: unknown;
}

export interface LlmReviewFinding {
  severity?: string;
  claim?: string;
  evidence?: string;
  suggestion?: string;
}

export interface LlmReviewResult {
  match?: boolean;
  findings?: LlmReviewFinding[];
  reason?: string;
}

export type CheckStatus = "pass" | "fail" | "unevaluable";

export interface ChecksResult {
  sim: SimResult;
  logicpass: LogicPassResult;
  statepass: StatePassResult;
  llmreview?: LlmReviewResult;
  fab: { lit: boolean };
  status: CheckStatus;
  consequences?: string[];
}

export function fabLit(sim: SimResult, logicpass: LogicPassResult): boolean {
  return Boolean(
    sim.ok &&
      logicpass.outcome === "pass" &&
      logicpass.logic_pass === true &&
      logicpass.final_pass_v2 === true
  );
}

/** Pass iff FAB is lit. Unevaluable is never pass. */
export function checkStatus(checks: {
  sim: SimResult;
  logicpass: LogicPassResult;
  fab: { lit: boolean };
}): CheckStatus {
  if (checks.fab.lit) return "pass";
  if (checks.logicpass.outcome === "unevaluable") return "unevaluable";
  if (
    checks.logicpass.outcome === "skipped" &&
    isUnevaluableCode(checks.logicpass.reason || checks.sim.reason)
  ) {
    return "unevaluable";
  }
  return "fail";
}

export function unevaluableLogic(reason: string): LogicPassResult {
  return {
    outcome: "unevaluable",
    logic_pass: false,
    final_pass_v2: false,
    issues: [],
    reason,
  };
}

/** LogicPass was not run (sim fail / raise-only). Not the same as unevaluable. */
export function skippedLogic(reason: string): LogicPassResult {
  return {
    outcome: "skipped",
    logic_pass: false,
    final_pass_v2: false,
    issues: [],
    reason,
  };
}

export function forceRaiseOnlySim(httpSim?: SimResult): SimResult {
  const errors = [...(httpSim?.errors ?? [])];
  if (httpSim?.ok) {
    errors.push("raise-only script cannot be treated as sim success");
  }
  if (!errors.length) errors.push("raise-only script is not a protocol");
  return { ok: false, reason: "raise_only", errors };
}

export function sanitizeLogicpass(
  raw: Record<string, unknown> | null | undefined
): LogicPassResult {
  const issues = Array.isArray(raw?.issues) ? raw.issues : [];
  const coverage = raw?.coverage;
  const reason = typeof raw?.reason === "string" ? raw.reason : undefined;
  const outcome = raw?.outcome;
  const logicPass = raw?.logic_pass === true;
  const finalPass = raw?.final_pass_v2;

  if (outcome === "fail") {
    return {
      outcome: "fail",
      logic_pass: false,
      final_pass_v2: false,
      issues,
      coverage,
      reason,
    };
  }

  if (outcome === "pass" && logicPass && (finalPass === true || finalPass === undefined)) {
    return {
      outcome: "pass",
      logic_pass: true,
      final_pass_v2: true,
      issues,
      coverage,
      reason,
    };
  }

  return {
    outcome: "unevaluable",
    logic_pass: false,
    final_pass_v2: false,
    issues,
    coverage,
    reason: reason ?? "invalid_logicpass_outcome",
  };
}

export type AnalyzeInspect =
  | { ok: true }
  | { ok: false; reason: "missing_analyze_artifact" | "analyze_has_errors" | "missing_commands" };

export function inspectAnalyze(payload: Record<string, unknown> | null): AnalyzeInspect {
  if (!payload) return { ok: false, reason: "missing_analyze_artifact" };
  const errors = payload.errors;
  if (Array.isArray(errors) && errors.length > 0) {
    return { ok: false, reason: "analyze_has_errors" };
  }
  const commands = payload.commands;
  if (!Array.isArray(commands) || commands.length === 0) {
    return { ok: false, reason: "missing_commands" };
  }
  return { ok: true };
}

export function emptyStatepass(reason?: string): StatePassResult {
  return {
    issues: [],
    coverage: {},
    input_conflicts: [],
    ledger_event_count: 0,
    ledger_well_count: 0,
    ledger_tip_count: 0,
    ledger_reagent_count: 0,
    ...(reason ? { reason } : {}),
  };
}

export function wrapChecks(
  sim: SimResult,
  logicpass: LogicPassResult,
  statepass: StatePassResult,
  llmreview?: LlmReviewResult
): ChecksResult {
  return attachConsequences({
    sim,
    logicpass,
    statepass,
    fab: { lit: fabLit(sim, logicpass) },
    ...(llmreview ? { llmreview } : {}),
  });
}

export function attachConsequences(
  checks: Omit<ChecksResult, "status" | "consequences"> & {
    status?: CheckStatus;
    consequences?: string[];
  }
): ChecksResult {
  return { ...checks, status: checkStatus(checks), consequences: collectConsequences(checks) };
}

export function issueLine(item: unknown, unevaluable = false): string {
  return formatIssue(item, unevaluable);
}

export const PATCH_CAP = 1;

export const PATCH_BUDGET_REFUSAL =
  "Patch budget used. Stop calling tools. Tell the user what fails, what that means for their experiment, and ask how to proceed.";

/** Iterate when FAB is dark, or when llmreview explicitly disagrees. */
export function needsPatch(checks: ChecksResult | null | undefined): boolean {
  if (!checks) return false;
  if (!checks.fab.lit) return true;
  return checks.llmreview?.match === false;
}

/** One patch per turn. Further generate_code/emit_plan calls must be refused. */
export function patchCapHit(
  patchesUsed: number,
  checks: ChecksResult | null | undefined
): boolean {
  if (patchesUsed < PATCH_CAP) return false;
  return !checks || needsPatch(checks);
}

export function isPatchBudgetRefusal(details: unknown): boolean {
  return Boolean(
    details && typeof details === "object" && (details as { refused?: boolean }).refused
  );
}

export function compactChecks(
  checks: ChecksResult,
  patchesUsed = 0
): {
  sim: { ok: boolean; consequence?: string };
  logicpass: { outcome: string; issues: string[] };
  review: { match?: boolean; findings: string[] };
  fab: { lit: boolean };
  next: "patch" | "done";
  consequences: string[];
} {
  const uneval = checks.logicpass.outcome === "unevaluable";
  const issues = (checks.logicpass.issues ?? [])
    .slice(0, 3)
    .map((item) => issueLine(item, uneval))
    .filter(Boolean);
  const findings = (checks.llmreview?.findings ?? []).slice(0, 2).map(issueLine).filter(Boolean);
  const iterate = needsPatch(checks) && patchesUsed < PATCH_CAP;
  const consequences = checks.consequences ?? collectConsequences(checks);
  return {
    sim: {
      ok: checks.sim.ok,
      ...(!checks.sim.ok
        ? { consequence: formatReason(checks.sim.reason || "sim_failed", isUnevaluableCode(checks.sim.reason)) }
        : {}),
    },
    logicpass: { outcome: String(checks.logicpass.outcome), issues },
    review: {
      ...(typeof checks.llmreview?.match === "boolean" ? { match: checks.llmreview.match } : {}),
      findings,
    },
    fab: { lit: checks.fab.lit },
    next: iterate ? "patch" : "done",
    consequences: consequences.slice(0, 5),
  };
}

export function patchInstruction(checks: ChecksResult): string {
  const lines = [
    "Patch this Opentrons protocol. Apply the check failures and review findings. Return a complete runnable script.",
  ];
  if (!checks.sim.ok) {
    lines.push(formatReason(checks.sim.reason || "sim_failed", isUnevaluableCode(checks.sim.reason)));
    for (const err of (checks.sim.errors ?? []).slice(0, 3)) {
      const text = issueLine(err);
      if (text && text !== checks.sim.reason) lines.push(`- ${text}`);
    }
  }
  const uneval = checks.logicpass.outcome === "unevaluable";
  const issues = (checks.logicpass.issues ?? [])
    .slice(0, 3)
    .map((item) => issueLine(item, uneval))
    .filter(Boolean);
  if (issues.length) {
    lines.push("Logic check:");
    for (const item of issues) lines.push(`- ${item}`);
  }
  const findings = (checks.llmreview?.findings ?? []).slice(0, 3);
  if (findings.length) {
    lines.push("Review:");
    for (const item of findings) {
      if (item && typeof item === "object") {
        const rec = item as LlmReviewFinding;
        const claim = (rec.claim || "").trim();
        const suggestion = (rec.suggestion || "").trim();
        lines.push(`- ${claim}${suggestion ? ` → ${suggestion}` : ""}`.trim());
      } else {
        const text = issueLine(item);
        if (text) lines.push(`- ${text}`);
      }
    }
  }
  if (checks.llmreview?.match === false) {
    lines.push("Review does not match the goal; patch even if simulation passed.");
  }
  return lines.join("\n");
}

const LLMREVIEW_SKIP_REASONS = new Set([
  "logicpass_package_missing",
  "logicpass_cli_spawn_failed",
  "logicpass_cli_bad_json",
  "raise_only",
  "plr_unavailable",
]);

export function shouldRunLlmreview(sim: SimResult, logicpass: LogicPassResult): boolean {
  if (!sim.ok) return false;
  if (logicpass.outcome === "skipped") return false;
  if (logicpass.outcome === "fail") return false;
  if (LLMREVIEW_SKIP_REASONS.has(logicpass.reason ?? "")) return false;
  if (logicpass.outcome === "pass") return true;
  if (
    logicpass.outcome === "unevaluable" &&
    (logicpass.reason === "missing_analyze_artifact" || logicpass.reason === "missing_analyze")
  ) {
    return true;
  }
  return false;
}

function stripPythonCommentsAndDocs(src: string): string {
  return src
    .replace(/#.*$/gm, "")
    .replace(/"""[\s\S]*?"""/g, "")
    .replace(/'''[\s\S]*?'''/g, "");
}

function runBodyStatements(stripped: string): string[] | null {
  const match = stripped.match(
    /\bdef\s+run\s*\([^)]*\)\s*(?:->[^:]*)?:[ \t]*(.*)(?:\r?\n)([\s\S]*)/
  );
  if (!match) return null;
  const stmts: string[] = [];
  const sameLine = match[1].trim();
  if (sameLine) stmts.push(sameLine);
  for (const line of match[2].split("\n")) {
    if (line.trim() === "") continue;
    if (!/^[ \t]/.test(line)) break;
    stmts.push(line.trim());
  }
  return stmts;
}

export function looksLikeRaiseOnly(code: string): boolean {
  const src = code.trim();
  if (!src) return true;
  const stripped = stripPythonCommentsAndDocs(src);
  const body = runBodyStatements(stripped);
  if (body) {
    return body.length > 0 && body.every((stmt) => /^raise\b/.test(stmt));
  }
  const compact = stripped
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .join("\n");
  return /^raise\b/.test(compact);
}

export function refuseEmptySop(sop: string | undefined | null): string | null {
  const text = (sop ?? "").trim();
  if (!text || text === "none") {
    return "generate_code refused: SOP is empty. Write or fill an SOP first.";
  }
  return null;
}
