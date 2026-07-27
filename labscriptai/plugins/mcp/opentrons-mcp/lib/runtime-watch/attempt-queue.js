import fs from "fs";
import { createHash, randomUUID } from "crypto";

import { watchFilePath } from "./alert-store.js";

function utcNow(now = null) {
  if (now instanceof Date) {
    return now.toISOString();
  }
  if (now) {
    return new Date(now).toISOString();
  }
  return new Date().toISOString();
}

function coerceTime(value, fallback = Date.now()) {
  const parsed = Date.parse(value || "");
  return Number.isFinite(parsed) ? parsed : fallback;
}

function readAttemptsFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return {
      schema_version: "0.1",
      attempts: [],
    };
  }
  try {
    const parsed = JSON.parse(fs.readFileSync(filePath, "utf8"));
    return {
      schema_version: parsed.schema_version || "0.1",
      attempts: Array.isArray(parsed.attempts) ? parsed.attempts : [],
    };
  } catch {
    return {
      schema_version: "0.1",
      attempts: [],
    };
  }
}

function writeAttemptsFile(filePath, payload) {
  const tempPath = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  fs.writeFileSync(tempPath, `${JSON.stringify(payload, null, 2)}\n`);
  fs.renameSync(tempPath, filePath);
}

function idempotencyKey({ runId, failedCommandId, branch, index }) {
  return createHash("sha256")
    .update(`${runId}:${failedCommandId}:${branch}:${index}`)
    .digest("hex")
    .slice(0, 24);
}

export class RuntimeAttemptQueue {
  constructor({
    runId,
    watchDir = null,
    maxAttemptsPerFailedCommand = 3,
    staleRunningAfterMs = 1800000,
  } = {}) {
    if (!runId) {
      throw new Error("RuntimeAttemptQueue requires runId.");
    }
    this.runId = runId;
    this.watchDir = watchDir;
    this.maxAttemptsPerFailedCommand = maxAttemptsPerFailedCommand;
    this.staleRunningAfterMs = staleRunningAfterMs;
    this.filePath = watchFilePath(runId, "attempts.json", { watchDir });
    this.payload = readAttemptsFile(this.filePath);
  }

  get attempts() {
    return this.payload.attempts;
  }

  save() {
    writeAttemptsFile(this.filePath, this.payload);
  }

  reapStale({ now = null } = {}) {
    const nowMs = now ? Date.parse(utcNow(now)) : Date.now();
    const reaped = [];
    this.payload.attempts = this.attempts.map(attempt => {
      if (attempt.status !== "running") {
        return attempt;
      }
      const startedAt = coerceTime(attempt.started_at, nowMs);
      if (nowMs - startedAt < this.staleRunningAfterMs) {
        return attempt;
      }
      const updated = {
        ...attempt,
        status: "failed",
        finished_at: utcNow(now),
        result: {
          ...(attempt.result || {}),
          result: "stale_running_reaped",
        },
      };
      reaped.push(updated);
      return updated;
    });
    if (reaped.length > 0) {
      this.save();
    }
    return reaped;
  }

  matchingAttempts({ failedCommandId, branch }) {
    return this.attempts.filter(
      attempt =>
        attempt.run_id === this.runId &&
        attempt.failed_command_id === String(failedCommandId || "") &&
        attempt.branch === String(branch || ""),
    );
  }

  canAttempt({ failedCommandId, branch, now = null } = {}) {
    this.reapStale({ now });
    const matching = this.matchingAttempts({ failedCommandId, branch });
    const key = `${failedCommandId || ""}:${branch || ""}`;
    if (matching.length >= this.maxAttemptsPerFailedCommand) {
      return {
        allowed: false,
        reason: `retry budget exhausted for ${key}`,
        attempts_used: matching.length,
        attempts_remaining: 0,
      };
    }
    if (matching.some(attempt => attempt.status === "running")) {
      return {
        allowed: false,
        reason: `attempt already running for ${key}`,
        attempts_used: matching.length,
        attempts_remaining: Math.max(0, this.maxAttemptsPerFailedCommand - matching.length),
      };
    }
    return {
      allowed: true,
      reason: null,
      attempts_used: matching.length,
      attempts_remaining: Math.max(0, this.maxAttemptsPerFailedCommand - matching.length),
    };
  }

  beginAttempt({ failedCommandId, errorLeaf, branch, gate = "L0", now = null } = {}) {
    const existingCount = this.matchingAttempts({ failedCommandId, branch }).length;
    const index = existingCount + 1;
    const attempt = {
      attempt_id: randomUUID(),
      run_id: this.runId,
      failed_command_id: String(failedCommandId || ""),
      error_leaf: String(errorLeaf || "UNKNOWN_NEEDS_HUMAN"),
      branch: String(branch || ""),
      idempotency_key: idempotencyKey({
        runId: this.runId,
        failedCommandId,
        branch,
        index,
      }),
      status: "running",
      started_at: utcNow(now),
      finished_at: null,
      gate,
      result: {},
    };
    this.payload.attempts.push(attempt);
    this.save();
    return attempt;
  }

  finishAttempt(attemptId, { status, result = {}, now = null } = {}) {
    let matched = null;
    this.payload.attempts = this.attempts.map(attempt => {
      if (attempt.attempt_id !== attemptId) {
        return attempt;
      }
      matched = {
        ...attempt,
        status: status || "failed",
        finished_at: utcNow(now),
        result,
      };
      return matched;
    });
    if (!matched) {
      throw new Error(`runtime attempt ${attemptId} was not found.`);
    }
    this.save();
    return matched;
  }
}

export function loadAttemptQueue(runId, options = {}) {
  return new RuntimeAttemptQueue({ runId, ...options });
}
