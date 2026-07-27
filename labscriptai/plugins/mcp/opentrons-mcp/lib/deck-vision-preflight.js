const ESCALATION_UNCERTAINTIES = new Set([
  "low_confidence",
  "ambiguous_class",
  "invalid_vision_json",
  "vision_process_failed",
  "uncertain_slot",
]);

export function isPreflightVisionEnabled() {
  const flag = String(process.env.OPENTRONS_PREFLIGHT_VISION || "on").trim().toLowerCase();
  return !["0", "false", "off", "no"].includes(flag);
}

export function resolveVlmProvider({ provider = null } = {}) {
  const resolved = String(provider || process.env.OPENTRONS_VLM_PROVIDER || "ark")
    .trim()
    .toLowerCase();
  if (["off", "none", "false", "0"].includes(resolved)) {
    return "off";
  }
  if (resolved === "kimi") {
    return "kimi";
  }
  return "ark";
}

export function shouldEscalateToVlm(visionResult = {}, { force = false } = {}) {
  if (force) {
    return { escalate: true, reasons: ["forced_by_operator"] };
  }

  const reasons = [];
  const uncertainties = Array.isArray(visionResult.uncertainties) ? visionResult.uncertainties : [];
  for (const item of uncertainties) {
    const normalized = String(item || "").toLowerCase();
    if (
      ESCALATION_UNCERTAINTIES.has(normalized) ||
      normalized.includes("low_confidence") ||
      normalized.includes("ambiguous") ||
      normalized.includes("uncertain")
    ) {
      reasons.push(`uncertainty:${item}`);
    }
  }

  const mismatches = Array.isArray(visionResult.mismatches) ? visionResult.mismatches : [];
  if (mismatches.length > 0) {
    for (const mismatch of mismatches) {
      reasons.push(`mismatch:${mismatch.slot}:${mismatch.reason || "unknown"}`);
    }
  }

  if (visionResult.summary && String(visionResult.summary).toLowerCase().includes("failed")) {
    reasons.push("vision_summary_failed");
  }

  // YOLO hard-review flag must escalate even when mismatches/uncertainties are empty.
  if (Boolean(visionResult.needs_human_review)) {
    reasons.push("yolo_needs_human_review");
  }

  return {
    escalate: reasons.length > 0,
    reasons,
  };
}

/**
 * Run optional VLM second opinion. Never throw — missing keys / API errors fall
 * through so consensus can still emit auto_fixable + reconcile.
 */
export async function runVlmSecondOpinion({
  escalate = false,
  provider = "ark",
  imagePath,
  expectedLayout = null,
  analyzeArk = null,
  analyzeKimi = null,
} = {}) {
  if (!escalate || provider === "off") {
    return { vlmResult: null, vlmError: null };
  }

  try {
    let raw;
    if (provider === "kimi") {
      if (typeof analyzeKimi !== "function") {
        throw new Error("Kimi VLM analyzer is not configured.");
      }
      raw = await analyzeKimi({
        image_path: imagePath,
        expected_layout: expectedLayout,
      });
    } else {
      if (typeof analyzeArk !== "function") {
        throw new Error("Ark VLM analyzer is not configured.");
      }
      raw = await analyzeArk({
        image_path: imagePath,
        expected_layout: expectedLayout,
      });
    }
    const vlmResult = raw?.data ?? raw ?? null;
    return { vlmResult, vlmError: null };
  } catch (error) {
    return {
      vlmResult: null,
      vlmError: {
        provider,
        message: error?.message || String(error),
        recoverable: true,
      },
    };
  }
}

function isVlmCleanAgree(vlmParsed) {
  if (!vlmParsed || typeof vlmParsed !== "object") {
    return false;
  }
  const possibleIssues = Array.isArray(vlmParsed.possible_issues) ? vlmParsed.possible_issues : [];
  return !Boolean(vlmParsed.needs_human_review) && possibleIssues.length === 0;
}

/**
 * Layout is consistent when YOLO has no mismatches and VLM (if present) reports
 * no layout issues. Empty/missing expected_layout is treated as no extra constraint;
 * VLM is already prompted to put expected_layout diffs into possible_issues.
 */
export function isLayoutConsistentWithExpected({
  yoloMismatches = [],
  vlmParsed = null,
  expectedLayout = null,
} = {}) {
  if (Array.isArray(yoloMismatches) && yoloMismatches.length > 0) {
    return false;
  }
  if (vlmParsed) {
    return isVlmCleanAgree(vlmParsed);
  }
  const hasExpected =
    expectedLayout &&
    typeof expectedLayout === "object" &&
    Object.keys(expectedLayout).length > 0;
  // Without VLM, cannot affirm expected layout when one was supplied.
  return !hasExpected;
}

