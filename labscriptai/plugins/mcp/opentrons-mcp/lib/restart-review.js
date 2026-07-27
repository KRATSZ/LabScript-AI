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

function resolveLatestResolutionPlan(logEntries = []) {
  const entry = logEntries.find(
    item => Array.isArray(item?.data?.resolution_plan) && item.data.resolution_plan.length > 0,
  );
  if (!entry) {
    return {
      plan: [],
      source: null,
    };
  }
  return {
    plan: entry.data.resolution_plan,
    source: {
      entry_id: entry.entry_id || null,
      tool_name: entry.tool_name || null,
      event_kind: entry.event_kind || null,
      status: entry.status || null,
      timestamp: entry.timestamp || null,
      operator_request_json_path: entry.data.operator_request_json_path || null,
      operator_request_md_path: entry.data.operator_request_md_path || null,
      output_path: entry.data.output_path || null,
    },
  };
}

function resolveLatestOperatorRequest(logEntries = []) {
  const entry = logEntries.find(
    item => item?.data?.operator_request && typeof item.data.operator_request === "object",
  );
  if (!entry) {
    return {
      request: null,
      source: null,
    };
  }
  return {
    request: entry.data.operator_request,
    source: {
      entry_id: entry.entry_id || null,
      tool_name: entry.tool_name || null,
      event_kind: entry.event_kind || null,
      status: entry.status || null,
      timestamp: entry.timestamp || null,
      operator_request_json_path: entry.data.operator_request_json_path || null,
      operator_request_md_path: entry.data.operator_request_md_path || null,
      output_path: entry.data.output_path || null,
    },
  };
}

