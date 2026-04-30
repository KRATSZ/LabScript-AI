import test from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import os from "os";
import path from "path";

import { TOOL_HANDLERS } from "../index.js";
import { buildLiveReadinessReport } from "../lib/live-readiness.js";

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json",
    },
  });
}

test("buildLiveReadinessReport prioritizes local runtime blockers", () => {
  const report = buildLiveReadinessReport({
    healthReport: {
      venv: { status: "ok", opentrons: "not_installed" },
      robot: { status: "reachable", robot_model: "OT-3 Standard", robot_serial: "FLX-1" },
    },
    restartReviewData: {
      session_summary: {
        session_id: "FLX-1",
        needs_reconciliation: false,
        last_run_id: null,
      },
    },
  });

  assert.equal(report.overall_status, "fail");
  assert.equal(report.checks[0].name, "local_runtime");
  assert.equal(report.checks[0].error_leaf, "RUNTIME_UNAVAILABLE");
  assert.deepEqual(report.recommended_next_tools, ["doctor_local_runtime"]);
});

test("buildLiveReadinessReport warns on stale session and preflight warnings", () => {
  const report = buildLiveReadinessReport({
    healthReport: {
      venv: { status: "ok", opentrons: "8.0.0" },
      robot: { status: "reachable", robot_model: "OT-3 Standard", robot_serial: "FLX-1" },
    },
    restartReviewData: {
      session_summary: {
        session_id: "FLX-1",
        needs_reconciliation: false,
        last_run_id: "run-1",
      },
      guidance: {
        suggested_tool_order: ["robot_status", "module_status", "run_history", "parse_error"],
      },
    },
    safeNextAction: {
      recommended_next_tool: "robot_status",
      tool_sequence: [
        { order: 1, tool: "robot_status" },
        { order: 2, tool: "module_status" },
        { order: 3, tool: "run_history" },
        { order: 4, tool: "parse_error" },
      ],
    },
    robotStatusSnapshot: {
      blockers: [],
      ready_for_physical_action: true,
    },
    moduleStatusSnapshot: {
      blockers: [],
    },
    homeSafety: {
      auto_home_allowed: true,
      blockers: [],
      minimum_cleanup_actions: [],
    },
    preflight: {
      ok: true,
      summary: "Preflight passed with warnings.",
      blocking_checks: [],
      warning_checks: [
        {
          error_leaf: "LABWARE_MISMATCH",
        },
      ],
    },
    hasFilePath: true,
  });

  assert.equal(report.overall_status, "warn");
  assert.ok(report.checks.some(check => check.name === "session_state" && check.status === "warn"));
  assert.ok(report.checks.some(check => check.name === "preflight_gate" && check.status === "warn"));
  assert.deepEqual(report.recommended_next_tools.slice(0, 4), [
    "safe_next_action",
    "run_history",
    "parse_error",
    "robot_status",
  ]);
});

test("live_readiness_check handler returns structured checks with mocked robot", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-live-readiness-"));
  const protocolPath = path.join(tempDir, "noop.py");
  const fakePython = path.join(tempDir, "python");
  fs.writeFileSync(
    protocolPath,
    [
      "from opentrons import protocol_api",
      "",
      'requirements = {"robotType": "Flex", "apiLevel": "2.24"}',
      "",
      "def run(protocol: protocol_api.ProtocolContext) -> None:",
      '    protocol.comment("noop")',
      "",
    ].join("\n"),
  );
  fs.writeFileSync(
    fakePython,
    [
      "#!/bin/sh",
      'case "$2" in',
      '  *"import sys; print(sys.version.split()[0])"*) echo "3.12.0" ;;',
      '  *"import opentrons; print(opentrons.__version__)"*) echo "9.9.9" ;;',
      "  *) exit 1 ;;",
      "esac",
      "",
    ].join("\n"),
  );
  fs.chmodSync(fakePython, 0o755);

  const originalFetch = global.fetch;
  global.fetch = async (url, options = {}) => {
    const requestUrl = new URL(url);
    const pathname = requestUrl.pathname;
    const method = options.method || "GET";

    if (method === "GET" && pathname === "/health") {
      return jsonResponse({ name: "Flex", robot_model: "OT-3 Standard", robot_serial: "FLX-1" });
    }
    if (method === "GET" && pathname === "/instruments") {
      return jsonResponse({
        data: [{ mount: "left", instrumentName: "p1000_single_flex", ok: true, state: { tipDetected: false } }],
      });
    }
    if (method === "GET" && pathname === "/robot/door/status") {
      return jsonResponse({ data: { status: "closed" } });
    }
    if (method === "GET" && pathname === "/robot/control/estopStatus") {
      return jsonResponse({ data: { status: "disengaged" } });
    }
    if (method === "GET" && pathname === "/deck_configuration") {
      return jsonResponse({ data: { cutoutFixtures: [] } });
    }
    if (method === "GET" && pathname === "/modules") {
      return jsonResponse({ data: [] });
    }
    if (method === "GET" && pathname === "/runs") {
      return jsonResponse({ data: [] });
    }

    throw new Error(`Unexpected request: ${method} ${requestUrl.toString()}`);
  };

  try {
    const result = await TOOL_HANDLERS.live_readiness_check({
      robot_ip: "10.31.2.149:31950",
      file_path: protocolPath,
      session_id: "readiness-test",
      python_executable: fakePython,
    });

    assert.ok(Array.isArray(result.data.checks));
    assert.ok(result.data.checks.some(check => check.name === "robot_connectivity"));
    assert.ok(result.data.checks.some(check => check.name === "preflight_gate"));
    assert.ok(result.data.checks.some(check => check.name === "local_runtime" && check.status === "pass"));
    assert.ok(Array.isArray(result.data.recommended_next_tools));
    assert.ok(result.data.safe_next_action);
  } finally {
    global.fetch = originalFetch;
  }
});
