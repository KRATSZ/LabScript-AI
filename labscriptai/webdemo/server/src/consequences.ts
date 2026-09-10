/** Consequence-first sentences for check codes/reasons. No raw code prefixes. */

export const CONSEQUENCE_BY_CODE: Record<string, string> = {
  "LP-OVERFLOW": "Liquid exceeds well capacity, it will spill.",
  "LP-L4": "Liquid exceeds well capacity, it will spill.",
  "LP-EMPTY": "Aspirating more than the well holds: air gets aspirated, the transfer is short.",
  "LP-L1": "Aspirating more than the well holds: air gets aspirated, the transfer is short.",
  "LP-PIPETTE-EMPTY": "Dispensing more than was aspirated: nothing left to dispense.",
  "LP-NO-TIP":
    "Liquid handling without a tip: nothing moves, and it would contaminate the pipette on real hardware.",
  "LP-TIP-LIQUID": "Dropping a tip that still holds liquid: reagent lost, deck contaminated.",
  "LP-CAPACITY-UNKNOWN":
    "Cannot verify: capacity of the named well(s) is unknown, so overflow cannot be ruled out.",
  capacity_unknown:
    "Cannot verify: capacity of the named well(s) is unknown, so overflow cannot be ruled out.",
  "LP-L5": "Cannot verify: the protocol trace is incomplete, so this check could not finish.",
  sim_failed: "The protocol cannot run as written (simulation failed).",
  plr_unavailable:
    "Cannot verify: the Hamilton/Tecan simulator is not installed, so only partial checks ran.",
  invalid_plan: "The protocol plan is not valid, so it cannot run.",
  raise_only: "The protocol only raises an error and never actually runs.",
  sim_timeout: "The protocol cannot run as written (simulation timed out).",
  plr_error: "The protocol cannot run as written (simulator error).",
  virtual_deck_error: "Cannot verify: the deck check could not complete.",
  missing_analyze_artifact:
    "Cannot verify: Opentrons analysis is missing, so overflow and empty-well checks cannot run.",
  missing_analyze:
    "Cannot verify: Opentrons analysis is missing, so overflow and empty-well checks cannot run.",
  missing_commands:
    "Cannot verify: Opentrons analysis has no commands, so the protocol cannot be checked.",
  analyze_has_errors:
    "Cannot verify: Opentrons analysis reported errors, so the protocol cannot be checked.",
};

const UNEVALUABLE = new Set([
  "LP-CAPACITY-UNKNOWN",
  "capacity_unknown",
  "LP-L5",
  "plr_unavailable",
  "virtual_deck_error",
  "missing_analyze_artifact",
  "missing_analyze",
  "missing_commands",
  "analyze_has_errors",
  "logicpass_package_missing",
  "logicpass_cli_spawn_failed",
  "logicpass_cli_bad_json",
  "invalid_logicpass_outcome",
]);

const CONSEQUENCE_CAP = 5;

export interface ConsequenceSource {
  sim: { ok: boolean; reason?: string; errors?: string[] };
  logicpass: { outcome?: string; issues?: unknown[]; reason?: string };
  llmreview?: { match?: boolean; findings?: unknown[] };
}

function str(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function canonical(code: string): string {
  const key = code.trim();
  if (key.startsWith("plr_error")) return "plr_error";
  if (key.startsWith("virtual_deck_error")) return "virtual_deck_error";
  return key;
}

export function isUnevaluableCode(code?: string): boolean {
  if (!code) return false;
  return UNEVALUABLE.has(canonical(code));
}

function lookup(code: string): string | undefined {
  return CONSEQUENCE_BY_CODE[canonical(code)];
}

function ensureUnevaluable(text: string, unevaluable: boolean): string {
  if (!unevaluable || text.startsWith("Cannot verify:")) return text;
  const rest = text.charAt(0).toLowerCase() + text.slice(1);
  return `Cannot verify: ${rest}`;
}

function fold(head: string, detail?: string): string {
  const d = (detail ?? "").trim();
  if (!d || d === head || head.includes(d)) return head;
  return `${head} ${d}`;
}

function stepDetail(rec: Record<string, unknown>): string {
  const detail = str(rec.detail_text) || str(rec.hint);
  const step =
    str(rec.step_id) || (typeof rec.step_index === "number" ? String(rec.step_index) : "");
  if (step && detail && !/step\s/i.test(detail)) return `Step ${step}: ${detail}`;
  return detail;
}

export function formatReason(reason?: string, unevaluable = false): string {
  const key = (reason ?? "").trim();
  const flagged = unevaluable || isUnevaluableCode(key);
  const mapped = key ? lookup(key) : undefined;
  if (mapped) return ensureUnevaluable(mapped, flagged);
  if (flagged) return "Cannot verify: a check could not be completed.";
  return "The protocol cannot run as written.";
}

export function formatIssue(item: unknown, unevaluable = false): string {
  if (typeof item === "string") {
    const text = item.trim();
    if (!text) return "";
    if (lookup(text) || isUnevaluableCode(text)) return formatReason(text, unevaluable);
    return text;
  }
  if (item && typeof item === "object") {
    const rec = item as Record<string, unknown>;
    const code = str(rec.code) || str(rec.reason);
    const detail = stepDetail(rec);
    const claim = str(rec.claim);
    const suggestion = str(rec.suggestion);
    const flagged = unevaluable || isUnevaluableCode(code);
    if (code) {
      const mapped = lookup(code);
      if (mapped) return fold(ensureUnevaluable(mapped, flagged), detail);
      if (detail) return ensureUnevaluable(detail, flagged);
      if (claim) return fold(claim, suggestion);
      return formatReason(code, flagged);
    }
    if (claim) return fold(claim, suggestion);
    if (detail) return ensureUnevaluable(detail, flagged);
  }
  const text = String(item ?? "").trim();
  return text;
}

export function collectConsequences(checks: ConsequenceSource, cap = CONSEQUENCE_CAP): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  const push = (line: string) => {
    const text = line.trim();
    if (!text || seen.has(text) || out.length >= cap) return;
    seen.add(text);
    out.push(text);
  };

  if (!checks.sim.ok) {
    push(formatReason(checks.sim.reason || "sim_failed", isUnevaluableCode(checks.sim.reason)));
    for (const err of (checks.sim.errors ?? []).slice(0, 2)) {
      const line = formatIssue(err);
      if (line && line !== checks.sim.reason) push(line);
    }
  }

  const uneval = checks.logicpass.outcome === "unevaluable";
  const issues = checks.logicpass.issues ?? [];
  for (const issue of issues.slice(0, 4)) {
    push(formatIssue(issue, uneval));
  }
  if (uneval && issues.length === 0 && checks.logicpass.reason) {
    push(formatReason(checks.logicpass.reason, true));
  }

  if (checks.llmreview?.match === false) {
    for (const finding of (checks.llmreview.findings ?? []).slice(0, 2)) {
      push(formatIssue(finding));
    }
  }

  return out;
}
