import fs from "fs";
import { randomUUID } from "crypto";

import { watchFilePath } from "./alert-store.js";
import { runtimeWatchPoll } from "./sentry-step.js";
import { deliverRuntimeOutbox } from "../runtime-outbox.js";
import {
  appendWatchLoopOutboxEntry,
  shouldWakeOnTick,
  tickOutboxKind,
} from "./outbox-tick.js";

const DEFAULT_MAX_TURNS = 20;
const DEFAULT_MAX_RUNTIME_MS = 10 * 60 * 1000;
const DEFAULT_INTERVAL_MS = 5000;
const DEFAULT_POLL_BLOCK_MS = 30 * 1000;
const MIN_INTERVAL_MS = 250;
const MAX_INTERVAL_MS = 60 * 1000;

const TERMINAL_STATUSES = new Set(["completed", "hard_stop", "unreachable", "needs_user"]);

function sleep(ms, deps) {
  if (typeof deps?.sleep === "function") {
    return deps.sleep(ms);
  }
  return new Promise(resolve => setTimeout(resolve, ms));
}

function goalStatePath(runId, { watchDir = null } = {}) {
  return watchFilePath(runId, "goal-state.json", { watchDir });
}

function readGoalState(runId, { watchDir = null } = {}) {
  const filePath = goalStatePath(runId, { watchDir });
  if (!fs.existsSync(filePath)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function writeGoalState(runId, goalState, { watchDir = null } = {}) {
  const filePath = goalStatePath(runId, { watchDir });
  fs.mkdirSync(filePath.replace(/\/[^/]+$/, ""), { recursive: true });
  const tempPath = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  fs.writeFileSync(tempPath, `${JSON.stringify(goalState, null, 2)}\n`);
  fs.renameSync(tempPath, filePath);
}

function clampInt(value, fallback, min, max) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return fallback;
  }
  return Math.max(min, Math.min(max, Math.trunc(number)));
}

function goalStatusFromTick(status, verified) {
  if (verified) {
    return "complete";
  }
  if (status === "completed") {
    return "complete";
  }
  if (status === "running") {
    return "continue";
  }
  return "blocked";
}

function recommendedNextTool(status, tickData = {}) {
  if (tickData.recommended_next_tool) {
    return tickData.recommended_next_tool;
  }
  if (status === "completed") {
    return "experiment_history";
  }
  if (status === "needs_user" || status === "hard_stop") {
    return "runtime_get_alerts";
  }
  if (status === "unreachable") {
    return "robot_status";
  }
  return "runtime_watch_poll";
}

function severityForStatus(status) {
  if (status === "hard_stop") {
    return "hard_stop";
  }
  if (status === "needs_user" || status === "unreachable") {
    return "warn";
  }
  return "info";
}

function levelForStatus(status) {
  if (status === "hard_stop") {
    return "L4";
  }
  if (status === "needs_user" || status === "unreachable") {
    return "L3";
  }
  if (status === "completed") {
    return "L2";
  }
  return "L2";
}

function buildHeartbeatEvent({ goal, turn, goalStatus }) {
  const ts = new Date().toISOString();
  return {
    kind: "heartbeat",
    wake: false,
    session_id: goal.session_id,
    run_id: goal.run_id,
    source: "runtime_watch_loop",
    level: "L2",
    type: "runtime_watch_loop_heartbeat",
    severity: "info",
    status: "running",
    title: `runtime_watch_loop turn ${turn}: heartbeat`,
    message: `Goal ${goal.goal_id} turn ${turn} heartbeat; no_error=true.`,
    message_zh: `目标 ${goal.goal_id} 第 ${turn} 轮心跳；no_error=true。`,
    requires_attention: false,
    requires_ack: false,
    recommended_next_tool: "runtime_watch_poll",
    no_robot_motion: true,
    dedupe_key: `${goal.goal_id}:heartbeat:${turn}`,
    created_at: ts,
    data: {
      kind: "heartbeat",
      wake: false,
      ts,
      goal_status: goalStatus,
      no_error: true,
      goal_id: goal.goal_id,
      turn,
    },
  };
}

