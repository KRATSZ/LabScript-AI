import {
  acquireRunLock,
  appendAlert,
  readLatest,
  writeLatest,
} from "./alert-store.js";
import { loadAttemptQueue } from "./attempt-queue.js";
import {
  buildWatchMessage,
  classifyWatchSnapshot,
  failedCommandIdFromGuidance,
  runIdFromSnapshot,
  runStatusFromSnapshot,
} from "./classifier.js";
import { evaluateAutonomy, recoveryAction } from "./autonomy.js";
import {
  executeRuntimeSelfFix,
  summarizeSelfFixResult,
} from "../self-fix/orchestrator.js";

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function normalizeGuidance(guidance = {}) {
  const parsedError =
    guidance.parsedError ||
    guidance.parsed_error ||
    guidance.parse_error?.data ||
    guidance.parse_error ||
    {};
  const recoveryContainer =
    guidance.recoveryResult?.data ||
    guidance.suggest_recovery_action?.data ||
    guidance.recovery ||
    {};
  const recovery = recoveryContainer.recovery || recoveryContainer;
  const actionSummary =
    recoveryContainer.action_summary ||
    guidance.action_summary ||
    null;

  return {
    parsedError,
    recovery,
    actionSummary,
    raw: guidance,
  };
}

function latestPayload({
  status,
  runId,
  runStatus = null,
  reason = null,
  lastEvent = null,
  unreachableCount = null,
  parsedError = null,
  recovery = null,
  alert = null,
  attempt = null,
  execution = null,
} = {}) {
  return {
    status,
    run_status: runStatus,
    reason,
    last_event: lastEvent,
    unreachable_count: unreachableCount,
    parsed_error: parsedError,
    recovery,
    alert,
    attempt,
    execution,
    run_id: runId,
  };
}

function buildAlert({
  runId,
  status,
  level,
  parsedError,
  recovery,
  actionSummary = null,
  attemptDecision = null,
  extraData = {},
} = {}) {
  const action = recoveryAction(recovery);
  const failedCommandId =
    parsedError?.failed_command?.id ||
    extraData.failed_command_id ||
    "unknown-command";
  return {
    type: status === "auto_fixed" ? "auto_fixed" : "runtime_watch",
    status,
    level,
    message: buildWatchMessage({ status, parsedError, recovery }),
    dedupe_key: `${status}:${failedCommandId}:${action || "unknown"}`,
    requires_ack: !["completed", "auto_fixed"].includes(status),
    data: {
      action,
      parsed_error: parsedError,
      recovery,
      action_summary: actionSummary,
      attempt_decision: attemptDecision,
      ...extraData,
    },
  };
}

