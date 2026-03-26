import test from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import os from "os";
import path from "path";

import { TOOL_HANDLERS } from "../index.js";

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json",
    },
  });
}

function createFakeSimulationRunner(tempDir, { simulatePass = true } = {}) {
  const runnerPath = path.join(tempDir, "fake-simulation-runner.py");
  const script = [
    "#!/usr/bin/env python3",
    "import json",
    "import sys",
    "",
    "command = sys.argv[2] if len(sys.argv) > 2 else ''",
    "protocol = sys.argv[-1] if command == 'simulate' and len(sys.argv) > 3 else None",
    "",
    "if command == 'doctor':",
    "    print(json.dumps({",
    "        'ok': True,",
    "        'python': sys.argv[0],",
    "        'workspace_root': None,",
    "        'api_root': None,",
    "        'shared_data_root': None,",
    "        'source_layout_ready': False,",
    "        'opentrons_simulate': {'ok': True, 'module': 'opentrons.simulate'}",
    "    }))",
    simulatePass
      ? [
          "elif command == 'simulate':",
          "    print(json.dumps({",
          "        'ok': True,",
          "        'python': sys.argv[0],",
          "        'module': 'opentrons.simulate',",
          "        'protocol': protocol,",
          "        'workspace_root': None,",
          "        'api_root': None,",
          "        'shared_data_root': None,",
          "        'source_layout_ready': False,",
          "        'exit_code': 0,",
          "        'stdout': '',",
          "        'stderr': '',",
          "        'error': None",
          "    }))",
        ].join("\n")
      : [
          "elif command == 'simulate':",
          "    print(json.dumps({",
          "        'ok': False,",
          "        'python': sys.argv[0],",
          "        'module': 'opentrons.simulate',",
          "        'protocol': protocol,",
          "        'workspace_root': None,",
          "        'api_root': None,",
          "        'shared_data_root': None,",
          "        'source_layout_ready': False,",
          "        'exit_code': 1,",
          "        'stdout': '',",
          "        'stderr': 'SyntaxError: invalid syntax\\n',",
          "        'error': {'error_type': 'SyntaxError', 'error': 'invalid syntax'}",
          "    }))",
        ].join("\n"),
    "else:",
    "    raise SystemExit(f'unsupported command: {command}')",
    "",
  ].join("\n");

  fs.writeFileSync(runnerPath, script);
  fs.chmodSync(runnerPath, 0o755);
  return runnerPath;
}