function buildTickSentinelEvent({ goal, turn, status, goalStatus, tick, zeroLlmWhenNoError }) {
  const tickData = tick?.data || {};
  const recommended = recommendedNextTool(status, tickData);
  const requiresAttention = goalStatus === "blocked";
  const kind = tickOutboxKind(status, goalStatus);
  const wake = shouldWakeOnTick(status, goalStatus, zeroLlmWhenNoError);
  return {
    kind,
    wake,
    session_id: goal.session_id,
    run_id: goal.run_id,
    source: "runtime_watch_loop",
    level: levelForStatus(status),
    type: "runtime_watch_loop_tick",
    severity: severityForStatus(status),
    status,
    title: `runtime_watch_loop turn ${turn}: ${status} (${goalStatus})`,
    message: `Goal ${goal.goal_id} turn ${turn} returned ${status}; goal_status=${goalStatus}.`,
    message_zh: `目标 ${goal.goal_id} 第 ${turn} 轮返回 ${status}；goal_status=${goalStatus}。`,
    requires_attention: requiresAttention,
    requires_ack: requiresAttention,
    recommended_next_tool: recommended,
    no_robot_motion: true,
    dedupe_key: `${goal.goal_id}:turn:${turn}:${status}`,
    data: {
      kind,
      wake,
      goal_id: goal.goal_id,
      turn,
      goal_status: goalStatus,
      tick_reason: tickData.reason || null,
      last_event: tickData.last_event || null,
      recommended_next_tool: recommended,
      run_status: tickData.run_status || null,
      error: tickData.error || null,
    },
  };
}

function defaultEmitSentinel({ event, outboxDir }) {
  return appendWatchLoopOutboxEntry(event, { outboxDir });
}

