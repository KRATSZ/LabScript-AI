import fs from "fs";
import path from "path";
import { createHash, randomUUID } from "crypto";

import { DATA_DIR } from "./paths.js";
import { appendAlert } from "./runtime-watch/alert-store.js";

const OUTBOX_DIR_ENV = "OPENTRONS_RUNTIME_OUTBOX_DIR";
const HOST_ADAPTER_DIR_ENV = "OPENTRONS_RUNTIME_HOST_ADAPTER_DIR";
const WEBHOOK_URL_ENV = "OPENTRONS_RUNTIME_ALERT_WEBHOOK_URL";
const DEFAULT_SESSION_ID = "default";
const DEFAULT_ADAPTERS = [
  "claudecode",
  "claude",
  "codex",
  "cursor",
  "piagent",
  "opencode",
  "cli",
  "webhook",
];

function sanitizePart(value, fallback = "default") {
  return String(value || fallback).replace(/[^a-zA-Z0-9._-]/g, "_");
}

function resolveOutboxRoot(outboxDir = null) {
  return path.resolve(outboxDir || process.env[OUTBOX_DIR_ENV] || path.join(DATA_DIR, "runtime-outbox"));
}

function resolveHostAdapterRoot(hostAdapterDir = null) {
  return path.resolve(
    hostAdapterDir ||
      process.env[HOST_ADAPTER_DIR_ENV] ||
      path.join(DATA_DIR, "host-adapters"),
  );
}

function sessionDir(sessionId = DEFAULT_SESSION_ID, { outboxDir = null } = {}) {
  return path.join(resolveOutboxRoot(outboxDir), sanitizePart(sessionId, DEFAULT_SESSION_ID));
}

function outboxPath(sessionId = DEFAULT_SESSION_ID, options = {}) {
  return path.join(sessionDir(sessionId, options), "outbox.jsonl");
}

function monitorStatePath(sessionId = DEFAULT_SESSION_ID, options = {}) {
  return path.join(sessionDir(sessionId, options), "monitor-state.json");
}

function adapterOutboxPath(adapter, sessionId = DEFAULT_SESSION_ID, { hostAdapterDir = null } = {}) {
  return path.join(
    resolveHostAdapterRoot(hostAdapterDir),
    sanitizePart(adapter, "adapter"),
    `${sanitizePart(sessionId, DEFAULT_SESSION_ID)}.jsonl`,
  );
}

function parseJsonlLine(line) {
  const trimmed = String(line || "").trim();
  if (!trimmed) {
    return null;
  }
  try {
    return JSON.parse(trimmed);
  } catch {
    return null;
  }
}

function readJsonFile(filePath, fallback) {
  if (!fs.existsSync(filePath)) {
    return fallback;
  }
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return fallback;
  }
}

function writeJsonFile(filePath, payload) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const tempPath = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  fs.writeFileSync(tempPath, `${JSON.stringify(payload, null, 2)}\n`);
  fs.renameSync(tempPath, filePath);
}

function stableValue(value) {
  if (Array.isArray(value)) {
    return value.map(stableValue);
  }
  if (value && typeof value === "object") {
    return Object.keys(value)
      .sort()
      .reduce((out, key) => {
        if (["created_at", "notification_id", "monitor_id", "timestamp"].includes(key)) {
          return out;
        }
        out[key] = stableValue(value[key]);
        return out;
      }, {});
  }
  return value;
}

function stableJson(value) {
  return JSON.stringify(stableValue(value));
}

function shortHash(value) {
  return createHash("sha256").update(String(value)).digest("hex").slice(0, 16);
}

function normalizeAdapterList(adapters = []) {
  const requested = Array.isArray(adapters) ? adapters : [];
  const normalized = requested
    .map(item => String(item || "").trim().toLowerCase())
    .map(item => (item === "claude" ? "claudecode" : item))
    .filter(item => DEFAULT_ADAPTERS.includes(item));
  return [...new Set(normalized)];
}

function notificationFingerprint({ sessionId, runId, notification }) {
  const signature = {
    session_id: sessionId,
    run_id: runId || null,
    level: notification.level || null,
    type: notification.type || "runtime_monitor",
    severity: notification.severity || "info",
    requires_attention: notification.requires_attention === true,
    recommended_next_tool: notification.recommended_next_tool || null,
    data: notification.data || {},
  };
  return shortHash(stableJson(signature));
}

