import test from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import os from "os";
import path from "path";

import { readSessionState, writeSessionState } from "../lib/state.js";
import { appendResultLogEntry, readResultLogEntries } from "../lib/result-log.js";

test("restart review: reconcile flag wins over a historical success log entry", () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-restart-"));
  const sessionDir = path.join(tempDir, "session-state");
  const logDir = path.join(tempDir, "result-logs");
  fs.mkdirSync(sessionDir, { recursive: true });
  fs.mkdirSync(logDir, { recursive: true });

  const originalSessionDir = process.env.OPENTRONS_SESSION_STATE_DIR;
  const originalLogDir = process.env.OPENTRONS_RESULT_LOG_DIR;

  process.env.OPENTRONS_SESSION_STATE_DIR = sessionDir;
  process.env.OPENTRONS_RESULT_LOG_DIR = logDir;

  try {
    writeSessionState({
      session_id: "restart-session",
      needs_reconciliation: true,
      state_revision: 3,
      deck: { slots: {} },
    });

    appendResultLogEntry({
      session_id: "restart-session",
      run_id: "run-old",
      tool_name: "run_protocol",
      event_kind: "protocol_run",
      status: "succeeded",
      summary: "Historical run succeeded",
      data: { note: "append-only evidence only" },
    });

    const session = readSessionState("restart-session");
    const entries = readResultLogEntries({ session_id: "restart-session", limit: 10 });

    assert.equal(session.needs_reconciliation, true);
    assert.equal(entries.length, 1);
    assert.equal(entries[0].tool_name, "run_protocol");
    assert.equal(entries[0].status, "succeeded");

    const restartGuidance = {
      mustReconcileBeforeAutonomousMotion: session.needs_reconciliation === true,
      lastLogStatus: entries[0]?.status || null,
    };

    assert.equal(restartGuidance.mustReconcileBeforeAutonomousMotion, true);
    assert.equal(restartGuidance.lastLogStatus, "succeeded");
  } finally {
    if (originalSessionDir === undefined) {
      delete process.env.OPENTRONS_SESSION_STATE_DIR;
    } else {
      process.env.OPENTRONS_SESSION_STATE_DIR = originalSessionDir;
    }
    if (originalLogDir === undefined) {
      delete process.env.OPENTRONS_RESULT_LOG_DIR;
    } else {
      process.env.OPENTRONS_RESULT_LOG_DIR = originalLogDir;
    }
  }
});
