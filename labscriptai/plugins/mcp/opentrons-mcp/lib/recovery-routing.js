const DASHBOARD_LEAVES = new Set([
  "DOOR_OPEN",
  "ESTOP_ENGAGED",
  "MODULE_NOT_READY",
  "INSTRUMENT_NOT_READY",
  "ROBOT_UNREACHABLE",
]);

// Observation-only vision channel. Hard-stops and slot-confirm leaves stay out.
const VISION_LEAVES = new Set([
  "LABWARE_MISMATCH",
  "DESTINATION_UNAVAILABLE",
  "SLOT_NOT_ADDRESSABLE",
]);

// State sync: reconcile first — not camera/VLM-first.
const RECONCILE_LEAVES = new Set(["SESSION_NEEDS_RECONCILIATION", "STATE_MISMATCH"]);

// Hard-stop collision: manual only (do not route as vision).
const HARD_STOP_MANUAL_LEAVES = new Set(["DECK_COLLISION"]);

// Human slot confirmation: no camera as primary path.
const SLOT_CONFIRM_LEAVES = new Set(["DESTINATION_OCCUPIED"]);

const PROBE_LEAVES = new Set([
  "INSUFFICIENT_VOLUME",
  "AIR_BUBBLE",
  "LIQUID_PROPERTY_ERROR",
  "TIP_CLOG",
]);

const TIP_LEAVES = new Set(["TIP_PHYSICALLY_MISSING"]);

const CHANNEL_TOOLS = Object.freeze({
  dashboard: [
    "robot_status",
    "module_status",
    "live_readiness_check",
    "safe_next_action",
    "is_home_safe",
  ],
  vision: [
    "camera_status",
    "capture_preview_image",
    "deck_vision_check",
    "vision_check",
    "analyze_image_with_ark",
    "reconcile_state",
  ],
  reconcile: ["reconcile_state", "robot_status", "get_slot_occupation", "safe_next_action"],
  probe: [
    "recover_liquid_source_substitution",
    "list_critical_probe_targets",
    "probe_wells",
    "apply_liquid_probe_results",
    "get_liquid_source_map",
  ],
  tip: ["recover_tip_pickup", "suggest_next_tip_well", "list_tip_candidates"],
  // live_readiness_check included so DECK_COLLISION / hard-stop operator_steps
  // ("re-run live_readiness_check") match recommended_next_tools.
  manual: ["safe_next_action", "parse_error", "experiment_history", "live_readiness_check"],
  slot_confirm: [
    "suggest_recovery_action",
    "get_slot_occupation",
    "safe_next_action",
    "parse_error",
  ],
});

export function resolveRecoveryChannel(errorLeaf = null) {
  const leaf = String(errorLeaf || "UNKNOWN_NEEDS_HUMAN").trim().toUpperCase();
  if (DASHBOARD_LEAVES.has(leaf)) {
    return "dashboard";
  }
  if (RECONCILE_LEAVES.has(leaf)) {
    return "reconcile";
  }
  if (HARD_STOP_MANUAL_LEAVES.has(leaf) || SLOT_CONFIRM_LEAVES.has(leaf)) {
    return HARD_STOP_MANUAL_LEAVES.has(leaf) ? "manual" : "slot_confirm";
  }
  if (VISION_LEAVES.has(leaf)) {
    return "vision";
  }
  if (PROBE_LEAVES.has(leaf)) {
    return "probe";
  }
  if (TIP_LEAVES.has(leaf)) {
    return "tip";
  }
  return "manual";
}

export function buildRecoveryRoutingGuidance({
  errorLeaf = null,
  recoverySuggestion = null,
} = {}) {
  const leaf = String(
    errorLeaf ||
      recoverySuggestion?.error_leaf ||
      recoverySuggestion?.error_category ||
      "UNKNOWN_NEEDS_HUMAN",
  )
    .trim()
    .toUpperCase();
  const channel = resolveRecoveryChannel(leaf);
  const recommendedNextTools = [...(CHANNEL_TOOLS[channel] || CHANNEL_TOOLS.manual)];

  const guidance = {
    recovery_channel: channel,
    recovery_channel_label:
      channel === "dashboard"
        ? "仪表盘"
        : channel === "vision"
          ? "眼睛"
          : channel === "reconcile"
            ? "状态对齐"
            : channel === "probe"
              ? "手指"
              : channel === "tip"
                ? "手指(tip)"
                : channel === "slot_confirm"
                  ? "人工换槽"
                  : "人工",
    recommended_next_tools: recommendedNextTools,
    channel_rationale:
      channel === "dashboard"
        ? "门/急停/模块/锁状态先用 HTTP 仪表盘确认，不用相机。"
        : channel === "vision"
          ? "台面移位或 labware 不一致时拍照 + YOLO/VLM 第二意见，再 reconcile。"
          : channel === "reconcile"
            ? "会话/状态不一致时先 reconcile_state，不要先开相机或 VLM。"
            : channel === "probe"
              ? "液体空/气泡等问题用 targeted probe_wells，不用 VLM。"
              : channel === "tip"
                ? "缺 tip 走 tip 恢复分支。"
                : channel === "slot_confirm"
                  ? "目标槽位占用：人工确认替代槽位；不以相机为主要路径。"
                  : leaf === "DECK_COLLISION"
                    ? "硬停碰撞：禁止 vision 自动恢复；人工检查后重新 live_readiness_check。"
                    : "无安全自动分支，停止并人工判断。",
  };

  if (recoverySuggestion?.hard_stop || leaf === "DECK_COLLISION") {
    guidance.resume_allowed = false;
    guidance.operator_steps = [
      "停止自动恢复。",
      "按 recovery_channel 完成物理检查。",
      "重新走 live_readiness_check 后再决定是否 resume。",
    ];
  }

  return guidance;
}

export function enrichRecoverySuggestion(recoverySuggestion = {}) {
  const routing = buildRecoveryRoutingGuidance({ recoverySuggestion });
  const recommendedNextTools = [...(routing.recommended_next_tools || [])];
  if (
    recoverySuggestion?.same_liquid_source_substitution_allowed === true &&
    recoverySuggestion?.same_liquid_source_substitution_next_tool
  ) {
    const nextTool = recoverySuggestion.same_liquid_source_substitution_next_tool;
    if (!recommendedNextTools.includes(nextTool)) {
      recommendedNextTools.unshift(nextTool);
    }
    for (const gateTool of recoverySuggestion.same_liquid_source_substitution_required_gates || []) {
      if (gateTool && !recommendedNextTools.includes(gateTool)) {
        recommendedNextTools.push(gateTool);
      }
    }
  }
  return {
    ...recoverySuggestion,
    ...routing,
    recommended_next_tools: recommendedNextTools,
    default_next_step: recommendedNextTools[0] || routing.recommended_next_tools[0] || "safe_next_action",
  };
}
