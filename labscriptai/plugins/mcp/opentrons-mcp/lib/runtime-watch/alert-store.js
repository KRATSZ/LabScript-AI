import fs from "fs";
import path from "path";
import { randomUUID } from "crypto";

import { DATA_DIR } from "../paths.js";

const WATCH_DIR_ENV = "OPENTRONS_RUNTIME_WATCH_DIR";

function sanitizeRunId(runId) {
  return String(runId || "unknown-run").replace(/[^a-zA-Z0-9._-]/g, "_");
}

function dataDir() {
  return process.env.PLUGIN_DATA ? path.resolve(process.env.PLUGIN_DATA) : DATA_DIR;
}

export function resolveWatchRoot(watchDir = null) {
  return path.resolve(watchDir || process.env[WATCH_DIR_ENV] || path.join(dataDir(), "watch"));
}

export function getRunWatchDir(runId, { watchDir = null } = {}) {
  return path.join(resolveWatchRoot(watchDir), sanitizeRunId(runId));
}

export function ensureRunWatchDir(runId, options = {}) {
  const dir = getRunWatchDir(runId, options);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

export function watchFilePath(runId, fileName, options = {}) {
  return path.join(ensureRunWatchDir(runId, options), fileName);
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

export function readAlerts(runId, { limit = 50, includeAcked = true, watchDir = null } = {}) {
  const filePath = watchFilePath(runId, "alerts.jsonl", { watchDir });
  if (!fs.existsSync(filePath)) {
    return [];
  }

  const alerts = fs
    .readFileSync(filePath, "utf8")
    .split("\n")
    .map(parseJsonlLine)
    .filter(Boolean)
    .filter(alert => includeAcked || !alert.acked_at);

  alerts.sort((left, right) => String(right.created_at).localeCompare(String(left.created_at)));
  return alerts.slice(0, Math.max(1, Math.min(Number(limit || 50), 500)));
}

export function appendAlert(runId, alert, { watchDir = null, dedupe = true } = {}) {
  const filePath = watchFilePath(runId, "alerts.jsonl", { watchDir });
  const existingAlerts = readAlerts(runId, { limit: 500, includeAcked: true, watchDir });
  const dedupeKey = alert?.dedupe_key || null;

  if (dedupe && dedupeKey) {
    const existing = existingAlerts.find(
      item => item.dedupe_key === dedupeKey && !item.acked_at && item.type === alert.type,
    );
    if (existing) {
      return existing;
    }
  }

  const normalized = {
    alert_id: alert?.alert_id || randomUUID(),
    created_at: alert?.created_at || new Date().toISOString(),
    run_id: runId,
    type: alert?.type || "runtime_watch",
    status: alert?.status || "needs_user",
    level: alert?.level || "L3",
    message: alert?.message || null,
    dedupe_key: dedupeKey,
    requires_ack: alert?.requires_ack !== false,
    acked_at: alert?.acked_at || null,
    data: alert?.data || {},
  };

  fs.appendFileSync(filePath, `${JSON.stringify(normalized)}\n`);
  return normalized;
}

export function ackAlert(runId, alertId, { watchDir = null, note = null, selection = null } = {}) {
  const filePath = watchFilePath(runId, "alerts.jsonl", { watchDir });
  const alerts = readAlerts(runId, { limit: 500, includeAcked: true, watchDir }).sort((left, right) =>
    String(left.created_at).localeCompare(String(right.created_at)),
  );

  let matched = null;
  const updated = alerts.map(alert => {
    if (alert.alert_id !== alertId) {
      return alert;
    }
    matched = {
      ...alert,
      acked_at: new Date().toISOString(),
      ack_note: note,
      ack_selection: selection,
    };
    return matched;
  });

  if (!matched) {
    throw new Error(`runtime_ack_alert could not find alert ${alertId} for run ${runId}.`);
  }

  fs.writeFileSync(filePath, updated.map(alert => JSON.stringify(alert)).join("\n") + "\n");
  return matched;
}

export function readLatest(runId, { watchDir = null } = {}) {
  return readJsonFile(watchFilePath(runId, "latest.json", { watchDir }), null);
}

export function writeLatest(runId, latest, { watchDir = null } = {}) {
  const payload = {
    updated_at: new Date().toISOString(),
    run_id: runId,
    ...latest,
  };
  writeJsonFile(watchFilePath(runId, "latest.json", { watchDir }), payload);
  return payload;
}

export function acquireRunLock(runId, { watchDir = null, staleMs = 120000 } = {}) {
  const filePath = watchFilePath(runId, "run.lock", { watchDir });
  const token = randomUUID();
  const payload = {
    token,
    pid: process.pid,
    created_at: new Date().toISOString(),
  };

  try {
    fs.writeFileSync(filePath, JSON.stringify(payload), { flag: "wx" });
    return buildLockHandle(filePath, payload);
  } catch (error) {
    if (error?.code !== "EEXIST") {
      throw error;
    }
  }

  const existing = readJsonFile(filePath, null);
  const createdAt = existing?.created_at ? Date.parse(existing.created_at) : 0;
  const stale = !createdAt || Date.now() - createdAt >= staleMs;
  if (!stale) {
    return {
      acquired: false,
      lock: existing,
      release() {},
    };
  }

  try {
    fs.unlinkSync(filePath);
    fs.writeFileSync(filePath, JSON.stringify(payload), { flag: "wx" });
    return buildLockHandle(filePath, payload);
  } catch (error) {
    if (error?.code === "EEXIST") {
      return {
        acquired: false,
        lock: readJsonFile(filePath, null),
        release() {},
      };
    }
    throw error;
  }
}

function buildLockHandle(filePath, payload) {
  return {
    acquired: true,
    lock: payload,
    release() {
      const current = readJsonFile(filePath, null);
      if (current?.token === payload.token) {
        try {
          fs.unlinkSync(filePath);
        } catch (error) {
          if (error?.code !== "ENOENT") {
            throw error;
          }
        }
      }
    },
  };
}
