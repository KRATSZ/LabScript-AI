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

test("run_protocol uploads, plays, and returns final run snapshot", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-run-"));
  const protocolPath = path.join(tempDir, "noop_protocol.py");
  const fakeRunnerPath = createFakeSimulationRunner(tempDir, { simulatePass: true });
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

  const originalFetch = global.fetch;
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
    if (method === "GET" && pathname === "/runs/run-1") {
      return jsonResponse({
        data: { id: "run-1", protocolId: "protocol-1", status: "succeeded", labware: [] },
      });
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

  try {
    const result = await TOOL_HANDLERS.run_protocol({
      robot_ip: "10.31.2.149:31950",
      file_path: protocolPath,
      python_executable: fakeRunnerPath,
      timeout_ms: 10,
      poll_interval_ms: 1,
    });

    assert.equal(result.runId, "run-1");
    assert.equal(result.data.final_status, "succeeded");
    assert.equal(result.data.requires_attention, false);
    assert.equal(result.data.simulation_gate.parsed.success, true);
    assert.equal(result.data.preflight_gate?.ok, true);
    assert.equal(result.data.final_run_history.run_id, "run-1");
    assert.equal(result.hardwareSnapshot.run.data.id, "run-1");
    assert.equal(result.hardwareSnapshot.health.robot_serial, "FLX-1");
  } finally {
    global.fetch = originalFetch;
  }
});

test("run_protocol blocks real execution when simulation fails", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-run-fail-"));
  const protocolPath = path.join(tempDir, "broken_protocol.py");
  const fakeRunnerPath = createFakeSimulationRunner(tempDir, { simulatePass: false });
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

  const originalFetch = global.fetch;
  let fetchCalled = false;
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
          timeout_ms: 10,
          poll_interval_ms: 1,
        }),
      /Simulation gate blocked real execution/,
    );
    assert.equal(fetchCalled, false);
  } finally {
    global.fetch = originalFetch;
  }
});