function installSuccessfulRunFetch() {
  global.fetch = async (url, options = {}) => {
    const requestUrl = new URL(url);
    const pathname = requestUrl.pathname;
    const method = options.method || "GET";

    if (method === "POST" && pathname === "/protocols") {
      return jsonResponse({ data: { id: "protocol-1", files: [] } });
    }
    if (method === "POST" && pathname === "/runs") {
      return jsonResponse({ data: { id: "run-1", status: "idle" } });
    }
    if (method === "POST" && pathname === "/runs/run-1/actions") {
      return jsonResponse({ data: { id: "action-1", actionType: "play" } });
    }
    if (method === "GET" && pathname === "/runs/run-1") {
      return jsonResponse({ data: { id: "run-1", protocolId: "protocol-1", status: "succeeded" } });
    }
    if (method === "GET" && pathname === "/runs/run-1/commands") {
      return jsonResponse({
        data: [{ id: "cmd-1", commandType: "comment", status: "succeeded" }],
      });
    }
    if (method === "GET" && pathname === "/health") {
      return jsonResponse({ name: "Flex", robot_model: "OT-3 Standard", robot_serial: "FLX-1" });
    }
    if (method === "GET" && pathname === "/instruments") {
      return jsonResponse({
        data: [{ mount: "left", instrumentName: "p1000_single_flex", ok: true }],
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

    throw new Error(`Unexpected request: ${method} ${requestUrl.toString()}`);
  };
}

test("experiment_history returns persisted run_protocol results", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-history-"));
  const protocolPath = path.join(tempDir, "noop_protocol.py");
  const fakeRunnerPath = createFakeSimulationRunner(tempDir, { simulatePass: true });
  const logDir = path.join(tempDir, "result-logs");
  const originalFetch = global.fetch;
  const originalLogDir = process.env.OPENTRONS_RESULT_LOG_DIR;
  process.env.OPENTRONS_RESULT_LOG_DIR = logDir;
  fs.writeFileSync(
    protocolPath,
    [
      "from opentrons import protocol_api",
      "",
      'metadata = {"protocolName": "Noop"}',
      'requirements = {"robotType": "Flex", "apiLevel": "2.22"}',
      "",
      "def run(protocol: protocol_api.ProtocolContext) -> None:",
      '    protocol.comment("noop")',
      "",
    ].join("\n"),
  );
  installSuccessfulRunFetch();

  try {
    await TOOL_HANDLERS.run_protocol({
      robot_ip: "10.31.2.149:31950",
      file_path: protocolPath,
      python_executable: fakeRunnerPath,
      session_id: "history-session",
      timeout_ms: 10,
      poll_interval_ms: 1,
    });

    const history = await TOOL_HANDLERS.experiment_history({
      session_id: "history-session",
      tool_name: "run_protocol",
    });

    assert.equal(history.data.entries.length, 1);
    assert.equal(history.data.entries[0].status, "succeeded");
    assert.equal(history.data.entries[0].tool_name, "run_protocol");
    assert.equal(history.data.entries[0].protocol_name, "noop_protocol.py");
    assert.equal(history.data.summary.total, 1);
  } finally {
    global.fetch = originalFetch;
    if (originalLogDir === undefined) {
      delete process.env.OPENTRONS_RESULT_LOG_DIR;
    } else {
      process.env.OPENTRONS_RESULT_LOG_DIR = originalLogDir;
    }
  }
});

test("run_protocol writes blocked history when simulation gate fails", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-history-blocked-"));
  const protocolPath = path.join(tempDir, "broken_protocol.py");
  const fakeRunnerPath = createFakeSimulationRunner(tempDir, { simulatePass: false });
  const logDir = path.join(tempDir, "result-logs");
  const originalFetch = global.fetch;
  const originalLogDir = process.env.OPENTRONS_RESULT_LOG_DIR;
  process.env.OPENTRONS_RESULT_LOG_DIR = logDir;
  let fetchCalled = false;
  fs.writeFileSync(
    protocolPath,
    [
      "from opentrons import protocol_api",
      "",
      'metadata = {"protocolName": "Broken"}',
      'requirements = {"robotType": "Flex", "apiLevel": "2.22"}',
      "",
      "def run(protocol: protocol_api.ProtocolContext) -> None:",
      "    pipette.pick_up_tip(",
      "",
    ].join("\n"),
  );
  global.fetch = async () => {
    fetchCalled = true;
    throw new Error("fetch should not be called when simulation gate fails");
  };

  try {
    await assert.rejects(
      () =>
        TOOL_HANDLERS.run_protocol({
          robot_ip: "10.31.2.149:31950",
          file_path: protocolPath,
          python_executable: fakeRunnerPath,
          session_id: "blocked-session",
          timeout_ms: 10,
          poll_interval_ms: 1,
        }),
      /Simulation gate blocked real execution/,
    );
    assert.equal(fetchCalled, false);

    const history = await TOOL_HANDLERS.experiment_history({
      session_id: "blocked-session",
      status: "blocked",
    });

    assert.equal(history.data.entries.length, 1);
    assert.equal(history.data.entries[0].tool_name, "run_protocol");
    assert.equal(history.data.entries[0].data.blocked_real_execution, true);
    assert.equal(history.data.entries[0].data.gate_stage, "simulate_protocol");
  } finally {
    global.fetch = originalFetch;
    if (originalLogDir === undefined) {
      delete process.env.OPENTRONS_RESULT_LOG_DIR;
    } else {
      process.env.OPENTRONS_RESULT_LOG_DIR = originalLogDir;
    }
  }
});