export async function runSentryStep(args = {}, dependencies = {}) {
  const runId = args.run_id;
  if (!runId) {
    throw new Error("runtime watch requires run_id.");
  }

  const watchDir = args.watch_dir || null;
  const maxSnapshotAgeMs = args.max_snapshot_age_ms ?? 120000;
  const unreachableThreshold = Math.max(1, Number(args.unreachable_threshold ?? 2));
  const readSnapshot = dependencies.readSnapshot;
  const readGuidance = dependencies.readGuidance;
  const executeRecovery = dependencies.executeRecovery;

  if (typeof readSnapshot !== "function") {
    throw new Error("runtime watch requires readSnapshot dependency.");
  }

  let snapshot;
  try {
    snapshot = await readSnapshot(args);
  } catch (error) {
    const previous = readLatest(runId, { watchDir });
    const unreachableCount = Number(previous?.unreachable_count || 0) + 1;
    if (unreachableCount < unreachableThreshold) {
      const latest = writeLatest(
        runId,
        latestPayload({
          status: "running",
          runId,
          reason: "snapshot_unreachable_retrying",
          unreachableCount,
        }),
        { watchDir },
      );
      return {
        status: "running",
        data: latest,
      };
    }

    const alert = appendAlert(
      runId,
      {
        type: "runtime_watch",
        status: "unreachable",
        level: "L3",
        message: buildWatchMessage({ status: "unreachable" }),
        dedupe_key: "unreachable",
        data: {
          error: error instanceof Error ? error.message : String(error),
        },
      },
      { watchDir },
    );
    const latest = writeLatest(
      runId,
      latestPayload({
        status: "unreachable",
        runId,
        reason: "snapshot_unreachable",
        unreachableCount,
        alert,
      }),
      { watchDir },
    );
    return {
      status: "unreachable",
      data: latest,
    };
  }

  const snapshotWithTime = {
    fetched_at: new Date().toISOString(),
    ...snapshot,
  };
  const snapshotClass = classifyWatchSnapshot(snapshotWithTime, {
    maxSnapshotAgeMs,
  });
  const resolvedRunId = runIdFromSnapshot(snapshotWithTime, runId);
  const runStatus = snapshotClass.run_status || runStatusFromSnapshot(snapshotWithTime);

  if (snapshotClass.status === "completed") {
    const latest = writeLatest(
      runId,
      latestPayload({
        status: "completed",
        runId: resolvedRunId,
        runStatus,
        reason: snapshotClass.reason,
      }),
      { watchDir },
    );
    return {
      status: "completed",
      data: latest,
    };
  }

  if (snapshotClass.status === "running") {
    const latest = writeLatest(
      runId,
      latestPayload({
        status: "running",
        runId: resolvedRunId,
        runStatus,
        reason: snapshotClass.reason,
      }),
      { watchDir },
    );
    return {
      status: "running",
      data: latest,
    };
  }

  if (snapshotClass.status === "hard_stop" && typeof readGuidance !== "function") {
    const parsedError = {
      error_category: "HARDWARE_FAULT",
      error_leaf: snapshotClass.reason === "estop_engaged" ? "ESTOP_ENGAGED" : "DOOR_OPEN",
      hard_stop: true,
    };
    const recovery = {
      action: "manual_only",
      hard_stop: true,
      escalate_to_human: true,
    };
    const alert = appendAlert(
      runId,
      buildAlert({
        runId,
        status: "hard_stop",
        level: "L4",
        parsedError,
        recovery,
      }),
      { watchDir },
    );
    const latest = writeLatest(
      runId,
      latestPayload({
        status: "hard_stop",
        runId: resolvedRunId,
        runStatus,
        reason: snapshotClass.reason,
        parsedError,
        recovery,
        alert,
      }),
      { watchDir },
    );
    return {
      status: "hard_stop",
      data: latest,
    };
  }

  if (typeof readGuidance !== "function") {
    const latest = writeLatest(
      runId,
      latestPayload({
        status: "needs_user",
        runId: resolvedRunId,
        runStatus,
        reason: "guidance_reader_missing",
      }),
      { watchDir },
    );
    return {
      status: "needs_user",
      data: latest,
    };
  }

  let guidance;
  try {
    guidance = await readGuidance(args);
  } catch (error) {
    const previous = readLatest(runId, { watchDir });
    const unreachableCount = Number(previous?.unreachable_count || 0) + 1;
    if (unreachableCount < unreachableThreshold) {
      const latest = writeLatest(
        runId,
        latestPayload({
          status: "running",
          runId: resolvedRunId,
          runStatus,
          reason: "guidance_unreachable_retrying",
          unreachableCount,
        }),
        { watchDir },
      );
      return {
        status: "running",
        data: latest,
      };
    }

    const alert = appendAlert(
      runId,
      {
        type: "runtime_watch",
        status: "unreachable",
        level: "L3",
        message: buildWatchMessage({ status: "unreachable" }),
        dedupe_key: "guidance_unreachable",
        data: {
          error: error instanceof Error ? error.message : String(error),
        },
      },
      { watchDir },
    );
    const latest = writeLatest(
      runId,
      latestPayload({
        status: "unreachable",
        runId: resolvedRunId,
        runStatus,
        reason: "guidance_unreachable",
        unreachableCount,
        alert,
      }),
      { watchDir },
    );
    return {
      status: "unreachable",
      data: latest,
    };
  }

  const { parsedError, recovery, actionSummary } = normalizeGuidance(guidance);
  const action = recoveryAction(recovery);
  const failedCommandId = failedCommandIdFromGuidance({
    parsedError,
    snapshot: snapshotWithTime,
  });
  const queue = loadAttemptQueue(runId, {
    watchDir,
    maxAttemptsPerFailedCommand: args.max_attempts_per_failed_command ?? 3,
    staleRunningAfterMs: args.stale_running_after_ms ?? 1800000,
  });
  const attemptDecision = queue.canAttempt({
    failedCommandId,
    branch: action,
  });
  const autonomy = evaluateAutonomy({
    runStatus,
    parsedError,
    recovery,
    attemptDecision,
  });

  if (!autonomy.can_execute) {
    const alertStatus = autonomy.status === "hard_stop" ? "hard_stop" : "needs_user";
    const alert = appendAlert(
      runId,
      buildAlert({
        runId,
        status: alertStatus,
        level: autonomy.level,
        parsedError,
        recovery,
        actionSummary,
        attemptDecision,
        extraData: {
          failed_command_id: failedCommandId,
          autonomy,
        },
      }),
      { watchDir },
    );
    const latest = writeLatest(
      runId,
      latestPayload({
        status: alertStatus,
        runId: resolvedRunId,
        runStatus,
        reason: autonomy.reason,
        parsedError,
        recovery,
        alert,
      }),
      { watchDir },
    );
    return {
      status: alertStatus,
      data: latest,
    };
  }

  const lock = acquireRunLock(runId, {
    watchDir,
    staleMs: args.lock_stale_ms ?? 120000,
  });
  if (!lock.acquired) {
    const latest = writeLatest(
      runId,
      latestPayload({
        status: "running",
        runId: resolvedRunId,
        runStatus,
        reason: "runtime_watch_lock_held",
        parsedError,
        recovery,
      }),
      { watchDir },
    );
    return {
      status: "running",
      data: latest,
    };
  }

  let attempt = null;
  try {
    attempt = queue.beginAttempt({
      failedCommandId,
      errorLeaf: parsedError.error_leaf,
      branch: action,
      gate: autonomy.level,
    });
    const execution = await executeRuntimeSelfFix({
      args,
      recovery,
      attempt,
      executeRecovery,
    });
    const summary = summarizeSelfFixResult({ recovery, result: execution });
    const terminalSuccess = ["succeeded", "completed"].includes(String(summary.final_status || "").toLowerCase());
    const recoveryApplied = summary.recovery_applied === true;
    const finishedAttempt = queue.finishAttempt(attempt.attempt_id, {
      status: recoveryApplied ? "succeeded" : "failed",
      result: summary,
    });

    if (terminalSuccess) {
      const autoFixedAlert = appendAlert(
        runId,
        buildAlert({
          runId,
          status: "auto_fixed",
          level: "L0",
          parsedError,
          recovery,
          actionSummary,
          attemptDecision,
          extraData: {
            failed_command_id: failedCommandId,
            consumed_tips: summary.consumed_tips,
            self_fix: summary,
          },
        }),
        { watchDir, dedupe: false },
      );
      const alert = appendAlert(
        runId,
        buildAlert({
          runId,
          status: "completed",
          level: "L2",
          parsedError,
          recovery,
          actionSummary,
          attemptDecision,
          extraData: {
            failed_command_id: failedCommandId,
            consumed_tips: summary.consumed_tips,
            self_fix: summary,
          },
        }),
        { watchDir, dedupe: false },
      );
      const latest = writeLatest(
        runId,
        latestPayload({
          status: "completed",
          runId: resolvedRunId,
          runStatus: summary.final_status,
          reason: "auto_fix_completed",
          parsedError,
          recovery,
          alert,
          attempt: finishedAttempt,
          execution,
          lastEvent: autoFixedAlert.type,
        }),
        { watchDir },
      );
      return {
        status: "completed",
        data: latest,
      };
    }

    if (recoveryApplied) {
      const alert = appendAlert(
        runId,
        buildAlert({
          runId,
          status: "auto_fixed",
          level: "L0",
          parsedError,
          recovery,
          actionSummary,
          attemptDecision,
          extraData: {
            failed_command_id: failedCommandId,
            consumed_tips: summary.consumed_tips,
            self_fix: summary,
          },
        }),
        { watchDir, dedupe: false },
      );
      const latest = writeLatest(
        runId,
        latestPayload({
          status: "running",
          runId: resolvedRunId,
          runStatus: summary.final_status || "running",
          reason: "auto_fix_applied",
          lastEvent: "auto_fixed",
          parsedError,
          recovery,
          alert,
          attempt: finishedAttempt,
          execution,
        }),
        { watchDir },
      );
      return {
        status: "running",
        data: latest,
      };
    }

    const latest = writeLatest(
      runId,
      latestPayload({
        status: "needs_user",
        runId: resolvedRunId,
        runStatus: summary.final_status,
        reason: "auto_fix_not_applied",
        parsedError,
        recovery,
        attempt: finishedAttempt,
        execution,
      }),
      { watchDir },
    );
    return {
      status: "needs_user",
      data: latest,
    };
  } catch (error) {
    let finishedAttempt = attempt;
    if (attempt) {
      finishedAttempt = queue.finishAttempt(attempt.attempt_id, {
        status: "failed",
        result: {
          error: error instanceof Error ? error.message : String(error),
        },
      });
    }
    const alert = appendAlert(
      runId,
      buildAlert({
        runId,
        status: "needs_user",
        level: "L3",
        parsedError,
        recovery,
        actionSummary,
        attemptDecision,
        extraData: {
          failed_command_id: failedCommandId,
          autonomy,
          error: error instanceof Error ? error.message : String(error),
        },
      }),
      { watchDir },
    );
    const latest = writeLatest(
      runId,
      latestPayload({
        status: "needs_user",
        runId: resolvedRunId,
        runStatus,
        reason: "auto_fix_failed",
        parsedError,
        recovery,
        alert,
        attempt: finishedAttempt,
      }),
      { watchDir },
    );
    return {
      status: "needs_user",
      data: latest,
    };
  } finally {
    lock.release();
  }
}