function alertStatusForEvent(event = {}) {
  if (event.severity === "hard_stop") {
    return "hard_stop";
  }
  if (event.requires_attention) {
    return "needs_user";
  }
  if (event.type === "monitor_status_changed") {
    return event.status || "info";
  }
  return event.type === "robot_api_reachable" || event.type === "liquid_gate_ready"
    ? "resolved"
    : "info";
}

function normalizeOutboxEvent(event = {}) {
  const sessionId = sanitizePart(event.session_id || DEFAULT_SESSION_ID, DEFAULT_SESSION_ID);
  const runId = event.run_id || null;
  const type = event.type || "runtime_monitor";
  const createdAt = event.created_at || new Date().toISOString();
  const dedupeKey =
    event.dedupe_key ||
    `${sessionId}:${runId || "session"}:${type}:${shortHash(stableJson(event.data || {}))}`;
  const kind = event.kind ?? event.data?.kind ?? null;
  const wake =
    event.wake === true ? true : event.wake === false ? false : null;
  const data = { ...(event.data || {}) };
  if (kind != null && data.kind == null) {
    data.kind = kind;
  }
  if (wake != null && data.wake == null) {
    data.wake = wake;
  }
  return {
    outbox_id: event.outbox_id || randomUUID(),
    created_at: createdAt,
    session_id: sessionId,
    run_id: runId,
    robot_ip: event.robot_ip || null,
    source: event.source || "runtime_recovery_monitor",
    level: event.level || "L2",
    type,
    severity: event.severity || "info",
    status: event.status || alertStatusForEvent(event),
    title: event.title || event.message_zh || event.message || type,
    message: event.message || event.message_zh || type,
    message_zh: event.message_zh || event.message || type,
    requires_attention: event.requires_attention === true,
    requires_ack: event.requires_ack !== false,
    recommended_next_tool: event.recommended_next_tool || null,
    no_robot_motion: event.no_robot_motion !== false,
    dedupe_key: dedupeKey,
    acked_at: event.acked_at || null,
    ack_note: event.ack_note || null,
    ack_selection: event.ack_selection ?? null,
    deliveries: event.deliveries || {},
    delivery_status: event.delivery_status || "pending",
    kind,
    wake,
    data,
  };
}

function readOutboxFile(sessionId = DEFAULT_SESSION_ID, { outboxDir = null } = {}) {
  const filePath = outboxPath(sessionId, { outboxDir });
  if (!fs.existsSync(filePath)) {
    return [];
  }
  return fs
    .readFileSync(filePath, "utf8")
    .split("\n")
    .map(parseJsonlLine)
    .filter(Boolean);
}

function writeOutboxFile(sessionId = DEFAULT_SESSION_ID, entries = [], { outboxDir = null } = {}) {
  const filePath = outboxPath(sessionId, { outboxDir });
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, entries.map(entry => JSON.stringify(entry)).join("\n") + "\n");
}

export function readRuntimeOutbox({
  sessionId = DEFAULT_SESSION_ID,
  runId = null,
  includeAcked = false,
  includeDelivered = true,
  limit = 50,
  outboxDir = null,
} = {}) {
  const entries = readOutboxFile(sessionId, { outboxDir })
    .filter(entry => !runId || entry.run_id === runId)
    .filter(entry => includeAcked || !entry.acked_at)
    .filter(entry => includeDelivered || entry.delivery_status !== "delivered");
  entries.sort((left, right) => String(right.created_at).localeCompare(String(left.created_at)));
  return entries.slice(0, Math.max(1, Math.min(Number(limit || 50), 500)));
}

export function appendRuntimeOutboxEvent(event = {}, { outboxDir = null, dedupe = true } = {}) {
  const normalized = normalizeOutboxEvent(event);
  const entries = readOutboxFile(normalized.session_id, { outboxDir });

  if (dedupe && normalized.dedupe_key) {
    const existing = entries.find(
      item => item.dedupe_key === normalized.dedupe_key && !item.acked_at,
    );
    if (existing) {
      return existing;
    }
  }

  entries.push(normalized);
  writeOutboxFile(normalized.session_id, entries, { outboxDir });
  return normalized;
}

