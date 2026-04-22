import { summarizeResultLogEntries } from "./result-log.js";

function uniqueOrdered(items = []) {
  const seen = new Set();
  const out = [];
  for (const item of items) {
    if (!item || seen.has(item)) {
      continue;
    }
    seen.add(item);
    out.push(item);
  }
  return out;
}

/**
 * Build a structured restart / resume snapshot from persisted session state,
 * recent result-log entries, and optional live-derived home safety.
 */
export function buildRestartReview({
  sessionState = {},
  logEntries = [],
  homeSafety = null,
} = {}) {
  const pendingCleanup = sessionState.cleanup?.pending_actions || [];
  const sessionSummary = {
    session_id: sessionState.session_id || null,
    state_revision: Number(sessionState.state_revision || 0),
    needs_reconciliation: Boolean(sessionState.needs_reconciliation),
    last_run_id: sessionState.last_run_id || null,
    robot_serial: sessionState.robot_serial || null,
    cleanup_pending_actions: pendingCleanup,
    cleanup_pending_count: pendingCleanup.length,
  };

  const logSummary = summarizeResultLogEntries(logEntries);

  const needsReconcile = sessionState.needs_reconciliation === true;
  const lastRunId = sessionState.last_run_id || null;
  const followActiveRun = Boolean(String(lastRunId || "").trim());

  const suggestedToolOrder = uniqueOrdered([
    ...(needsReconcile ? ["reconcile_state"] : []),
    "robot_status",
    "module_status",
    ...(followActiveRun ? ["run_history", "parse_error"] : []),
    "experiment_history",
    "is_home_safe",
  ]);

  let narrative = needsReconcile
    ? "Session needs_reconciliation is true: call reconcile_state before autonomous physical motion. Result logs are audit-only and may show older successes that do not reflect the deck now."
    : "Committed session state has no reconciliation flag; still poll robot_status and module_status after restart. Use experiment_history only for narrative context, not current deck truth.";

  if (homeSafety && homeSafety.auto_home_allowed === false) {
    narrative +=
      " Live home-safety preview disallows auto-home; clear blockers and cleanup first even when recent logs look successful.";
  }

  return {
    session_summary: sessionSummary,
    recent_log_entries: logEntries,
    recent_log_summary: logSummary,
    guidance: {
      reconcile_first: needsReconcile,
      logs_are_historical_only: true,
      narrative,
      suggested_tool_order: suggestedToolOrder,
      home_safety_preview: homeSafety
        ? {
            auto_home_allowed: homeSafety.auto_home_allowed,
            blockers: homeSafety.blockers || [],
            minimum_cleanup_actions: homeSafety.minimum_cleanup_actions || [],
          }
        : null,
    },
  };
}

const TOOL_HINTS = {
  reconcile_state: "Sync committed session deck state with the physical deck.",
  robot_status: "Live door, estop, and current command snapshot.",
  module_status: "Module readiness (thermocycler, heater-shaker, temperature).",
  run_history: "Command timeline for the active or last run.",
  parse_error: "Structured runtime error for a run.",
  experiment_history: "Audit narrative from persisted logs only.",
  is_home_safe: "Gate before homing or cleanup that implies homing.",
};

/**
 * Thin operator-facing summary on top of buildRestartReview output.
 * Does not replace atomic tools; points to the single best next MCP call.
 */
export function buildSafeNextAction(restartReviewData = {}) {
  const guidance = restartReviewData.guidance || {};
  const sessionSummary = restartReviewData.session_summary || {};
  const homeSafetyPreview = guidance.home_safety_preview || null;

  const reconcileFirst = guidance.reconcile_first === true;
  const lastRunId = sessionSummary.last_run_id || null;
  const homeBlocked = homeSafetyPreview?.auto_home_allowed === false;
  const homeBlockers = homeSafetyPreview?.blockers || [];
  const minimumCleanupActions = homeSafetyPreview?.minimum_cleanup_actions || [];

  const recommended_next_tool = reconcileFirst ? "reconcile_state" : "robot_status";

  const rationale_short = reconcileFirst
    ? "Session needs_reconciliation: align committed deck state before autonomous physical motion."
    : "Poll live robot_status first; persisted logs are historical and not current deck truth.";

  const operator_steps = [];
  let n = 1;
  if (reconcileFirst) {
    operator_steps.push(
      `${n++}. Call reconcile_state for this session until the deck matches reality.`,
    );
  }
  operator_steps.push(`${n++}. Call robot_status and module_status (pass robot_ip).`);
  if (lastRunId) {
    operator_steps.push(
      `${n++}. last_run_id is set (${lastRunId}): use run_history then parse_error if that run still matters.`,
    );
  }
  if (homeBlocked) {
    operator_steps.push(
      `${n++}. Do not home yet; live preview shows blockers: ${homeBlockers.join(", ") || "see home_safety_preview"}.`,
    );
    if (minimumCleanupActions.length > 0) {
      operator_steps.push(
        `${n++}. Minimum cleanup before home: ${minimumCleanupActions.join(", ")}.`,
      );
    }
  }
  operator_steps.push(
    `${n++}. Use experiment_history only for audit context, not as current deck truth.`,
  );
  operator_steps.push(
    `${n++}. Before home: is_home_safe (or use home_safety_preview when robot_ip was provided).`,
  );

  const suggested = guidance.suggested_tool_order || [];
  const tool_sequence = suggested.map((tool, idx) => ({
    order: idx + 1,
    tool,
    hint: TOOL_HINTS[tool] || "See MCP tool description.",
  }));

  return {
    recommended_next_tool,
    rationale_short,
    operator_steps,
    tool_sequence,
    reconcile_first: reconcileFirst,
    home_action_required: homeBlocked,
    home_blockers: homeBlockers,
    minimum_cleanup_actions: minimumCleanupActions,
    note:
      "Atomic tools remain available; this block is a single-entry summary for operators after MCP/host restart.",
  };
}
