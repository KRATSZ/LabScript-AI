import test from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import os from "os";
import path from "path";

import { TOOL_HANDLERS } from "../index.js";
import { buildRestartReview, buildSafeNextAction } from "../lib/restart-review.js";
import { writeSessionState } from "../lib/state.js";
import { appendResultLogEntry } from "../lib/result-log.js";

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

test("buildRestartReview includes run_history and parse_error when last_run_id is set", () => {
  const data = buildRestartReview({
    sessionState: {
      session_id: "s-run",
      state_revision: 1,
      needs_reconciliation: false,
      last_run_id: "run-abc",
      cleanup: { pending_actions: [] },
    },
    logEntries: [],
    homeSafety: null,
  });

  const order = data.guidance.suggested_tool_order;
  assert.ok(order.indexOf("reconcile_state") === -1);
  assert.ok(order.indexOf("robot_status") < order.indexOf("run_history"));
  assert.ok(order.indexOf("run_history") < order.indexOf("parse_error"));
  assert.ok(order.includes("experiment_history"));
  assert.ok(order.includes("is_home_safe"));
});

test("buildRestartReview extends narrative when home safety preview blocks auto-home", () => {
  const data = buildRestartReview({
    sessionState: {
      session_id: "s1",
      state_revision: 1,
      needs_reconciliation: false,
      last_run_id: null,
      cleanup: { pending_actions: [] },
    },
    logEntries: [
      {
        tool_name: "run_protocol",
        status: "succeeded",
        timestamp: "2026-01-01T00:00:00.000Z",
      },
    ],
    homeSafety: {
      auto_home_allowed: false,
      blockers: ["tip_attached:left"],
      minimum_cleanup_actions: ["drop_tip:left"],
    },
  });

  assert.equal(data.guidance.home_safety_preview?.auto_home_allowed, false);
  assert.match(data.guidance.narrative, /Live home-safety preview disallows auto-home/i);
});

test("buildSafeNextAction recommends reconcile_state when session needs reconciliation", () => {
  const data = buildRestartReview({
    sessionState: {
      session_id: "s-rec",
      state_revision: 2,
      needs_reconciliation: true,
      last_run_id: "run-x",
      cleanup: { pending_actions: [] },
    },
    logEntries: [],
    homeSafety: null,
  });
  const sn = buildSafeNextAction(data);
  assert.equal(sn.recommended_next_tool, "reconcile_state");
  assert.equal(sn.reconcile_first, true);
  assert.ok(sn.operator_steps[0].includes("reconcile_state"));
});

test("buildSafeNextAction recommends robot_status when no reconciliation flag", () => {
  const data = buildRestartReview({
    sessionState: {
      session_id: "s-ok",
      state_revision: 1,
      needs_reconciliation: false,
      last_run_id: null,
      cleanup: { pending_actions: [] },
    },
    logEntries: [],
    homeSafety: null,
  });
  const sn = buildSafeNextAction(data);
  assert.equal(sn.recommended_next_tool, "robot_status");
  assert.equal(sn.reconcile_first, false);
});

test("buildSafeNextAction surfaces home blockers and cleanup actions from preview", () => {
  const data = buildRestartReview({
    sessionState: {
      session_id: "s-home",
      state_revision: 1,
      needs_reconciliation: false,
      last_run_id: "run-home",
      cleanup: { pending_actions: [] },
    },
    logEntries: [],
    homeSafety: {
      auto_home_allowed: false,
      blockers: ["tip_attached:left", "cleanup_pending"],
      minimum_cleanup_actions: ["drop_tip:left", "finish_cleanup_motion"],
    },
  });
  const sn = buildSafeNextAction(data);
  assert.equal(sn.home_action_required, true);
  assert.deepEqual(sn.home_blockers, ["tip_attached:left", "cleanup_pending"]);
  assert.deepEqual(sn.minimum_cleanup_actions, ["drop_tip:left", "finish_cleanup_motion"]);
  assert.ok(sn.operator_steps.some((step) => step.includes("Do not home yet")));
  assert.ok(sn.operator_steps.some((step) => step.includes("drop_tip:left")));
});

