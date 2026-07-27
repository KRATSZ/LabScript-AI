export const WATCH_L0_ACTIONS = new Set([
  "retry_pick_up_tip_with_next_candidate",
  "wait_and_poll_module_status",
  "reconcile_state_first",
]);

const HARD_STOP_CATEGORIES = new Set([
  "HARDWARE_FAULT",
  "DECK_COLLISION",
  "UNKNOWN",
]);

const HARD_STOP_LEAVES = new Set([
  "DECK_COLLISION",
  "DOOR_OPEN",
  "ESTOP_ENGAGED",
  "INSTRUMENT_NOT_READY",
  "UNKNOWN_NEEDS_HUMAN",
]);

function normalize(value) {
  return String(value || "").trim();
}

function lower(value) {
  return normalize(value).toLowerCase();
}

export function recoveryAction(recovery = {}) {
  return recovery?.recovery?.action || recovery?.action || null;
}

export function isHardStop(parsedError = {}, recovery = {}) {
  const category = normalize(parsedError.error_category || recovery.error_category).toUpperCase();
  const leaf = normalize(parsedError.error_leaf || recovery.error_leaf).toUpperCase();
  return (
    parsedError.hard_stop === true ||
    recovery.hard_stop === true ||
    HARD_STOP_CATEGORIES.has(category) ||
    HARD_STOP_LEAVES.has(leaf)
  );
}

export function evaluateAutonomy({
  runStatus,
  parsedError = {},
  recovery = {},
  attemptDecision = null,
} = {}) {
  const action = recoveryAction(recovery);
  const normalizedRunStatus = lower(runStatus);

  if (isHardStop(parsedError, recovery)) {
    return {
      level: "L4",
      status: "hard_stop",
      can_execute: false,
      action,
      reason: "hard_stop_error",
    };
  }

  if (
    recovery.escalate_to_human === true ||
    recovery.requires_confirmation === true ||
    recovery.actionability === "manual_confirmation_required"
  ) {
    return {
      level: "L3",
      status: "needs_user",
      can_execute: false,
      action,
      reason: "human_review_required",
    };
  }

  if (normalizedRunStatus !== "awaiting-recovery") {
    return {
      level: "L3",
      status: "needs_user",
      can_execute: false,
      action,
      reason: "run_not_awaiting_recovery",
    };
  }

  if (recovery.auto_executable !== true) {
    return {
      level: "L3",
      status: "needs_user",
      can_execute: false,
      action,
      reason: "recovery_not_auto_executable",
    };
  }

  if (!WATCH_L0_ACTIONS.has(action)) {
    return {
      level: "L3",
      status: "needs_user",
      can_execute: false,
      action,
      reason: "action_not_in_runtime_watch_l0",
    };
  }

  if (attemptDecision && attemptDecision.allowed !== true) {
    return {
      level: "L3",
      status: "needs_user",
      can_execute: false,
      action,
      reason: attemptDecision.reason || "attempt_queue_rejected",
    };
  }

  return {
    level: "L0",
    status: "auto_fix",
    can_execute: true,
    action,
    reason: "runtime_watch_l0_allowed",
  };
}