export function ackRuntimeOutboxEvent({
  sessionId = DEFAULT_SESSION_ID,
  outboxId,
  note = null,
  selection = null,
  outboxDir = null,
} = {}) {
  if (!outboxId) {
    throw new Error("runtime_ack_outbox requires outbox_id.");
  }
  const entries = readOutboxFile(sessionId, { outboxDir });
  let matched = null;
  const updated = entries.map(entry => {
    if (entry.outbox_id !== outboxId) {
      return entry;
    }
    matched = {
      ...entry,
      acked_at: new Date().toISOString(),
      ack_note: note,
      ack_selection: selection,
      delivery_status: "acked",
    };
    return matched;
  });
  if (!matched) {
    throw new Error(`runtime_ack_outbox could not find outbox event ${outboxId}.`);
  }
  writeOutboxFile(sessionId, updated, { outboxDir });
  return matched;
}

function buildOutboxEventFromNotification({
  monitor,
  notification,
  eventType = null,
  message = null,
  messageZh = null,
  requiresAttention = null,
  severity = null,
} = {}) {
  const sessionId = monitor.session_id || DEFAULT_SESSION_ID;
  const runId = monitor.run_id || null;
  const dedupeSeed = notificationFingerprint({
    sessionId,
    runId,
    notification: {
      ...notification,
      type: eventType || notification.type,
      severity: severity || notification.severity,
      requires_attention:
        typeof requiresAttention === "boolean"
          ? requiresAttention
          : notification.requires_attention === true,
    },
  });
  return normalizeOutboxEvent({
    session_id: sessionId,
    run_id: runId,
    robot_ip: monitor.robot_ip || null,
    type: eventType || notification.type,
    level: notification.level || "L2",
    severity: severity || notification.severity || "info",
    message: message || notification.message || notification.type,
    message_zh: messageZh || notification.message_zh || notification.message || notification.type,
    requires_attention:
      typeof requiresAttention === "boolean"
        ? requiresAttention
        : notification.requires_attention === true,
    requires_ack:
      typeof requiresAttention === "boolean"
        ? requiresAttention
        : notification.requires_attention === true,
    recommended_next_tool: notification.recommended_next_tool || null,
    no_robot_motion: monitor.no_robot_motion !== false,
    dedupe_key: `${sessionId}:${runId || "session"}:${eventType || notification.type}:${dedupeSeed}`,
    data: {
      monitor_id: monitor.monitor_id || null,
      monitor_status: monitor.status || null,
      notification,
    },
  });
}

function currentMonitorFlags(monitor = {}) {
  const notifications = Array.isArray(monitor.notifications) ? monitor.notifications : [];
  const l1Checks = monitor.levels?.L1?.checks || [];
  const robotStatus = l1Checks.find(check => check.name === "robot_status")?.status || null;
  const liquidGateReady = monitor.levels?.L3?.liquid_gate?.ok_for_live_liquid_rerun === true;
  const liquidGateBlocked = notifications.some(item => item.type === "liquid_gate_blocked");
  return {
    status: monitor.status || null,
    requires_attention: monitor.requires_attention === true,
    robot_api_unreachable: robotStatus === "unreachable",
    robot_status: robotStatus,
    liquid_gate_blocked: liquidGateBlocked,
    liquid_gate_ready: liquidGateReady,
    active_notification_types: notifications
      .filter(item => item.requires_attention || item.severity === "hard_stop")
      .map(item => item.type)
      .sort(),
  };
}

function buildSyntheticEvents({ monitor, previousState, currentFlags } = {}) {
  if (!previousState) {
    return [];
  }
  const events = [];
  const baseNotification = {
    level: "L1",
    type: "runtime_monitor",
    severity: "info",
    requires_attention: false,
    recommended_next_tool: "runtime_recovery_monitor",
    data: {},
  };

  if (previousState.robot_api_unreachable === true && currentFlags.robot_api_unreachable === false) {
    events.push(
      buildOutboxEventFromNotification({
        monitor,
        notification: {
          ...baseNotification,
          level: "L1",
          type: "robot_api_reachable",
          data: { robot_status: currentFlags.robot_status },
        },
        eventType: "robot_api_reachable",
        message: "Robot API became reachable again.",
        messageZh: "机器人 API 已恢复可达。",
        requiresAttention: false,
        severity: "info",
      }),
    );
  }

  if (previousState.liquid_gate_blocked === true && currentFlags.liquid_gate_ready === true) {
    events.push(
      buildOutboxEventFromNotification({
        monitor,
        notification: {
          ...baseNotification,
          level: "L3",
          type: "liquid_gate_ready",
          recommended_next_tool: "safe_next_action",
          data: { liquid_gate: monitor.levels?.L3?.liquid_gate || null },
        },
        eventType: "liquid_gate_ready",
        message: "Live liquid recovery gate is ready for the next explicit operator decision.",
        messageZh: "液体恢复 gate 已通过，可以进入下一步人工确认。",
        requiresAttention: false,
        severity: "info",
      }),
    );
  }

  if (
    previousState.status &&
    previousState.status !== currentFlags.status &&
    (previousState.requires_attention === true || currentFlags.requires_attention === true)
  ) {
    events.push(
      buildOutboxEventFromNotification({
        monitor,
        notification: {
          ...baseNotification,
          level: "L2",
          type: "monitor_status_changed",
          data: {
            previous_status: previousState.status,
            current_status: currentFlags.status,
          },
        },
        eventType: "monitor_status_changed",
        message: `Runtime monitor status changed from ${previousState.status} to ${currentFlags.status}.`,
        messageZh: `主动监控状态从 ${previousState.status} 变为 ${currentFlags.status}。`,
        requiresAttention: currentFlags.requires_attention === true,
        severity: currentFlags.requires_attention === true ? "warn" : "info",
      }),
    );
  }

  return events;
}