function uniqueActions(actions = []) {
  const seen = new Set();
  const out = [];
  for (const action of actions) {
    const normalized = String(action || "").trim();
    if (!normalized || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    out.push(normalized);
  }
  return out;
}

function withoutPrimaryOperatorConfirm(actions = []) {
  return actions.filter(action => action !== "operator_confirm_deck_layout");
}

function vlmActionsPreferContinue(actions = []) {
  return actions.some(action => {
    const normalized = String(action || "").toLowerCase();
    return (
      normalized === "continue_critical_probe" ||
      normalized === "continue" ||
      normalized.startsWith("continue_")
    );
  });
}

/**
 * Phase 3b consensus statuses are machine-judged under HumanConfirmBudget.
 * Never emit needs_confirmation here — that status is final go-live only.
 */
export function summarizeDeckVisionConsensus({
  yoloResult = null,
  vlmResult = null,
  escalation = null,
  expectedLayout = null,
} = {}) {
  const mismatches = Array.isArray(yoloResult?.mismatches) ? yoloResult.mismatches : [];
  const vlmParsed = vlmResult?.parsed_result || null;
  const yoloNeedsHumanReview = Boolean(yoloResult?.needs_human_review);
  const vlmNeedsHumanReview = Boolean(vlmParsed?.needs_human_review);
  const possibleIssues = Array.isArray(vlmParsed?.possible_issues) ? vlmParsed.possible_issues : [];
  const vlmCleanAgree = isVlmCleanAgree(vlmParsed);
  const layoutConsistent = isLayoutConsistentWithExpected({
    yoloMismatches: mismatches,
    vlmParsed,
    expectedLayout,
  });
  const vlmActions = Array.isArray(vlmParsed?.recommended_next_actions)
    ? vlmParsed.recommended_next_actions
    : [];
  // Combined review signal for agents. YOLO review alone is not silently passed;
  // VLM clean agree can clear it via the escalation path below.
  const needsHumanReview = vlmNeedsHumanReview || (yoloNeedsHumanReview && !vlmCleanAgree);

  let status = "passed";
  let recommendedNextActions = [];

  if (mismatches.length > 0) {
    // Reconcile-able mismatch: auto_fixable so agents run reconcile_state first.
    // Never primary operator_confirm_deck_layout (vision ≠ deck truth).
    status = "auto_fixable";
    recommendedNextActions = uniqueActions([
      "reconcile_state",
      ...withoutPrimaryOperatorConfirm(vlmActions),
    ]);
  } else if (vlmNeedsHumanReview) {
    // True physical / human-review case — not a go-live verbal confirm.
    // Reconcile still comes first (vision ≠ deck truth); operator_confirm may follow.
    status = "needs_operator_physical_action";
    recommendedNextActions = uniqueActions(["reconcile_state", ...vlmActions]);
  } else if (possibleIssues.length > 0) {
    // Soft VLM issues with needs_human_review=false: never needs_confirmation.
    status = "auto_fixable";
    recommendedNextActions = uniqueActions([
      "reconcile_state",
      ...withoutPrimaryOperatorConfirm(vlmActions),
      ...(vlmActionsPreferContinue(vlmActions) ? ["continue_critical_probe"] : []),
    ]);
  } else if (escalation?.escalate || yoloNeedsHumanReview) {
    if (vlmCleanAgree && layoutConsistent) {
      // YOLO uncertain/escalated but VLM agrees cleanly — pass with audit flags.
      status = "passed";
      recommendedNextActions = uniqueActions([...vlmActions, "continue_critical_probe"]);
    } else if (vlmParsed) {
      // Residual uncertainty after VLM: auto-reconcile, not go-live confirm.
      status = "auto_fixable";
      recommendedNextActions = uniqueActions([
        "reconcile_state",
        ...withoutPrimaryOperatorConfirm(vlmActions),
        "continue_critical_probe",
      ]);
    } else {
      // Escalated / YOLO review with no VLM second opinion — reconcile first.
      // Prefer auto_fixable so HumanConfirmBudget still routes to reconcile_state.
      status = "auto_fixable";
      recommendedNextActions = ["reconcile_state", "deck_vision_check"];
    }
  } else {
    recommendedNextActions = uniqueActions([...vlmActions, "continue_critical_probe"]);
  }

  return {
    status,
    yolo_mismatch_count: mismatches.length,
    vlm_escalated: Boolean(escalation?.escalate),
    vlm_escalate_reasons: escalation?.reasons || [],
    needs_human_review: needsHumanReview,
    yolo_needs_human_review: yoloNeedsHumanReview,
    layout_consistent_with_expected: layoutConsistent,
    summary:
      vlmParsed?.summary ||
      yoloResult?.summary ||
      (mismatches.length > 0
        ? `YOLO detected ${mismatches.length} deck mismatches against expected layout.`
        : "Deck vision check completed."),
    recommended_next_actions: recommendedNextActions,
    observation_only: true,
    deck_truth_requires_reconcile: mismatches.length > 0 || status === "auto_fixable",
    expected_layout: expectedLayout || null,
  };
}

export function buildDeckVisionPreflightResult({
  imagePath,
  yoloResult,
  vlmResult = null,
  vlmError = null,
  escalation = null,
  expectedLayout = null,
  provider = "ark",
} = {}) {
  const consensus = summarizeDeckVisionConsensus({
    yoloResult,
    vlmResult,
    escalation,
    expectedLayout,
  });

  return {
    image_path: imagePath,
    sensors_used: vlmResult ? ["vision_check", `analyze_image_with_${provider}`] : ["vision_check"],
    vlm_provider: vlmResult || vlmError ? provider : null,
    vlm_used: Boolean(vlmResult),
    vlm_error: vlmError || null,
    yolo: yoloResult,
    vlm: vlmResult,
    escalation,
    consensus,
    subphase: "deck_vision",
  };
}
