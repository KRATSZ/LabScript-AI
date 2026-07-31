const PLAYBOOKS = Object.freeze({
  substitute_liquid_source_with_attached_tip: Object.freeze({
    id: "substitute_liquid_source_with_attached_tip",
    title: "Same-liquid reserve substitution with attached tip",
    level: "L0",
    error_leaves: ["INSUFFICIENT_VOLUME"],
    recovery_type: "alternative_resource",
    resource_type: "liquid_source",
    executor_tool: "recover_liquid_source_substitution",
    allowed_watch_mode: true,
    can_move_robot: true,
    requires_operator_opt_in: false,
    required_gates: ["run_status_awaiting_recovery", "same_liquid_identity", "reuse_attached_tip_eligible"],
    semantic_invariants: [
      "liquid_name_unchanged",
      "replacement_source_expected_present",
      "reuse_attached_tip_probe_and_transfer",
    ],
  }),
  retry_pick_up_tip_with_next_candidate: Object.freeze({
    id: "retry_pick_up_tip_with_next_candidate",
    title: "Retry missing tip with next candidate",
    level: "L0",
    error_leaves: ["TIP_PHYSICALLY_MISSING"],
    recovery_type: "small_action",
    executor_tool: "execute_protocol_recovery",
    allowed_watch_mode: true,
    can_move_robot: true,
    requires_operator_opt_in: false,
    required_gates: ["run_status_awaiting_recovery", "tip_binding_mode_auto"],
    semantic_invariants: [
      "same_protocol_run",
      "same_pipette_and_tiprack",
      "next_tip_well_not_missing_or_depleted",
    ],
  }),
  wait_and_poll_module_status: Object.freeze({
    id: "wait_and_poll_module_status",
    title: "Wait for module readiness and resume",
    level: "L0",
    error_leaves: ["MODULE_NOT_READY"],
    recovery_type: "small_action",
    executor_tool: "execute_protocol_recovery",
    allowed_watch_mode: true,
    can_move_robot: false,
    requires_operator_opt_in: false,
    required_gates: ["module_status", "run_status_awaiting_recovery"],
    semantic_invariants: ["same_protocol_run", "module_target_unchanged"],
  }),
  reconcile_state_first: Object.freeze({
    id: "reconcile_state_first",
    title: "Reconcile module-only state before resume",
    level: "L0",
    error_leaves: ["STATE_MISMATCH"],
    recovery_type: "state_reconcile",
    executor_tool: "execute_protocol_recovery",
    allowed_watch_mode: true,
    can_move_robot: false,
    requires_operator_opt_in: false,
    required_gates: ["reconcile_state", "module_blocker_only_diff"],
    semantic_invariants: ["deck_state_reconciled_before_motion"],
  }),
  suggest_new_destination_slot: Object.freeze({
    id: "suggest_new_destination_slot",
    title: "Human-reviewed destination slot replacement",
    level: "L3",
    error_leaves: ["DESTINATION_OCCUPIED"],
    recovery_type: "alternative_resource",
    resource_type: "deck_slot",
    executor_tool: "execute_protocol_recovery",
    allowed_watch_mode: false,
    can_move_robot: true,
    requires_operator_opt_in: true,
    required_gates: ["operator_confirmation", "destination_slot_supplied", "preflight_run_setup"],
    semantic_invariants: ["labware_identity_unchanged", "destination_slot_confirmed_by_operator"],
  }),
});

export function listRecoveryPlaybooks({ includeMotion = true } = {}) {
  return Object.values(PLAYBOOKS).filter(playbook => includeMotion || playbook.can_move_robot !== true);
}

export function getRecoveryPlaybook(id) {
  return PLAYBOOKS[String(id || "").trim()] || null;
}

export function requireRecoveryPlaybook(id) {
  const playbook = getRecoveryPlaybook(id);
  if (!playbook) {
    throw new Error(`Unknown recovery playbook: ${id || "missing"}.`);
  }
  return playbook;
}

export function summarizeRecoveryPlaybook(id) {
  const playbook = requireRecoveryPlaybook(id);
  return {
    id: playbook.id,
    title: playbook.title,
    level: playbook.level,
    recovery_type: playbook.recovery_type,
    resource_type: playbook.resource_type || null,
    executor_tool: playbook.executor_tool,
    live_executor_tool: playbook.live_executor_tool || null,
    allowed_watch_mode: playbook.allowed_watch_mode,
    can_move_robot: playbook.can_move_robot,
    requires_operator_opt_in: playbook.requires_operator_opt_in,
    required_gates: playbook.required_gates,
    semantic_invariants: playbook.semantic_invariants,
  };
}

export function buildPlaybookGateSummary(id, observed = {}) {
  const playbook = requireRecoveryPlaybook(id);
  const satisfied = [];
  const missing = [];
  const observedGates = new Set(Object.entries(observed)
    .filter(([, value]) => value === true)
    .map(([key]) => key));
  for (const gate of playbook.required_gates) {
    if (observedGates.has(gate)) {
      satisfied.push(gate);
    } else {
      missing.push(gate);
    }
  }
  return {
    playbook_id: playbook.id,
    status: missing.length === 0 ? "pass" : "blocked",
    satisfied_gates: satisfied,
    missing_gates: missing,
    can_move_robot: playbook.can_move_robot,
    requires_operator_opt_in: playbook.requires_operator_opt_in,
  };
}