function shouldPublishNotification(notification = {}, { includeInfo = false } = {}) {
  return (
    notification.requires_attention === true ||
    notification.severity === "hard_stop" ||
    includeInfo === true
  );
}

export function publishMonitorNotifications({
  monitor,
  watchDir = null,
  outboxDir = null,
  includeInfo = false,
} = {}) {
  if (!monitor || typeof monitor !== "object") {
    return {
      status: "skipped",
      reason: "monitor_missing",
      alerts: [],
      outbox_events: [],
      monitor_state_path: null,
    };
  }

  const sessionId = sanitizePart(monitor.session_id || DEFAULT_SESSION_ID, DEFAULT_SESSION_ID);
  const runKey = monitor.run_id || sessionId;
  const stateFile = monitorStatePath(sessionId, { outboxDir });
  const previousState = readJsonFile(stateFile, null);
  const currentFlags = currentMonitorFlags(monitor);
  const notifications = Array.isArray(monitor.notifications) ? monitor.notifications : [];
  const publishable = notifications
    .filter(notification => shouldPublishNotification(notification, { includeInfo }))
    .map(notification => buildOutboxEventFromNotification({ monitor, notification }));
  const synthetic = buildSyntheticEvents({ monitor, previousState, currentFlags });
  const events = [...publishable, ...synthetic];
  const alerts = [];
  const outboxEvents = [];

  for (const event of events) {
    const alert = appendAlert(
      runKey,
      {
        type: `monitor_${event.type}`,
        status: alertStatusForEvent(event),
        level: event.level,
        message: event.message_zh || event.message,
        dedupe_key: event.dedupe_key,
        requires_ack: event.requires_ack,
        data: {
          ...event.data,
          session_id: sessionId,
          outbox_dedupe_key: event.dedupe_key,
          no_robot_motion: event.no_robot_motion,
          recommended_next_tool: event.recommended_next_tool,
        },
      },
      { watchDir },
    );
    const outboxEvent = appendRuntimeOutboxEvent(
      {
        ...event,
        data: {
          ...event.data,
          alert_id: alert.alert_id,
          alert_run_id: runKey,
        },
      },
      { outboxDir },
    );
    alerts.push(alert);
    outboxEvents.push(outboxEvent);
  }

  writeJsonFile(stateFile, {
    updated_at: new Date().toISOString(),
    session_id: sessionId,
    run_id: monitor.run_id || null,
    robot_ip: monitor.robot_ip || null,
    ...currentFlags,
  });

  return {
    status: "published",
    alerts,
    outbox_events: outboxEvents,
    monitor_state_path: stateFile,
  };
}

function renderCliMessage(event = {}) {
  const tool = event.recommended_next_tool ? ` next=${event.recommended_next_tool}` : "";
  return `[${event.level || "L?"}/${event.severity || "info"}] ${event.message_zh || event.message || event.type}${tool} no_robot_motion=${event.no_robot_motion !== false}`;
}

