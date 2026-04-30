const ERROR_LEAF_DEFINITIONS = {
  RUNTIME_UNAVAILABLE: {
    error_domain: "environment",
    severity: "error",
    recoverability: "environment_fix_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "doctor_local_runtime",
    evidence_sources: ["stdout", "stderr"],
  },
  PYTHON_ENV_BROKEN: {
    error_domain: "environment",
    severity: "error",
    recoverability: "environment_fix_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "health_check",
    evidence_sources: ["local_runtime", "filesystem"],
  },
  MCP_CONFIG_MISMATCH: {
    error_domain: "environment",
    severity: "error",
    recoverability: "environment_fix_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "health_check",
    evidence_sources: ["tool_config", "request_args"],
  },
  SYNTAX_OR_IMPORT: {
    error_domain: "protocol",
    severity: "error",
    recoverability: "protocol_edit_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "edit_protocol_and_retry_simulation",
    evidence_sources: ["stdout", "stderr", "protocol_source"],
  },
  API_MISUSE: {
    error_domain: "protocol",
    severity: "error",
    recoverability: "protocol_edit_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "edit_protocol_and_retry_simulation",
    evidence_sources: ["stdout", "stderr", "protocol_source"],
  },
  LABWARE_OR_MODULE_COMPAT: {
    error_domain: "protocol",
    severity: "error",
    recoverability: "protocol_edit_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "edit_protocol_and_retry_simulation",
    evidence_sources: ["stdout", "stderr", "protocol_source"],
  },
  MISSING_TRASH_OR_SETUP: {
    error_domain: "protocol",
    severity: "error",
    recoverability: "protocol_edit_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "edit_protocol_and_retry_simulation",
    evidence_sources: ["stdout", "stderr", "protocol_source"],
  },
  VOLUME_OR_RANGE_VIOLATION: {
    error_domain: "protocol",
    severity: "error",
    recoverability: "protocol_edit_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "edit_protocol_and_retry_simulation",
    evidence_sources: ["stdout", "stderr", "protocol_source"],
  },
  OUT_OF_TIPS: {
    error_domain: "protocol",
    severity: "error",
    recoverability: "protocol_edit_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "edit_protocol_and_retry_simulation",
    evidence_sources: ["stdout", "stderr", "protocol_source"],
  },
  SESSION_NEEDS_RECONCILIATION: {
    error_domain: "session_state",
    severity: "error",
    recoverability: "state_sync_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "reconcile_state",
    evidence_sources: ["session_state"],
  },
  STALE_LAST_RUN: {
    error_domain: "session_state",
    severity: "warning",
    recoverability: "state_review_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "run_history",
    evidence_sources: ["session_state", "result_logs"],
  },
  RUN_NOT_AWAITING_RECOVERY: {
    error_domain: "session_state",
    severity: "warning",
    recoverability: "state_review_required",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "run_history",
    evidence_sources: ["run_history"],
  },
  ROBOT_UNREACHABLE: {
    error_domain: "robot_state",
    severity: "error",
    recoverability: "manual_recovery",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "robot_health",
    evidence_sources: ["health_endpoint"],
  },
  DOOR_OPEN: {
    error_domain: "robot_state",
    severity: "error",
    recoverability: "manual_recovery",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "robot_status",
    evidence_sources: ["door_status", "robot_status"],
  },
  ESTOP_ENGAGED: {
    error_domain: "robot_state",
    severity: "error",
    recoverability: "human_intervention_required",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "robot_status",
    evidence_sources: ["estop_status", "robot_status"],
  },
  INSTRUMENT_NOT_READY: {
    error_domain: "robot_state",
    severity: "error",
    recoverability: "manual_recovery",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "robot_status",
    evidence_sources: ["instruments", "robot_status"],
  },
  MODULE_NOT_READY: {
    error_domain: "module_state",
    severity: "warning",
    recoverability: "wait_then_retry",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "module_status",
    evidence_sources: ["modules", "module_status"],
  },
  DESTINATION_OCCUPIED: {
    error_domain: "deck_state",
    severity: "error",
    recoverability: "manual_recovery",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "suggest_recovery_action",
    evidence_sources: ["run_history", "commands", "deck_state"],
  },
  DESTINATION_UNAVAILABLE: {
    error_domain: "deck_state",
    severity: "error",
    recoverability: "manual_recovery",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "suggest_recovery_action",
    evidence_sources: ["run_history", "commands", "deck_configuration"],
  },
  LABWARE_MISMATCH: {
    error_domain: "deck_state",
    severity: "error",
    recoverability: "manual_recovery",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "reconcile_state",
    evidence_sources: ["protocol_source", "deck_configuration", "session_state"],
  },
  SLOT_NOT_ADDRESSABLE: {
    error_domain: "deck_state",
    severity: "error",
    recoverability: "manual_recovery",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "preflight_run_setup",
    evidence_sources: ["protocol_source", "deck_configuration"],
  },
  DECK_COLLISION: {
    error_domain: "motion_or_liquid",
    severity: "error",
    recoverability: "human_intervention_required",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "suggest_recovery_action",
    evidence_sources: ["run_history", "commands"],
  },
  TIP_PHYSICALLY_MISSING: {
    error_domain: "motion_or_liquid",
    severity: "error",
    recoverability: "runtime_fixit_available",
    requires_human_review: false,
    auto_executable: false,
    default_next_step: "suggest_recovery_action",
    evidence_sources: ["run_history", "commands", "session_state"],
  },
  TIP_CLOG: {
    error_domain: "motion_or_liquid",
    severity: "error",
    recoverability: "manual_recovery",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "suggest_recovery_action",
    evidence_sources: ["run_history", "commands"],
  },
  INSUFFICIENT_VOLUME: {
    error_domain: "motion_or_liquid",
    severity: "error",
    recoverability: "manual_recovery",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "suggest_recovery_action",
    evidence_sources: ["run_history", "commands"],
  },
  AIR_BUBBLE: {
    error_domain: "motion_or_liquid",
    severity: "error",
    recoverability: "manual_recovery",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "suggest_recovery_action",
    evidence_sources: ["run_history", "commands"],
  },
  LIQUID_PROPERTY_ERROR: {
    error_domain: "motion_or_liquid",
    severity: "error",
    recoverability: "manual_recovery",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "suggest_recovery_action",
    evidence_sources: ["run_history", "commands"],
  },
  UNKNOWN_NEEDS_HUMAN: {
    error_domain: "unknown",
    severity: "error",
    recoverability: "human_intervention_required",
    requires_human_review: true,
    auto_executable: false,
    default_next_step: "inspect_runtime_or_escalate",
    evidence_sources: ["stdout", "stderr", "run_history", "commands"],
  },
};