test("buildRestartReview flags reconcile_first when session needs reconciliation", () => {
  const data = buildRestartReview({
    sessionState: {
      session_id: "s1",
      state_revision: 2,
      needs_reconciliation: true,
      last_run_id: "run-x",
      cleanup: { pending_actions: [] },
    },
    logEntries: [
      {
        tool_name: "run_protocol",
        status: "succeeded",
        timestamp: "2026-01-01T00:00:00.000Z",
      },
    ],
    homeSafety: null,
  });

  assert.equal(data.guidance.reconcile_first, true);
  assert.equal(data.guidance.logs_are_historical_only, true);
  assert.ok(data.guidance.suggested_tool_order.includes("reconcile_state"));
  assert.equal(data.guidance.home_safety_preview, null);
  assert.equal(data.recent_log_summary.total, 1);
});

test("restart_review handler includes run_history and parse_error when last_run_id is set", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-restart-order-"));
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
      session_id: "order-session",
      needs_reconciliation: false,
      state_revision: 2,
      last_run_id: "run-active",
      deck: { slots: {} },
      cleanup: { pending_actions: [] },
    });

    appendResultLogEntry({
      session_id: "order-session",
      run_id: "run-active",
      tool_name: "run_protocol",
      event_kind: "protocol_run",
      status: "succeeded",
      summary: "Historical success",
    });

    const result = await TOOL_HANDLERS.restart_review({
      session_id: "order-session",
      limit: 5,
    });

    const order = result.data.guidance.suggested_tool_order;
    assert.ok(order.includes("run_history"));
    assert.ok(order.includes("parse_error"));
    assert.ok(order.indexOf("robot_status") < order.indexOf("run_history"));
    assert.ok(order.indexOf("run_history") < order.indexOf("parse_error"));
    assert.equal(result.data.guidance.reconcile_first, false);
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

test("safe_next_action handler merges safe_next_action summary into restart_review data", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-safe-next-"));
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
      session_id: "sns-session",
      needs_reconciliation: false,
      state_revision: 1,
      last_run_id: "run-active",
      deck: { slots: {} },
      cleanup: { pending_actions: [] },
    });

    const result = await TOOL_HANDLERS.safe_next_action({
      session_id: "sns-session",
      limit: 5,
    });

    assert.ok(result.data.guidance);
    assert.ok(result.data.safe_next_action);
    assert.equal(result.data.safe_next_action.recommended_next_tool, "robot_status");
    assert.equal(result.data.safe_next_action.reconcile_first, false);
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

