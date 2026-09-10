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
  compile_state_machine:
    "The robot would try to aspirate with no tips loaded — on the bench that means spraying or nothing happens.",
  compile_mapping:
    "A plate or well in the plan does not match the Fluent deck, so the robot cannot find that location.",
  compile_internal: "The Fluent compiler could not finish, so no worklist was produced.",
  NoTipError:
    "A step needs a tip that is not on the channel: nothing transfers, and the pipette can get wet. Add PICK_TIPS before that aspirate or dispense, or pick a tip well that still has a tip.",
  HasTipError:
    "The channel already has a tip, so it cannot pick another — crash or a stuck tip. Drop the current tip before the next PICK_TIPS.",
  TooLittleVolumeError:
    "That volume does not fit in the tip or well: liquid will spill or the robot will refuse. Lower the volume, split the transfer, or stay within 300 µL tips / 360 µL Corning wells on the STAR standard deck.",
  TooLittleLiquidError:
    "There is not enough liquid in that well or tip: air gets aspirated, the transfer is short. Lower the volume or put more reagent in that well.",
  ResourceNotFoundError:
    "A plate or tip rack in the plan is not on the deck, so the robot cannot find it. Declare it in resources[] and match the session deck.",
  NoLocationError:
    "A labware location was never assigned on the deck, so the head cannot go there. Give every resource a slot that matches the session deck.",
  WellNotFound:
    "The head would go to a well that is not on that plate, so the robot cannot complete the step. Use a well that exists on the labware (A1–H12 on a 96-well plate).",
  BadLocation:
    "A step location is not written as plate:well, so the robot cannot find it. Write locations like plate:A1.",
  CrossContaminationError:
    "The same tip would go into a second liquid: samples mix on the bench. Drop that tip and pick a fresh one before touching another reagent.",
  unmapped_sim_error:
    "The protocol cannot run as written. The simulator stopped at that step — check tip order, well names, and volumes against the deck.",
  plan_cli_spawn_failed:
    "Cannot verify: the plan checker did not start, so the protocol was not simulated.",
  plan_cli_bad_json:
    "Cannot verify: the plan checker returned unreadable output.",
  planir_package_missing:
    "Cannot verify: the plan checker is not installed, so the protocol was not simulated.",
  invalid_plan_json: "The protocol plan is not valid, so it cannot run.",
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
  "plan_cli_spawn_failed",
  "plan_cli_bad_json",
  "planir_package_missing",
]);

const CONSEQUENCE_CAP = 5;

export interface ConsequenceSource {
  sim: { ok: boolean; reason?: string; errors?: string[] };
  logicpass: { outcome?: string; issues?: unknown[]; reason?: string };
  llmreview?: { match?: boolean; findings?: unknown[] };
  compile?: { ok: boolean; stage?: string; error?: string; hint?: string };
}

function str(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

const PLR_CLASS_ORDER = [
  "TooLittleLiquidError",
  "TooLittleVolumeError",
  "ResourceNotFoundError",
  "NoLocationError",
  "CrossContaminationError",
  "NoTipError",
  "HasTipError",
] as const;

function classifyPlr(key: string): string | undefined {
  for (const name of PLR_CLASS_ORDER) {
    if (key.includes(name)) return name;
  }
  if (/\b(?:KeyError|IndexError)\b/.test(key) && /['"][A-Za-z]{1,2}\d{1,2}['"]/.test(key)) {
    return "WellNotFound";
  }
  if (/\bValueError\b/.test(key) && /unpack|not enough values/i.test(key)) return "BadLocation";
  if (/^[A-Za-z][A-Za-z0-9_.]*Error\b/.test(key)) return "unmapped_sim_error";
  return undefined;
}

function canonical(code: string): string {
  const key = code.trim();
  if (key.startsWith("plr_error")) return "plr_error";
  if (key.startsWith("virtual_deck_error")) return "virtual_deck_error";
  if (key === "state_machine" || key === "mapping" || key === "internal") return `compile_${key}`;
  const classified = classifyPlr(key);
  if (classified) return classified;
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
    if (/^LP-[A-Z0-9-]+$/.test(text)) return formatReason("unmapped_sim_error", unevaluable);
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

function reviewIsUnavailable(review?: { match?: boolean; findings?: unknown[]; reason?: string }): boolean {
  if (!review) return false;
  const reason = String(review.reason ?? "").toLowerCase();
  if (
    reason.includes("llmreview_") ||
    reason.includes("reviewer_exception") ||
    reason.startsWith("invalid_review")
  ) {
    return true;
  }
  return (review.findings ?? []).some((item) => {
    if (!item || typeof item !== "object") return false;
    return String((item as { claim?: string }).claim ?? "") === "reviewer_exception";
  });
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

  if (checks.compile && checks.compile.ok === false) {
    const stage = checks.compile.stage || "internal";
    push(fold(formatReason(stage), checks.compile.error));
  }

  const review = checks.llmreview;
  if (reviewIsUnavailable(review)) {
    push("Cannot verify: the reviewer did not finish, so this is not a mismatch.");
  } else if (review?.match === false) {
    for (const finding of (review.findings ?? []).slice(0, 2)) {
      push(formatIssue(finding));
    }
  }

  return out;
}
