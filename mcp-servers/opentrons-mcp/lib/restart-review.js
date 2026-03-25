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