export async function runtimeWatchLoop(args = {}, deps = {}) {
  const runId = args.run_id;
  if (!runId) {
    throw new Error("runtime_watch_loop requires run_id.");
  }

  const watchDir = args.watch_dir || null;
  const outboxDir = args.outbox_dir || null;
  const maxTurns = clampInt(args.max_turns, DEFAULT_MAX_TURNS, 1, 1000);
  const maxRuntimeMs = clampInt(args.max_runtime_ms, DEFAULT_MAX_RUNTIME_MS, 1000, 24 * 60 * 60 * 1000);
  const intervalMs = clampInt(args.interval_ms, DEFAULT_INTERVAL_MS, MIN_INTERVAL_MS, MAX_INTERVAL_MS);
  const pollBlockMs = clampInt(args.max_block_ms, DEFAULT_POLL_BLOCK_MS, 1000, 120000);

  const sessionId = args.session_id || "default";
  const goalPrompt = args.goal_prompt || null;
  const zeroLlmWhenNoError = args.zero_llm_when_no_error === true;
  const verify = typeof deps.verify === "function" ? deps.verify : null;
  const poll = typeof deps.runtimeWatchPoll === "function" ? deps.runtimeWatchPoll : runtimeWatchPoll;
  const emitSentinel = typeof deps.emitSentinel === "function" ? deps.emitSentinel : defaultEmitSentinel;

  const existing = args.resume === true ? readGoalState(runId, { watchDir }) : null;
  const resumable = existing && ["continue", "budget_limited"].includes(existing.status);
  const now = new Date().toISOString();
  const goal = resumable
    ? existing
    : {
        goal_id: args.goal_id || randomUUID(),
        run_id: runId,
        session_id: sessionId,
        goal_prompt: goalPrompt,
        status: "continue",
        turns_completed: 0,
        max_turns: maxTurns,
        max_runtime_ms: maxRuntimeMs,
        interval_ms: intervalMs,
        created_at: now,
        started_at: now,
        updated_at: now,
        ended_at: null,
        ticks: [],
        final_status: null,
        final_reason: null,
      };

  if (resumable) {
    goal.max_turns = maxTurns;
    goal.max_runtime_ms = maxRuntimeMs;
    goal.interval_ms = intervalMs;
    goal.updated_at = now;
  }

  const runtimeDeadline = Date.parse(goal.started_at) + goal.max_runtime_ms;
  let turn = goal.turns_completed || 0;
  let stopped = false;
  let stopReason = null;

  while (!stopped && turn < goal.max_turns && Date.now() < runtimeDeadline) {
    let tick;
    try {
      tick = await poll(
        {
          ...args,
          max_block_ms: Math.min(pollBlockMs, Math.max(1000, runtimeDeadline - Date.now())),
        },
        {
          readSnapshot: deps.readSnapshot,
          readGuidance: deps.readGuidance,
          executeRecovery: deps.executeRecovery,
        },
      );
    } catch (error) {
      tick = {
        status: "unreachable",
        data: {
          reason: "runtime_watch_loop_poll_error",
          error: error instanceof Error ? error.message : String(error),
        },
      };
    }

    turn += 1;
    const status = String(tick?.status || "running").toLowerCase();
    const verified = verify ? Boolean(verify(tick)) : false;
    const goalStatus = goalStatusFromTick(status, verified);
    const tickData = tick?.data || {};
    const recommended = recommendedNextTool(status, tickData);
    const tickRecord = {
      turn,
      status,
      goal_status: goalStatus,
      at: new Date().toISOString(),
      reason: tickData.reason || null,
      last_event: tickData.last_event || null,
      recommended_next_tool: recommended,
      verified,
    };
    goal.ticks.push(tickRecord);
    goal.turns_completed = turn;
    goal.status = goalStatus;
    goal.updated_at = new Date().toISOString();

    const outboxEvent = shouldWakeOnTick(status, goalStatus, zeroLlmWhenNoError)
      ? buildTickSentinelEvent({
          goal,
          turn,
          status,
          goalStatus,
          tick,
          zeroLlmWhenNoError,
        })
      : buildHeartbeatEvent({ goal, turn, goalStatus });
    try {
      emitSentinel({ event: outboxEvent, outboxDir });
    } catch {
      // Sentinel emission must not abort the loop; the goal-state file still records progress.
    }

    if (verified) {
      stopped = true;
      stopReason = "verify_passed";
      goal.final_status = status;
      goal.final_reason = stopReason;
    } else if (status === "completed") {
      stopped = true;
      stopReason = "completed";
      goal.final_status = status;
      goal.final_reason = stopReason;
    } else if (status === "hard_stop") {
      stopped = true;
      stopReason = "hard_stop";
      goal.status = "blocked";
      goal.final_status = status;
      goal.final_reason = stopReason;
    } else if (status === "needs_user") {
      stopped = true;
      stopReason = "needs_user";
      goal.status = "blocked";
      goal.final_status = status;
      goal.final_reason = stopReason;
    } else if (status === "unreachable") {
      stopped = true;
      stopReason = "unreachable";
      goal.status = "blocked";
      goal.final_status = status;
      goal.final_reason = stopReason;
    }

    writeGoalState(runId, goal, { watchDir });

    if (stopped) {
      break;
    }

    const remainingRuntime = runtimeDeadline - Date.now();
    if (remainingRuntime <= 0) {
      break;
    }
    await sleep(Math.min(intervalMs, remainingRuntime), deps);
  }

  if (!stopped) {
    if (turn >= goal.max_turns) {
      goal.status = "budget_limited";
      goal.final_reason = "max_turns_reached";
    } else {
      goal.status = "budget_limited";
      goal.final_reason = "max_runtime_reached";
    }
    goal.final_status = goal.final_status || "running";
  }

  goal.ended_at = new Date().toISOString();
  goal.updated_at = goal.ended_at;
  writeGoalState(runId, goal, { watchDir });

  let delivery = null;
  if (Array.isArray(args.notify_adapters) && args.notify_adapters.length > 0) {
    try {
      delivery = await deliverRuntimeOutbox({
        sessionId: goal.session_id,
        runId: goal.run_id,
        adapters: args.notify_adapters,
        limit: args.notify_limit ?? 20,
        outboxDir,
        hostAdapterDir: args.host_adapter_dir || null,
        webhookUrl: args.webhook_url || null,
      });
    } catch (error) {
      delivery = {
        status: "failed",
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  return {
    goal_id: goal.goal_id,
    run_id: goal.run_id,
    session_id: goal.session_id,
    status: goal.status,
    goal_status: goal.status === "complete" ? "COMPLETE" : goal.status === "blocked" ? "BLOCKED" : "BUDGET_LIMITED",
    turns_completed: goal.turns_completed,
    max_turns: goal.max_turns,
    final_status: goal.final_status,
    final_reason: goal.final_reason,
    ticks: goal.ticks,
    goal_state_path: goalStatePath(runId, { watchDir }),
    outbox_delivery: delivery,
    no_robot_motion: true,
  };
}