const SIMULATION_CATEGORY_TO_LEAF = {
  RUNTIME_UNAVAILABLE: "RUNTIME_UNAVAILABLE",
  MISSING_TRASH_OR_SETUP: "MISSING_TRASH_OR_SETUP",
  SYNTAX_OR_IMPORT: "SYNTAX_OR_IMPORT",
  API_MISUSE: "API_MISUSE",
  LABWARE_OR_MODULE_COMPAT: "LABWARE_OR_MODULE_COMPAT",
  VOLUME_OR_RANGE_VIOLATION: "VOLUME_OR_RANGE_VIOLATION",
  OUT_OF_TIPS: "OUT_OF_TIPS",
  UNKNOWN_NEEDS_HUMAN: "UNKNOWN_NEEDS_HUMAN",
};

const ROBOT_BLOCKER_TO_LEAF = {
  door_open: "DOOR_OPEN",
  estop_engaged: "ESTOP_ENGAGED",
  instrument_not_ready: "INSTRUMENT_NOT_READY",
};

export function normalizeErrorLeaf(errorLeaf) {
  return ERROR_LEAF_DEFINITIONS[errorLeaf] ? errorLeaf : "UNKNOWN_NEEDS_HUMAN";
}

export function getErrorTaxonomyDefinition(errorLeaf) {
  return ERROR_LEAF_DEFINITIONS[normalizeErrorLeaf(errorLeaf)];
}

export function mapSimulationCategoryToLeaf(category) {
  return normalizeErrorLeaf(SIMULATION_CATEGORY_TO_LEAF[category] || category);
}

export function mapRobotBlockerToLeaf(blocker) {
  return normalizeErrorLeaf(ROBOT_BLOCKER_TO_LEAF[blocker]);
}

export function buildErrorTaxonomy({
  phase,
  errorLeaf,
  overrides = {},
} = {}) {
  const definition = getErrorTaxonomyDefinition(errorLeaf);
  const taxonomy = {
    phase: phase || null,
    error_domain: definition.error_domain,
    error_leaf: normalizeErrorLeaf(errorLeaf),
    severity: overrides.severity || definition.severity,
    recoverability: overrides.recoverability || definition.recoverability,
    requires_human_review:
      overrides.requires_human_review ?? definition.requires_human_review,
    auto_executable: overrides.auto_executable ?? definition.auto_executable,
    default_next_step: overrides.default_next_step || definition.default_next_step,
    evidence_sources: overrides.evidence_sources || definition.evidence_sources,
  };

  if ("actionability" in overrides) {
    taxonomy.actionability = overrides.actionability;
  }
  if ("requires_confirmation" in overrides) {
    taxonomy.requires_confirmation = overrides.requires_confirmation;
  }
  if ("required_inputs" in overrides) {
    taxonomy.required_inputs = overrides.required_inputs;
  }

  return taxonomy;
}

export function buildTaxonomyIssue({
  phase,
  errorLeaf,
  message,
  overrides = {},
  extra = {},
} = {}) {
  return {
    ...buildErrorTaxonomy({ phase, errorLeaf, overrides }),
    message,
    ...extra,
  };
}
