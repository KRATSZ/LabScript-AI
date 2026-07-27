import { randomUUID } from "crypto";

const DEFAULT_LEVELS = ["L1", "L2", "L3", "L4"];
const TERMINAL_SUCCESS = new Set(["succeeded", "completed"]);
const TERMINAL_ATTENTION = new Set(["failed", "stopped", "canceled", "cancelled", "awaiting-recovery", "blocked-by-open-door"]);
const HARD_BLOCKERS = new Set(["door_open", "estop_engaged", "instrument_not_ready"]);

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

function normalizeLevel(level) {
  const normalized = String(level || "").trim().toUpperCase();
  return DEFAULT_LEVELS.includes(normalized) ? normalized : null;
}

function requestedLevels(args = {}) {
  if (!Array.isArray(args.levels) || args.levels.length === 0) {
    return new Set(DEFAULT_LEVELS);
  }
  const levels = args.levels.map(normalizeLevel).filter(Boolean);
  return new Set(levels.length > 0 ? levels : DEFAULT_LEVELS);
}

function unwrapData(payload) {
  if (payload && typeof payload === "object" && "data" in payload) {
    return payload.data;
  }
  return payload;
}

function normalizeStatus(status) {
  return String(status || "").trim().toLowerCase();
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function buildNotification({
  level,
  type,
  severity = "info",
  message,
  messageZh = null,
  requiresAttention = false,
  recommendedNextTool = null,
  data = {},
} = {}) {
  return {
    notification_id: randomUUID(),
    created_at: new Date().toISOString(),
    level,
    type,
    severity,
    message,
    message_zh: messageZh || message,
    requires_attention: requiresAttention,
    recommended_next_tool: recommendedNextTool,
    data,
  };
}

async function safeCall(name, fn) {
  if (typeof fn !== "function") {
    return {
      name,
      ok: false,
      skipped: true,
      error: `${name} dependency is not configured.`,
    };
  }
  try {
    const value = await fn();
    return {
      name,
      ok: true,
      value,
    };
  } catch (error) {
    return {
      name,
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

function statusFromRobotCall(call) {
  if (!call) {
    return "skipped";
  }
  if (!call.ok) {
    return "unreachable";
  }
  const blockers = asArray(call.value?.data?.blockers);
  if (blockers.some(blocker => HARD_BLOCKERS.has(blocker))) {
    return "hard_stop";
  }
  if (blockers.length > 0) {
    return "needs_attention";
  }
  return "pass";
}

function statusFromModuleCall(call) {
  if (!call) {
    return "skipped";
  }
  if (!call.ok) {
    return "unreachable";
  }
  return asArray(call.value?.data?.blockers).length > 0 ? "needs_attention" : "pass";
}

function runStatusFromHistory(runHistoryResult) {
  const data = unwrapData(runHistoryResult) || {};
  return data.status || data.run_status || null;
}

function l1RobotApiUnavailable(l1 = null) {
  return asArray(l1?.checks).some(
    check =>
      ["robot_status", "module_status"].includes(check.name) &&
      check.status === "unreachable",
  );
}

function buildL1Heartbeat({ selfTestCall, healthCall, robotCall, moduleCall } = {}) {
  const checks = [
    {
      name: "runtime_recovery_self_test",
      status: selfTestCall?.ok && selfTestCall.value?.data?.status === "pass" ? "pass" : "fail",
      error: selfTestCall?.error || null,
      runtime_build: selfTestCall?.value?.data?.runtime_build || null,
    },
    healthCall
      ? {
          name: "health_check",
          status: healthCall.ok ? "pass" : "fail",
          error: healthCall.error || null,
          required_runtime_tools_all_present:
            healthCall.value?.data?.mcp_server?.required_runtime_tools?.all_present ?? null,
        }
      : null,
    robotCall
      ? {
          name: "robot_status",
          status: statusFromRobotCall(robotCall),
          error: robotCall.error || null,
          blockers: asArray(robotCall.value?.data?.blockers),
        }
      : null,
    moduleCall
      ? {
          name: "module_status",
          status: statusFromModuleCall(moduleCall),
          error: moduleCall.error || null,
          blockers: asArray(moduleCall.value?.data?.blockers),
        }
      : null,
  ].filter(Boolean);

  const status = checks.some(check => check.status === "hard_stop")
    ? "hard_stop"
    : checks.some(check => check.status === "fail" || check.status === "unreachable")
      ? "blocked"
      : checks.some(check => check.status === "needs_attention")
        ? "needs_attention"
        : "pass";

  const notifications = [];
  const selfTest = checks.find(check => check.name === "runtime_recovery_self_test");
  if (selfTest?.status !== "pass") {
    notifications.push(
      buildNotification({
        level: "L1",
        type: "runtime_self_test_failed",
        severity: "blocker",
        message: "Loaded recovery runtime self-test failed.",
        messageZh: "当前加载的恢复运行时自检失败，不能信任自动恢复。",
        requiresAttention: true,
        recommendedNextTool: "health_check",
        data: selfTest,
      }),
    );
  }

  const robot = checks.find(check => check.name === "robot_status");
  if (robot?.status === "unreachable") {
    notifications.push(
      buildNotification({
        level: "L1",
        type: "robot_unreachable",
        severity: "warn",
        message: "Robot API is unreachable; no live action was attempted.",
        messageZh: "机器人 API 当前不可达；监控没有尝试任何真机动作。",
        requiresAttention: true,
        recommendedNextTool: "robot_status",
        data: robot,
      }),
    );
  } else if (robot?.status === "hard_stop") {
    notifications.push(
      buildNotification({
        level: "L1",
        type: "robot_hard_stop",
        severity: "hard_stop",
        message: "Robot reports a hard blocker.",
        messageZh: "机器人状态里有硬阻塞，需要现场处理。",
        requiresAttention: true,
        recommendedNextTool: "robot_status",
        data: robot,
      }),
    );
  } else if (robot?.status === "needs_attention") {
    notifications.push(
      buildNotification({
        level: "L1",
        type: "robot_blocker",
        severity: "warn",
        message: "Robot status has blockers.",
        messageZh: "机器人状态有阻塞项，继续前需要处理。",
        requiresAttention: true,
        recommendedNextTool: "robot_status",
        data: robot,
      }),
    );
  }

  const modules = checks.find(check => check.name === "module_status");
  if (modules?.status === "needs_attention") {
    notifications.push(
      buildNotification({
        level: "L1",
        type: "module_not_ready",
        severity: "warn",
        message: "One or more modules are not ready.",
        messageZh: "有模块还没准备好，运行前需要等待或确认。",
        requiresAttention: true,
        recommendedNextTool: "module_status",
        data: modules,
      }),
    );
  }

  return {
    status,
    checks,
    notifications,
    no_robot_motion: true,
  };
}

function buildL2RunWatch({
  args,
  runHistoryCall,
  guidanceCall,
  watchCall,
} = {}) {
  if (!args.run_id) {
    return {
      status: "skipped",
      reason: "run_id_not_provided",
      notifications: [],
      no_robot_motion: true,
    };
  }

  if (args.self_fix_mode === "l0") {
    const gateBlockers = [];
    if (args.allow_l4_execution !== true) {
      gateBlockers.push("allow_l4_execution_false");
    }
    if (args.operator_opt_in !== true) {
      gateBlockers.push("operator_opt_in_required");
    }
    if (gateBlockers.length > 0) {
      return {
        status: "blocked",
        mode: "l0_self_fix_blocked_before_watch",
        watch_result: null,
        blockers: gateBlockers,
        notifications: [
          buildNotification({
            level: "L2",
            type: "l0_self_fix_gate_blocked",
            severity: "warn",
            message: "L0 self-fix was not delegated because execution gates are not open.",
            messageZh: "L0 自修 gate 没打开，因此没有调用 runtime_watch_poll 执行动作。",
            requiresAttention: true,
            recommendedNextTool: "safe_next_action",
            data: { blockers: gateBlockers },
          }),
        ],
        no_robot_motion: true,
      };
    }
    const watchData = watchCall?.value?.data || {};
    const status = !watchCall?.ok ? "unreachable" : watchData.status || watchCall.value?.status || "running";
    const notifications = [];
    if (!watchCall?.ok) {
      notifications.push(
        buildNotification({
          level: "L2",
          type: "run_watch_unreachable",
          severity: "warn",
          message: "Runtime watch could not read the run.",
          messageZh: "运行监控无法读取当前 run。",
          requiresAttention: true,
          recommendedNextTool: "runtime_watch_poll",
          data: { error: watchCall?.error || null },
        }),
      );
    } else if (watchData.last_event === "auto_fixed") {
      notifications.push(
        buildNotification({
          level: "L2",
          type: "l0_auto_fixed",
          severity: "info",
          message: "Runtime watch applied an allowed L0 self-fix.",
          messageZh: "监控已执行一个允许的 L0 小修复，并继续观察。",
          requiresAttention: false,
          recommendedNextTool: "runtime_watch_poll",
          data: watchData,
        }),
      );
    } else if (["needs_user", "hard_stop", "unreachable"].includes(status)) {
      notifications.push(
        buildNotification({
          level: "L2",
          type: `run_${status}`,
          severity: status === "hard_stop" ? "hard_stop" : "warn",
          message: `Runtime watch returned ${status}.`,
          messageZh: `运行监控返回 ${status}，需要处理后再继续。`,
          requiresAttention: true,
          recommendedNextTool: "runtime_get_alerts",
          data: watchData,
        }),
      );
    }

    return {
      status,
      mode: "l0_self_fix",
      watch_result: watchData,
      notifications,
      no_robot_motion: watchData.last_event !== "auto_fixed",
    };
  }

  if (!runHistoryCall?.ok) {
    return {
      status: "unreachable",
      mode: "observe",
      error: runHistoryCall?.error || null,
      notifications: [
        buildNotification({
          level: "L2",
          type: "run_history_unreachable",
          severity: "warn",
          message: "Run history could not be read.",
          messageZh: "无法读取 run 历史；没有执行自修。",
          requiresAttention: true,
          recommendedNextTool: "run_history",
          data: { error: runHistoryCall?.error || null },
        }),
      ],
      no_robot_motion: true,
    };
  }

  const runStatus = runStatusFromHistory(runHistoryCall.value);
  const normalizedRunStatus = normalizeStatus(runStatus);
  const status = TERMINAL_SUCCESS.has(normalizedRunStatus)
    ? "completed"
    : TERMINAL_ATTENTION.has(normalizedRunStatus)
      ? "needs_attention"
      : "running";
  const notifications = [];

  if (status === "completed") {
    notifications.push(
      buildNotification({
        level: "L2",
        type: "run_completed",
        severity: "info",
        message: "Run reached a successful terminal state.",
        messageZh: "run 已成功结束。",
        requiresAttention: false,
        recommendedNextTool: "experiment_history",
        data: { run_status: runStatus },
      }),
    );
  } else if (status === "needs_attention") {
    const guidance = guidanceCall?.ok ? guidanceCall.value : null;
    notifications.push(
      buildNotification({
        level: "L2",
        type: "run_needs_attention",
        severity: normalizedRunStatus === "awaiting-recovery" ? "warn" : "blocker",
        message: `Run status is ${runStatus}; recovery guidance is available.`,
        messageZh: `run 状态是 ${runStatus}；需要按恢复建议处理。`,
        requiresAttention: true,
        recommendedNextTool: guidance ? "safe_next_action" : "parse_error",
        data: {
          run_status: runStatus,
          parsed_error: guidance?.parsedError || null,
          recovery: guidance?.recovery || null,
          guidance_error: guidanceCall?.error || null,
        },
      }),
    );
  }

  return {
    status,
    mode: "observe",
    run_status: runStatus,
    run_history: runHistoryCall.value?.data || null,
    guidance: guidanceCall?.ok ? guidanceCall.value : null,
    notifications,
    no_robot_motion: true,
  };
}

function buildL3RecoveryCoordinator({ args, safeNextCall, liquidGateCall } = {}) {
  const safeNext = safeNextCall?.value?.data?.safe_next_action || null;
  const liquidGate = liquidGateCall?.value?.data || null;
  const latestRecovery = safeNext?.latest_liquid_source_substitution_recovery || null;
  const notifications = [];

  if (!safeNextCall?.ok) {
    notifications.push(
      buildNotification({
        level: "L3",
        type: "safe_next_unavailable",
        severity: "warn",
        message: "safe_next_action could not be built.",
        messageZh: "无法生成 safe_next_action，恢复下一步不可靠。",
        requiresAttention: true,
        recommendedNextTool: "safe_next_action",
        data: { error: safeNextCall?.error || null },
      }),
    );
  }

  if (liquidGateCall) {
    if (!liquidGateCall.ok) {
      notifications.push(
        buildNotification({
          level: "L3",
          type: "liquid_gate_unavailable",
          severity: "warn",
          message: "Live liquid recovery gate could not be evaluated.",
          messageZh: "无法评估液体恢复 gate；不能继续液体相关真机动作。",
          requiresAttention: true,
          recommendedNextTool: "live_liquid_recovery_gate",
          data: { error: liquidGateCall.error || null },
        }),
      );
    } else if (liquidGate?.ok_for_live_liquid_rerun !== true) {
      notifications.push(
        buildNotification({
          level: "L3",
          type: "liquid_gate_blocked",
          severity: liquidGate?.status === "blocked" ? "blocker" : "warn",
          message: "Live liquid recovery gate did not pass.",
          messageZh: "液体恢复 gate 没通过，不能继续液体真机动作。",
          requiresAttention: true,
          recommendedNextTool: liquidGate?.allowed_next_tools?.[0] || "live_liquid_recovery_gate",
          data: liquidGate,
        }),
      );
    }
  }

  if (latestRecovery?.fixed_script_prepared === true) {
    const liveAllowed =
      latestRecovery.live_execution_allowed === true &&
      latestRecovery.live_protocol_run_allowed === true;
    notifications.push(
      buildNotification({
        level: "L3",
        type: "recovery_bundle_prepared",
        severity: liveAllowed ? "info" : "warn",
        message: "A fixed recovery bundle is prepared.",
        messageZh: `固定恢复包已准备：${latestRecovery.failed_source_key || "unknown"} -> ${latestRecovery.selected_source_key || "unknown"}。`,
        requiresAttention: !liveAllowed,
        recommendedNextTool: latestRecovery.next_tool || "live_liquid_recovery_gate",
        data: latestRecovery,
      }),
    );
  }

  const status = notifications.some(item => item.severity === "blocker")
    ? "blocked"
    : notifications.some(item => item.requires_attention)
      ? "needs_attention"
      : liquidGate?.ok_for_live_liquid_rerun === true
        ? "pass"
        : safeNextCall?.ok
          ? "pass"
          : "blocked";

  return {
    status,
    safe_next_action: safeNext,
    liquid_gate: liquidGate,
    latest_recovery_bundle: latestRecovery,
    notifications,
    no_robot_motion: true,
    requested_source_plan: args.source_plan || null,
  };
}

function buildL4GuardedExecution({ args, l1, l2, l3 } = {}) {
  const blockers = [];
  const latestRecovery = l3?.latest_recovery_bundle || null;
  const liquidGate = l3?.liquid_gate || null;
  const l2DidExecute = l2?.mode === "l0_self_fix" && l2?.watch_result?.last_event === "auto_fixed";

  if (args.self_fix_mode !== "l0") {
    blockers.push("self_fix_mode_is_observe");
  }
  if (args.allow_l4_execution !== true) {
    blockers.push("allow_l4_execution_false");
  }
  if (args.operator_opt_in !== true) {
    blockers.push("operator_opt_in_required");
  }
  if (l1?.status === "hard_stop") {
    blockers.push("l1_hard_stop");
  }
  if (l1?.status === "blocked") {
    blockers.push("l1_blocked");
  }
  if (liquidGate && liquidGate.ok_for_live_liquid_rerun !== true) {
    blockers.push("live_liquid_recovery_gate_not_passed");
  }
  if (
    latestRecovery?.fixed_script_prepared === true &&
    (latestRecovery.live_execution_allowed !== true ||
      latestRecovery.live_protocol_run_allowed !== true)
  ) {
    blockers.push("prepared_liquid_recovery_still_requires_live_gate_and_operator_opt_in");
  }

  const status = l2DidExecute
    ? "executed_l0_self_fix"
    : blockers.length > 0
      ? "blocked"
      : "ready_for_l0_self_fix";

  const notification = status === "executed_l0_self_fix"
    ? buildNotification({
        level: "L4",
        type: "guarded_l0_execution_applied",
        severity: "info",
        message: "Guarded execution path applied an allowed L0 self-fix.",
        messageZh: "受控执行层已经通过 runtime_watch_poll 执行了允许的 L0 小修。",
        requiresAttention: false,
        recommendedNextTool: "runtime_watch_poll",
        data: { watch_result: l2?.watch_result || null },
      })
    : buildNotification({
        level: "L4",
        type: status === "ready_for_l0_self_fix" ? "guarded_execution_ready" : "guarded_execution_blocked",
        severity: status === "ready_for_l0_self_fix" ? "info" : "warn",
        message:
          status === "ready_for_l0_self_fix"
            ? "Guarded L0 self-fix mode is ready."
            : "Guarded execution is blocked by policy or current state.",
        messageZh:
          status === "ready_for_l0_self_fix"
            ? "受控 L0 自修模式已满足条件，可以由 runtime_watch_poll 处理白名单小故障。"
            : "受控执行被策略或当前状态阻止，没有执行真机动作。",
        requiresAttention: status !== "ready_for_l0_self_fix",
        recommendedNextTool:
          blockers.includes("operator_opt_in_required")
            ? "safe_next_action"
            : blockers.includes("live_liquid_recovery_gate_not_passed")
              ? "live_liquid_recovery_gate"
              : "runtime_watch_poll",
        data: { blockers },
      });

  return {
    status,
    blockers,
    l4_action: "runtime_watch_l0_only",
    executed: l2DidExecute,
    notification,
    no_robot_motion: !l2DidExecute,
    safety_boundary:
      "L4 delegates only whitelisted L0 fixes to runtime_watch_poll. Liquid/source changes still require live gate and operator opt-in before any robot motion.",
  };
}

function combineOverallStatus(levels = {}) {
  const levelValues = Object.values(levels).filter(Boolean);
  if (levelValues.some(level => level.status === "hard_stop")) {
    return "hard_stop";
  }
  if (levelValues.some(level => level.status === "blocked" || level.status === "unreachable")) {
    return "blocked";
  }
  if (levelValues.some(level => level.status === "needs_attention")) {
    return "needs_attention";
  }
  if (levelValues.some(level => level.status === "executed_l0_self_fix")) {
    return "self_fixed";
  }
  if (levelValues.some(level => level.status === "running")) {
    return "running";
  }
  return "ok";
}

function checkAcceptance(name, passed, detail = {}) {
  return {
    name,
    status: passed ? "pass" : "fail",
    ...detail,
  };
}

function buildMonitorAcceptance({ args, levels, notifications, status } = {}) {
  const l1 = levels.L1 || null;
  const l2 = levels.L2 || null;
  const l3 = levels.L3 || null;
  const l4 = levels.L4 || null;
  const latestRecovery = l3?.latest_recovery_bundle || null;
  const l0AutoFixApplied =
    l2?.mode === "l0_self_fix" && l2?.watch_result?.last_event === "auto_fixed";
  const l0ExecutionAuthorized =
    args.self_fix_mode === "l0" &&
    args.allow_l4_execution === true &&
    args.operator_opt_in === true;
  const unapprovedMotionCount = l0AutoFixApplied && !l0ExecutionAuthorized ? 1 : 0;
  const intentViolationCount =
    Number(latestRecovery?.experiment_intent_violation_count || 0);
  const hardStopCount = notifications.filter(item => item.severity === "hard_stop").length;
  const humanGateCount = notifications.filter(item => item.requires_attention).length;
  const liquidGateBlockerCount =
    Number(latestRecovery?.semantic_gate_blocker_count || 0);

  const checks = [
    checkAcceptance("runtime_self_test_passed", !l1 || l1.checks?.find(check => check.name === "runtime_recovery_self_test")?.status === "pass", {
      level: "L1",
    }),
    checkAcceptance("observe_mode_no_robot_motion", args.self_fix_mode !== "observe" || l2?.no_robot_motion !== false, {
      level: "L2",
    }),
    checkAcceptance("l0_self_fix_requires_explicit_gates", args.self_fix_mode !== "l0" || l0ExecutionAuthorized || l2?.mode === "l0_self_fix_blocked_before_watch", {
      level: "L2",
      blockers: l2?.blockers || [],
    }),
    checkAcceptance("no_unapproved_robot_motion", unapprovedMotionCount === 0, {
      level: "L4",
      unapproved_motion_count: unapprovedMotionCount,
    }),
    checkAcceptance("liquid_recovery_does_not_bypass_gate", !latestRecovery || latestRecovery.live_execution_allowed !== true, {
      level: "L3",
      latest_recovery_bundle: latestRecovery
        ? {
            failed_source_key: latestRecovery.failed_source_key || null,
            selected_source_key: latestRecovery.selected_source_key || null,
            next_tool: latestRecovery.next_tool || null,
          }
        : null,
    }),
    checkAcceptance("experiment_intent_violation_count_zero", intentViolationCount === 0, {
      level: "L3",
      experiment_intent_violation_count: intentViolationCount,
    }),
  ];
  const failedChecks = checks.filter(check => check.status !== "pass");

  return {
    status: failedChecks.length > 0
      ? "failed"
      : humanGateCount > 0 || ["blocked", "needs_attention", "hard_stop"].includes(status)
        ? "needs_attention"
        : "pass",
    checks,
    failed_checks: failedChecks.map(check => check.name),
    metrics: {
      monitor_tick_count: 1,
      l0_auto_fix_count: l0AutoFixApplied ? 1 : 0,
      human_gate_count: humanGateCount,
      hard_stop_count: hardStopCount,
      unapproved_motion_count: unapprovedMotionCount,
      experiment_intent_violation_count: intentViolationCount,
      liquid_recovery_gate_blocker_count: liquidGateBlockerCount,
      notification_count: notifications.length,
    },
    l4_execution: l4
      ? {
          status: l4.status,
          executed: l4.executed === true,
          blockers: l4.blockers || [],
        }
      : null,
  };
}

export async function runRuntimeRecoveryMonitor(args = {}, dependencies = {}) {
  const levelsWanted = requestedLevels(args);
  const sessionId = args.session_id || args.run_id || "default";
  const selfFixMode = args.self_fix_mode === "l0" ? "l0" : "observe";
  const monitorArgs = {
    ...args,
    session_id: sessionId,
    self_fix_mode: selfFixMode,
  };
  const levels = {};

  const notifications = [];
  let selfTestCall = null;
  let healthCall = null;
  let robotCall = null;
  let moduleCall = null;
  let safeNextCall = null;
  let liquidGateCall = null;

  if (levelsWanted.has("L1")) {
    selfTestCall = await safeCall("runtime_recovery_self_test", () =>
      dependencies.runtimeRecoverySelfTest({}),
    );
    healthCall = await safeCall("health_check", () =>
      dependencies.healthCheck({
        ...(monitorArgs.robot_ip ? { robot_ip: monitorArgs.robot_ip } : {}),
        ...(monitorArgs.python_executable ? { python_executable: monitorArgs.python_executable } : {}),
      }),
    );
    if (monitorArgs.robot_ip) {
      robotCall = await safeCall("robot_status", () =>
        dependencies.readRobotStatus({ robot_ip: monitorArgs.robot_ip }),
      );
      moduleCall = await safeCall("module_status", () =>
        dependencies.readModuleStatus({ robot_ip: monitorArgs.robot_ip }),
      );
    }
    levels.L1 = buildL1Heartbeat({ selfTestCall, healthCall, robotCall, moduleCall });
    notifications.push(...levels.L1.notifications);
  }

  if (levelsWanted.has("L2")) {
    let runHistoryCall = null;
    let guidanceCall = null;
    let watchCall = null;
    if (monitorArgs.run_id && monitorArgs.robot_ip) {
      if (selfFixMode === "l0") {
        if (monitorArgs.allow_l4_execution === true && monitorArgs.operator_opt_in === true) {
          watchCall = await safeCall("runtime_watch_poll", () =>
            dependencies.runtimeWatchPoll({
              ...monitorArgs,
              max_block_ms: monitorArgs.max_block_ms ?? 0,
              poll_interval_ms: monitorArgs.poll_interval_ms ?? 250,
            }),
          );
        }
      } else {
        runHistoryCall = await safeCall("run_history", () =>
          dependencies.readRunHistory({
            robot_ip: monitorArgs.robot_ip,
            run_id: monitorArgs.run_id,
            page_length: monitorArgs.page_length ?? 20,
          }),
        );
        const runStatus = normalizeStatus(runStatusFromHistory(runHistoryCall?.value));
        if (runHistoryCall.ok && TERMINAL_ATTENTION.has(runStatus)) {
          guidanceCall = await safeCall("runtime_failure_guidance", () =>
            dependencies.readRunFailureGuidance(
              monitorArgs,
              monitorArgs.run_id,
              monitorArgs.session_id,
            ),
          );
        }
      }
    }
    levels.L2 = buildL2RunWatch({
      args: monitorArgs,
      runHistoryCall,
      guidanceCall,
      watchCall,
    });
    notifications.push(...levels.L2.notifications);
  }

  if (levelsWanted.has("L3")) {
    const robotApiUnavailable = l1RobotApiUnavailable(levels.L1);
    safeNextCall = await safeCall("safe_next_action", () =>
      dependencies.safeNextAction({
        session_id: monitorArgs.session_id,
        limit: monitorArgs.limit ?? 10,
        ...(monitorArgs.robot_ip && !robotApiUnavailable ? { robot_ip: monitorArgs.robot_ip } : {}),
      }),
    );
    const shouldRunLiquidGate =
      monitorArgs.enable_liquid_gate === true ||
      Boolean(monitorArgs.source_plan) ||
      asArray(monitorArgs.required_sources).length > 0;
    if (shouldRunLiquidGate && monitorArgs.robot_ip && !robotApiUnavailable) {
      liquidGateCall = await safeCall("live_liquid_recovery_gate", () =>
        dependencies.liveLiquidRecoveryGate({
          robot_ip: monitorArgs.robot_ip,
          session_id: monitorArgs.session_id,
          ...(monitorArgs.source_plan ? { source_plan: monitorArgs.source_plan } : {}),
          ...(asArray(monitorArgs.required_sources).length > 0
            ? { required_sources: monitorArgs.required_sources }
            : {}),
          allow_observed_mismatch_reprobe:
            monitorArgs.allow_observed_mismatch_reprobe === true,
        }),
      );
    }
    levels.L3 = buildL3RecoveryCoordinator({
      args: monitorArgs,
      safeNextCall,
      liquidGateCall,
    });
    notifications.push(...levels.L3.notifications);
  }

  if (levelsWanted.has("L4")) {
    levels.L4 = buildL4GuardedExecution({
      args: monitorArgs,
      l1: levels.L1,
      l2: levels.L2,
      l3: levels.L3,
    });
    notifications.push(levels.L4.notification);
  }

  const attentionNotifications = notifications.filter(item => item.requires_attention);
  const status = combineOverallStatus(levels);
  const acceptance = buildMonitorAcceptance({
    args: monitorArgs,
    levels,
    notifications,
    status,
  });
  return {
    status,
    monitor_id: randomUUID(),
    timestamp: new Date().toISOString(),
    session_id: sessionId,
    run_id: monitorArgs.run_id || null,
    robot_ip: monitorArgs.robot_ip || null,
    self_fix_mode: selfFixMode,
    allow_l4_execution: monitorArgs.allow_l4_execution === true,
    operator_opt_in: monitorArgs.operator_opt_in === true,
    no_robot_motion:
      selfFixMode !== "l0" ||
      levels.L4?.executed !== true,
    levels,
    notifications,
    acceptance,
    requires_attention: attentionNotifications.length > 0,
    attention_count: attentionNotifications.length,
    recommended_next_tools: uniqueOrdered(
      notifications
        .filter(item => item.requires_attention || item.severity === "hard_stop")
        .map(item => item.recommended_next_tool),
    ),
    summary_zh:
      attentionNotifications.length > 0
        ? `主动监控发现 ${attentionNotifications.length} 个需要处理的状态。`
        : status === "self_fixed"
          ? "主动监控已完成一个允许的 L0 自修，并继续保持可追踪状态。"
          : "主动监控未发现需要立刻处理的阻塞。",
  };
}