function resolveLatestLiquidSourceSubstitutionRecovery(logEntries = []) {
  const entry = logEntries.find(
    item =>
      item?.event_kind === "liquid_source_substitution_recovery_bundle" &&
      item?.data &&
      typeof item.data === "object",
  );
  if (!entry) {
    return {
      recovery: null,
      source: null,
    };
  }
  return {
    recovery: {
      status: entry.status || null,
      playbook: entry.data.playbook || "liquid_source_substitution_continuation_protocol",
      output_path: entry.data.output_path || null,
      generated_protocol_path: entry.data.generated_protocol_path || null,
      failed_source_key: entry.data.failed_source_key || null,
      selected_source_key: entry.data.selected_source_key || null,
      fixed_script_prepared: entry.data.fixed_script_prepared === true,
      no_robot_motion: entry.data.no_robot_motion === true,
      no_aspirate_or_dispense: entry.data.no_aspirate_or_dispense === true,
      simulation_status: entry.data.simulation_status || null,
      simulation_issue_count: entry.data.simulation_issue_count ?? null,
      auto_resume_eligible: entry.data.auto_resume_eligible === true,
      live_execution_allowed: entry.data.live_execution_allowed === true,
      live_protocol_run_allowed: entry.data.live_protocol_run_allowed === true,
      semantic_invariant_status: entry.data.semantic_invariant_status || null,
      experiment_intent_violation_count: entry.data.experiment_intent_violation_count ?? null,
      semantic_gate_blocker_count: entry.data.semantic_gate_blocker_count ?? null,
      next_tool: entry.data.next_tool || null,
      blocked_reason: entry.data.blocked_reason || null,
      required_next_gates: entry.data.required_next_gates || [],
    },
    source: {
      entry_id: entry.entry_id || null,
      tool_name: entry.tool_name || null,
      event_kind: entry.event_kind || null,
      status: entry.status || null,
      timestamp: entry.timestamp || null,
      output_path: entry.data.output_path || null,
      generated_protocol_path: entry.data.generated_protocol_path || null,
    },
  };
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
  const latestResolution = resolveLatestResolutionPlan(logEntries);
  const latestOperatorRequest = resolveLatestOperatorRequest(logEntries);
  const latestLiquidSourceSubstitutionRecovery =
    resolveLatestLiquidSourceSubstitutionRecovery(logEntries);

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
      latest_resolution_plan: latestResolution.plan,
      latest_resolution_plan_source: latestResolution.source,
      latest_operator_request: latestOperatorRequest.request,
      latest_operator_request_source: latestOperatorRequest.source,
      latest_liquid_source_substitution_recovery: latestLiquidSourceSubstitutionRecovery.recovery,
      latest_liquid_source_substitution_recovery_source: latestLiquidSourceSubstitutionRecovery.source,
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

function firstOperatorRequestByType(operatorRequest = {}, requestType) {
  const requests = Array.isArray(operatorRequest?.requests) ? operatorRequest.requests : [];
  return requests.find(request => request?.request_type === requestType) || null;
}

function summarizeLiquidIdentityInputs(operatorRequest = {}) {
  const liquidRequest = firstOperatorRequestByType(operatorRequest, "liquid_identity");
  const inputs = Array.isArray(liquidRequest?.inputs_needed) ? liquidRequest.inputs_needed : [];
  const missingByField = {};
  for (const input of inputs) {
    for (const field of input?.missing_identity_fields || []) {
      missingByField[field] = (missingByField[field] || 0) + 1;
    }
  }
  return {
    count: inputs.length,
    keys: inputs.map(input => input.key || `${input.slot_name || "?"}.${input.well_name || "?"}`),
    missing_by_field: missingByField,
  };
}

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
  const latestResolutionPlan = Array.isArray(guidance.latest_resolution_plan)
    ? guidance.latest_resolution_plan
    : [];
  const latestOperatorRequest = guidance.latest_operator_request || null;
  const latestOperatorRequestSource = guidance.latest_operator_request_source || null;
  const latestLiquidSourceSubstitutionRecovery =
    guidance.latest_liquid_source_substitution_recovery || null;
  const latestLiquidSourceSubstitutionRecoverySource =
    guidance.latest_liquid_source_substitution_recovery_source || null;
  const latestOperatorRequestArtifacts = latestOperatorRequestSource
    ? {
        markdown_path: latestOperatorRequestSource.operator_request_md_path || null,
        json_path: latestOperatorRequestSource.operator_request_json_path || null,
        gate_output_path: latestOperatorRequestSource.output_path || null,
      }
    : null;
  const liquidIdentityInputsNeededSummary = summarizeLiquidIdentityInputs(latestOperatorRequest);
  const firstResolutionStep = latestResolutionPlan[0] || null;

  const recommended_next_tool = reconcileFirst
    ? "reconcile_state"
    : firstResolutionStep?.allowed_next_tools?.[0] || "robot_status";

  const rationale_short = reconcileFirst
    ? "Session needs_reconciliation: align committed deck state before autonomous physical motion."
    : firstResolutionStep
      ? `Follow latest resolution_plan step ${firstResolutionStep.order || 1}: ${firstResolutionStep.action}.`
    : "Poll live robot_status first; persisted logs are historical and not current deck truth.";
  const rationale_zh = reconcileFirst
    ? "会话标记为 needs_reconciliation：任何自动物理动作前，先同步真实 deck 状态。"
    : firstResolutionStep
      ? `先处理最新 resolution_plan 第 ${firstResolutionStep.order || 1} 步：${firstResolutionStep.action}。`
      : "先只读查询 robot_status；持久化日志只能当历史记录，不能当当前 deck 真相。";

  const operator_steps = [];
  const operator_steps_zh = [];
  let n = 1;
  let nz = 1;
  if (reconcileFirst) {
    operator_steps.push(
      `${n++}. Call reconcile_state for this session until the deck matches reality.`,
    );
    operator_steps_zh.push(`${nz++}. 先调用 reconcile_state，直到记录的 deck 状态和真实机器一致。`);
  }
  if (!reconcileFirst && firstResolutionStep) {
    operator_steps.push(
      `${n++}. Follow latest resolution_plan step ${firstResolutionStep.order || 1}: ${firstResolutionStep.action}.`,
    );
    operator_steps_zh.push(
      `${nz++}. 按最新 resolution_plan 第 ${firstResolutionStep.order || 1} 步处理：${firstResolutionStep.action}。`,
    );
    if (latestOperatorRequestArtifacts?.markdown_path) {
      operator_steps.push(
        `${n++}. Read operator request artifact: ${latestOperatorRequestArtifacts.markdown_path}.`,
      );
      operator_steps_zh.push(
        `${nz++}. 先看中文交接单：${latestOperatorRequestArtifacts.markdown_path}。`,
      );
    }
    if (firstResolutionStep.no_robot_motion === true) {
      operator_steps.push(`${n++}. Do not run robot motion for this step.`);
      operator_steps_zh.push(`${nz++}. 这一步禁止机器人运动；不要自动 home，也不要继续液体测试。`);
    }
    if (Array.isArray(firstResolutionStep.acceptance_criteria) && firstResolutionStep.acceptance_criteria.length > 0) {
      const criteria = firstResolutionStep.acceptance_criteria
        .map(item => String(item || "").trim().replace(/[.。]+$/u, ""))
        .filter(Boolean);
      operator_steps.push(
        `${n++}. Clear criteria: ${criteria.join(" | ")}.`,
      );
      operator_steps_zh.push(`${nz++}. 通过标准：${criteria.join(" | ")}。`);
    }
  }
  operator_steps.push(`${n++}. Call robot_status and module_status (pass robot_ip).`);
  operator_steps_zh.push(`${nz++}. 调用 robot_status 和 module_status，只读确认机器状态。`);
  if (liquidIdentityInputsNeededSummary.count > 0) {
    operator_steps_zh.push(
      `${nz++}. 液体身份还缺 ${liquidIdentityInputsNeededSummary.count} 个孔位：${liquidIdentityInputsNeededSummary.keys.join(", ")}。`,
    );
  }
  if (latestLiquidSourceSubstitutionRecovery?.fixed_script_prepared === true) {
    operator_steps.push(
      `${n++}. Liquid source-substitution recovery is prepared: ${latestLiquidSourceSubstitutionRecovery.failed_source_key || "unknown"} -> ${latestLiquidSourceSubstitutionRecovery.selected_source_key || "unknown"}; next gate is ${latestLiquidSourceSubstitutionRecovery.next_tool || "live_liquid_recovery_gate"}.`,
    );
    operator_steps_zh.push(
      `${nz++}. 液体换源固定恢复包已准备：${latestLiquidSourceSubstitutionRecovery.failed_source_key || "unknown"} -> ${latestLiquidSourceSubstitutionRecovery.selected_source_key || "unknown"}；下一步仍要过 ${latestLiquidSourceSubstitutionRecovery.next_tool || "live_liquid_recovery_gate"}。`,
    );
    if (
      latestLiquidSourceSubstitutionRecovery.auto_resume_eligible === false ||
      latestLiquidSourceSubstitutionRecovery.live_execution_allowed === false
    ) {
      operator_steps.push(`${n++}. Do not auto-resume this liquid recovery before live gate and operator opt-in.`);
      operator_steps_zh.push(`${nz++}. live gate 和人工 opt-in 前，不要自动续跑这条液体恢复。`);
    }
    if (latestLiquidSourceSubstitutionRecovery.experiment_intent_violation_count > 0) {
      operator_steps.push(`${n++}. Stop: semantic invariants failed for this recovery bundle.`);
      operator_steps_zh.push(`${nz++}. 停止：这条恢复包的实验语义不变量未通过，不能续跑。`);
    }
  }
  if (lastRunId) {
    operator_steps.push(
      `${n++}. last_run_id is set (${lastRunId}): use run_history then parse_error if that run still matters.`,
    );
    operator_steps_zh.push(
      `${nz++}. last_run_id=${lastRunId}；如果这个 run 仍相关，再查 run_history 和 parse_error。`,
    );
  }
  if (homeBlocked) {
    operator_steps.push(
      `${n++}. Do not home yet; live preview shows blockers: ${homeBlockers.join(", ") || "see home_safety_preview"}.`,
    );
    operator_steps_zh.push(
      `${nz++}. 现在不要 home；home_safety_preview 仍有阻塞：${homeBlockers.join(", ") || "见 home_safety_preview"}。`,
    );
    if (minimumCleanupActions.length > 0) {
      operator_steps.push(
        `${n++}. Minimum cleanup before home: ${minimumCleanupActions.join(", ")}.`,
      );
      operator_steps_zh.push(
        `${nz++}. home 前最少要先做这些清理：${minimumCleanupActions.join(", ")}。`,
      );
    }
  }
  operator_steps.push(
    `${n++}. Use experiment_history only for audit context, not as current deck truth.`,
  );
  operator_steps_zh.push(`${nz++}. experiment_history 只当审计记录，不当当前 deck 真相。`);
  operator_steps.push(
    `${n++}. Before home: is_home_safe (or use home_safety_preview when robot_ip was provided).`,
  );
  operator_steps_zh.push(`${nz++}. 任何 home 前，先跑 is_home_safe 或检查 home_safety_preview。`);

  const suggested = guidance.suggested_tool_order || [];
  const tool_sequence = suggested.map((tool, idx) => ({
    order: idx + 1,
    tool,
    hint: TOOL_HINTS[tool] || "See MCP tool description.",
  }));

  return {
    recommended_next_tool,
    rationale_short,
    rationale_zh,
    operator_steps,
    operator_steps_zh,
    tool_sequence,
    reconcile_first: reconcileFirst,
    home_action_required: homeBlocked,
    home_blockers: homeBlockers,
    minimum_cleanup_actions: minimumCleanupActions,
    latest_resolution_plan: latestResolutionPlan,
    latest_resolution_plan_source: guidance.latest_resolution_plan_source || null,
    latest_operator_request: latestOperatorRequest,
    latest_operator_request_source: latestOperatorRequestSource,
    latest_operator_request_artifacts: latestOperatorRequestArtifacts,
    latest_liquid_source_substitution_recovery: latestLiquidSourceSubstitutionRecovery,
    latest_liquid_source_substitution_recovery_source: latestLiquidSourceSubstitutionRecoverySource,
    liquid_identity_inputs_needed_summary: liquidIdentityInputsNeededSummary,
    note:
      "Atomic tools remain available; this block is a single-entry summary for operators after MCP/host restart.",
  };
}