export async function runtimeWatchPoll(args = {}, dependencies = {}) {
  const runId = args.run_id;
  if (!runId) {
    throw new Error("runtime_watch_poll requires run_id.");
  }

  const maxBlockMs = Math.max(0, Math.min(Number(args.max_block_ms ?? 50000), 120000));
  const pollIntervalMs = Math.max(250, Math.min(Number(args.poll_interval_ms ?? 3000), 10000));
  const deadline = Date.now() + maxBlockMs;
  let latestResult = null;

  do {
    const remainingMs = Math.max(1, deadline - Date.now());
    latestResult = await runSentryStep(
      {
        ...args,
        timeout_ms: Math.min(Number(args.timeout_ms ?? remainingMs), remainingMs),
        module_wait_timeout_ms: Math.min(
          Number(args.module_wait_timeout_ms ?? remainingMs),
          remainingMs,
        ),
      },
      dependencies,
    );

    if (latestResult.status !== "running") {
      return latestResult;
    }

    const remainingAfterStep = deadline - Date.now();
    if (remainingAfterStep <= 0) {
      break;
    }
    await sleep(Math.min(pollIntervalMs, remainingAfterStep));
  } while (Date.now() < deadline);

  return latestResult || {
    status: "running",
    data: readLatest(runId, { watchDir: args.watch_dir || null }) || {
      status: "running",
      run_id: runId,
      reason: "poll_window_elapsed",
    },
  };
}