test("restart_review with tip on pipette warns in narrative despite succeeded log line", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-restart-home-block-"));
  const sessionDir = path.join(tempDir, "session-state");
  const logDir = path.join(tempDir, "result-logs");
  fs.mkdirSync(sessionDir, { recursive: true });
  fs.mkdirSync(logDir, { recursive: true });

  const originalSessionDir = process.env.OPENTRONS_SESSION_STATE_DIR;
  const originalLogDir = process.env.OPENTRONS_RESULT_LOG_DIR;
  const originalFetch = global.fetch;

  process.env.OPENTRONS_SESSION_STATE_DIR = sessionDir;
  process.env.OPENTRONS_RESULT_LOG_DIR = logDir;

  writeSessionState({
    session_id: "home-block",
    needs_reconciliation: false,
    state_revision: 1,
    last_run_id: "run-z",
    deck: { slots: {} },
    cleanup: { pending_actions: [] },
  });

  appendResultLogEntry({
    session_id: "home-block",
    run_id: "run-z",
    tool_name: "run_protocol",
    event_kind: "protocol_run",
    status: "succeeded",
    summary: "Looks successful in audit log",
  });

  global.fetch = async (url, options = {}) => {
    const requestUrl = new URL(url);
    if ((options.method || "GET") === "GET" && requestUrl.pathname === "/health") {
      return jsonResponse({
        name: "Flex",
        robot_model: "OT-3 Standard",
        robot_serial: "home-block",
      });
    }
    if ((options.method || "GET") === "GET" && requestUrl.pathname === "/instruments") {
      return jsonResponse({
        data: [
          {
            mount: "left",
            instrumentName: "p1000_single_flex",
            ok: true,
            state: { tipDetected: true },
          },
        ],
      });
    }
    if ((options.method || "GET") === "GET" && requestUrl.pathname === "/robot/door/status") {
      return jsonResponse({ data: { status: "closed" } });
    }
    if ((options.method || "GET") === "GET" && requestUrl.pathname === "/robot/control/estopStatus") {
      return jsonResponse({ data: { status: "disengaged" } });
    }
    if ((options.method || "GET") === "GET" && requestUrl.pathname === "/deck_configuration") {
      return jsonResponse({ data: { cutoutFixtures: [] } });
    }
    throw new Error(`Unexpected request: ${requestUrl.pathname}`);
  };

  try {
    const result = await TOOL_HANDLERS.restart_review({
      robot_ip: "10.0.0.2:31950",
      session_id: "home-block",
      limit: 5,
    });

    assert.equal(result.data.guidance.home_safety_preview?.auto_home_allowed, false);
    assert.match(result.data.guidance.narrative, /Live home-safety preview disallows auto-home/i);
    assert.equal(result.data.recent_log_entries[0].status, "succeeded");
  } finally {
    global.fetch = originalFetch;
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

test("restart_review merges session file and result logs without robot_ip", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-restart-review-"));
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
      session_id: "rr-session",
      needs_reconciliation: true,
      state_revision: 5,
      last_run_id: "run-99",
      deck: { slots: {} },
    });

    appendResultLogEntry({
      session_id: "rr-session",
      run_id: "run-99",
      tool_name: "run_protocol",
      event_kind: "protocol_run",
      status: "succeeded",
      summary: "Past success",
    });

    const result = await TOOL_HANDLERS.restart_review({
      session_id: "rr-session",
      limit: 10,
    });

    assert.equal(result.data.session_summary.needs_reconciliation, true);
    assert.equal(result.data.guidance.reconcile_first, true);
    assert.equal(result.data.recent_log_entries.length, 1);
    assert.equal(result.data.recent_log_entries[0].tool_name, "run_protocol");
    assert.equal(result.sessionId, "rr-session");
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

test("restart_review with robot_ip includes home_safety_preview", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-restart-review-live-"));
  const sessionDir = path.join(tempDir, "session-state");
  const logDir = path.join(tempDir, "result-logs");
  fs.mkdirSync(sessionDir, { recursive: true });
  fs.mkdirSync(logDir, { recursive: true });

  const originalSessionDir = process.env.OPENTRONS_SESSION_STATE_DIR;
  const originalLogDir = process.env.OPENTRONS_RESULT_LOG_DIR;
  const originalFetch = global.fetch;

  process.env.OPENTRONS_SESSION_STATE_DIR = sessionDir;
  process.env.OPENTRONS_RESULT_LOG_DIR = logDir;

  writeSessionState({
    session_id: "rr-live",
    needs_reconciliation: false,
    state_revision: 1,
    deck: { slots: {} },
    cleanup: { pending_actions: [] },
  });

  global.fetch = async (url, options = {}) => {
    const requestUrl = new URL(url);
    if ((options.method || "GET") === "GET" && requestUrl.pathname === "/health") {
      return jsonResponse({
        name: "Flex",
        robot_model: "OT-3 Standard",
        robot_serial: "rr-live",
      });
    }
    if ((options.method || "GET") === "GET" && requestUrl.pathname === "/instruments") {
      return jsonResponse({
        data: [{ mount: "left", instrumentName: "p1000_single_flex", ok: true, state: { tipDetected: false } }],
      });
    }
    if ((options.method || "GET") === "GET" && requestUrl.pathname === "/robot/door/status") {
      return jsonResponse({ data: { status: "closed" } });
    }
    if ((options.method || "GET") === "GET" && requestUrl.pathname === "/robot/control/estopStatus") {
      return jsonResponse({ data: { status: "disengaged" } });
    }
    if ((options.method || "GET") === "GET" && requestUrl.pathname === "/deck_configuration") {
      return jsonResponse({ data: { cutoutFixtures: [] } });
    }
    throw new Error(`Unexpected request: ${requestUrl.pathname}`);
  };

  try {
    const result = await TOOL_HANDLERS.restart_review({
      robot_ip: "10.0.0.1:31950",
      session_id: "rr-live",
      limit: 5,
    });

    assert.equal(result.sessionId, "rr-live");
    assert.equal(result.data.guidance.reconcile_first, false);
    assert.equal(result.data.guidance.home_safety_preview?.auto_home_allowed, true);
  } finally {
    global.fetch = originalFetch;
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