async function deliverToAdapter(event, adapter, options = {}) {
  if (adapter === "cli") {
    return {
      status: "delivered",
      target: "stdout",
      message: renderCliMessage(event),
    };
  }

  if (["claudecode", "codex", "cursor", "piagent", "opencode"].includes(adapter)) {
    const filePath = adapterOutboxPath(adapter, event.session_id, options);
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    const payload = {
      delivered_at: new Date().toISOString(),
      adapter,
      event,
    };
    const line = `${JSON.stringify(payload)}\n`;
    const existing = fs.existsSync(filePath) ? fs.readFileSync(filePath, "utf8") : "";
    const tempPath = `${filePath}.${process.pid}.${Date.now()}.tmp`;
    fs.writeFileSync(tempPath, existing + line);
    fs.renameSync(tempPath, filePath);
    const lastLine = fs.readFileSync(filePath, "utf8").trim().split("\n").pop();
    let verified = null;
    try {
      verified = JSON.parse(lastLine);
    } catch {
      verified = null;
    }
    if (verified?.event?.outbox_id !== event.outbox_id) {
      return {
        status: "failed",
        target: filePath,
        error: "adapter mailbox write verification failed",
      };
    }
    return {
      status: "delivered",
      target: filePath,
    };
  }

  if (adapter === "webhook") {
    const webhookUrl = options.webhookUrl || process.env[WEBHOOK_URL_ENV] || null;
    if (!webhookUrl) {
      return {
        status: "failed",
        target: null,
        error: `${WEBHOOK_URL_ENV} is not configured.`,
      };
    }
    const response = await fetch(webhookUrl, {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        event,
      }),
    });
    if (!response.ok) {
      return {
        status: "failed",
        target: webhookUrl,
        error: `webhook returned HTTP ${response.status}`,
      };
    }
    return {
      status: "delivered",
      target: webhookUrl,
      http_status: response.status,
    };
  }

  return {
    status: "failed",
    target: null,
    error: `Unsupported adapter ${adapter}.`,
  };
}

export async function deliverRuntimeOutbox({
  sessionId = DEFAULT_SESSION_ID,
  runId = null,
  adapters = [],
  limit = 20,
  includeDelivered = false,
  outboxDir = null,
  hostAdapterDir = null,
  webhookUrl = null,
} = {}) {
  const adapterList = normalizeAdapterList(adapters);
  if (adapterList.length === 0) {
    return {
      status: "skipped",
      reason: "no_adapters",
      delivered: [],
      failed: [],
      events: [],
    };
  }

  const entries = readOutboxFile(sessionId, { outboxDir });
  const pending = entries
    .filter(entry => !runId || entry.run_id === runId)
    .filter(entry => !entry.acked_at)
    .filter(entry => includeDelivered || adapterList.some(adapter => entry.deliveries?.[adapter]?.status !== "delivered"))
    .sort((left, right) => String(left.created_at).localeCompare(String(right.created_at)))
    .slice(0, Math.max(1, Math.min(Number(limit || 20), 200)));

  const delivered = [];
  const failed = [];
  const updated = [];

  for (const event of pending) {
    const nextEvent = {
      ...event,
      deliveries: { ...(event.deliveries || {}) },
    };
    for (const adapter of adapterList) {
      if (!includeDelivered && nextEvent.deliveries?.[adapter]?.status === "delivered") {
        continue;
      }
      const attempt = {
        attempted_at: new Date().toISOString(),
        ...(await deliverToAdapter(nextEvent, adapter, {
          hostAdapterDir,
          webhookUrl,
        })),
      };
      nextEvent.deliveries[adapter] = attempt;
      if (attempt.status === "delivered") {
        delivered.push({ outbox_id: nextEvent.outbox_id, adapter, attempt });
      } else {
        failed.push({ outbox_id: nextEvent.outbox_id, adapter, attempt });
      }
    }
    nextEvent.delivery_status = Object.values(nextEvent.deliveries).some(
      item => item?.status === "failed",
    )
      ? "partial"
      : adapterList.every(adapter => nextEvent.deliveries?.[adapter]?.status === "delivered")
        ? "delivered"
        : "pending";
    updated.push(nextEvent);
  }

  if (updated.length > 0) {
    const byId = new Map(updated.map(entry => [entry.outbox_id, entry]));
    const rewritten = entries.map(entry => byId.get(entry.outbox_id) || entry);
    writeOutboxFile(sessionId, rewritten, { outboxDir });
  }

  return {
    status: failed.length > 0 ? "partial" : "delivered",
    delivered,
    failed,
    events: updated,
  };
}

export function runtimeOutboxPaths({
  sessionId = DEFAULT_SESSION_ID,
  outboxDir = null,
  hostAdapterDir = null,
} = {}) {
  return {
    outbox_path: outboxPath(sessionId, { outboxDir }),
    monitor_state_path: monitorStatePath(sessionId, { outboxDir }),
    host_adapter_root: resolveHostAdapterRoot(hostAdapterDir),
  };
}
