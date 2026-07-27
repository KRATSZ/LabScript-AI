import { recoveryAction, WATCH_L0_ACTIONS } from "../runtime-watch/autonomy.js";

export async function executeRuntimeSelfFix({
  args = {},
  recovery = {},
  attempt,
  executeRecovery,
} = {}) {
  if (typeof executeRecovery !== "function") {
    throw new Error("executeRuntimeSelfFix requires executeRecovery dependency.");
  }

  const action = recoveryAction(recovery);
  if (!WATCH_L0_ACTIONS.has(action)) {
    throw new Error(`runtime watch cannot auto-execute recovery action ${action || "unknown"}.`);
  }

  const executionArgs = {
    ...args,
    expected_action: action,
    idempotency_key: attempt?.idempotency_key,
    watch_mode: true,
  };

  return executeRecovery(executionArgs, { expectedAction: action, watchMode: true });
}

export function summarizeSelfFixResult({ recovery = {}, result = {} } = {}) {
  const action = recoveryAction(recovery);
  const finalStatus = result?.data?.final_run_history?.status || null;
  const executedParams = result?.data?.executed_params || {};
  const recoveryApplied = Boolean(result?.data?.resume_action);
  const summary = {
    action,
    recovery_applied: recoveryApplied,
    final_status: finalStatus,
    terminal_poll_skipped: result?.data?.terminal_poll_skipped === true,
    executed_params: executedParams,
    consumed_tips: [],
  };

  if (action === "retry_pick_up_tip_with_next_candidate" && executedParams.well) {
    summary.consumed_tips.push({
      tiprack_slot: executedParams.tiprack_slot || null,
      well: executedParams.well,
    });
  }

  return summary;
}
