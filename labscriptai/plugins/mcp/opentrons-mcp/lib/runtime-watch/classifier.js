function unwrapData(payload) {
  if (payload && typeof payload === "object" && "data" in payload) {
    return payload.data;
  }
  return payload;
}

function readNested(value, candidates, fallback = null) {
  for (const candidate of candidates) {
    let current = value;
    let found = true;
    for (const part of candidate) {
      if (current && typeof current === "object" && part in current) {
        current = current[part];
      } else {
        found = false;
        break;
      }
    }
    if (found && current !== undefined) {
      return current;
    }
  }
  return fallback;
}

function normalizeRunStatus(status) {
  return String(status || "").trim().toLowerCase();
}

export function runStatusFromSnapshot(snapshot = {}) {
  const runHistory = snapshot.runHistoryResult || snapshot.run_history || {};
  const run = unwrapData(runHistory.hardwareSnapshot?.run || snapshot.run || {});
  return (
    readNested(runHistory, [["data", "status"], ["status"]], null) ||
    readNested(run, [["status"]], null)
  );
}

export function runIdFromSnapshot(snapshot = {}, fallback = null) {
  const runHistory = snapshot.runHistoryResult || snapshot.run_history || {};
  const run = unwrapData(runHistory.hardwareSnapshot?.run || snapshot.run || {});
  return (
    readNested(runHistory, [["runId"], ["data", "run_id"], ["run_id"]], null) ||
    readNested(run, [["id"]], null) ||
    fallback
  );
}

export function failedCommandIdFromGuidance({ parsedError = {}, snapshot = {} } = {}) {
  return (
    readNested(parsedError, [["failed_command", "id"]], null) ||
    readNested(snapshot, [["runHistoryResult", "data", "latest_failed_command", "id"]], null) ||
    readNested(snapshot, [["run_history", "data", "latest_failed_command", "id"]], null) ||
    ""
  );
}

export function classifyWatchSnapshot(snapshot = {}, { now = Date.now(), maxSnapshotAgeMs = 120000 } = {}) {
  const fetchedAt = snapshot.fetched_at || snapshot.fetchedAt || null;
  if (fetchedAt) {
    const fetchedMs = Date.parse(fetchedAt);
    if (!Number.isFinite(fetchedMs) || now - fetchedMs > maxSnapshotAgeMs) {
      return {
        status: "unreachable",
        run_status: null,
        reason: "stale_snapshot",
      };
    }
  }

  const runStatus = runStatusFromSnapshot(snapshot);
  const normalized = normalizeRunStatus(runStatus);
  const robotBlockers =
    snapshot.robotStatusResult?.data?.blockers ||
    snapshot.robot_status?.data?.blockers ||
    [];

  if (robotBlockers.includes("estop_engaged") || robotBlockers.includes("door_open")) {
    return {
      status: "hard_stop",
      run_status: runStatus,
      reason: robotBlockers.includes("estop_engaged") ? "estop_engaged" : "door_open",
    };
  }

  if (["succeeded", "completed"].includes(normalized)) {
    return {
      status: "completed",
      run_status: runStatus,
      reason: "run_terminal_success",
    };
  }

  if (normalized === "awaiting-recovery") {
    return {
      status: "awaiting_recovery",
      run_status: runStatus,
      reason: "run_awaiting_recovery",
    };
  }

  if (["failed", "stopped", "canceled", "cancelled", "blocked-by-open-door"].includes(normalized)) {
    return {
      status: "needs_user",
      run_status: runStatus,
      reason: `run_terminal_${normalized || "unknown"}`,
    };
  }

  return {
    status: "running",
    run_status: runStatus,
    reason: normalized ? "run_not_terminal" : "run_status_unknown",
  };
}

export function buildWatchMessage({ status, autonomy = null, parsedError = {}, recovery = {} } = {}) {
  const action = recovery?.action || recovery?.recovery?.action || autonomy?.action || null;
  const category = parsedError.error_category || recovery.error_category || "runtime";
  const leaf = parsedError.error_leaf || recovery.error_leaf || null;

  if (status === "completed") {
    return "run 已完成。";
  }

  if (status === "auto_fixed") {
    if (action === "retry_pick_up_tip_with_next_candidate") {
      return "已自动换 tip 并继续盯梢。";
    }
    if (action === "wait_and_poll_module_status" || action === "reconcile_state_first") {
      return "模块恢复后已自动继续盯梢。";
    }
    return "已自动修复一步并继续盯梢。";
  }

  if (status === "hard_stop") {
    return `检测到硬停风险（${leaf || category}），请到现场检查。`;
  }

  if (status === "needs_user") {
    if (action === "suggest_new_destination_slot") {
      const slots = recovery.candidate_destination_slots || [];
      const choices = slots.map(slot => slot.slot_name).filter(Boolean).join(" 或 ");
      return choices ? `目标槽位需要人工选择：请选 ${choices}。` : "目标槽位被占用，需要人工选择下一步。";
    }
    return `需要人工介入：${leaf || category}。`;
  }

  if (status === "unreachable") {
    return "暂时连不上机器人，未执行任何自动修复。";
  }

  return null;
}
