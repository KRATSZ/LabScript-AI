import test from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import os from "os";
import path from "path";

import { TOOL_HANDLERS } from "../index.js";
import { buildProbeWellsProtocol, extractProbeResultsFromCommands } from "../lib/probe.js";

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

test("buildProbeWellsProtocol renders measure_liquid_height workflow", () => {
  const protocol = buildProbeWellsProtocol({
    pipetteName: "flex_1channel_1000",
    mount: "left",
    tiprackLoadName: "opentrons_flex_96_tiprack_1000ul",
    tiprackSlot: "D1",
    labwareLoadName: "nest_12_reservoir_15ml",
    labwareSlot: "C1",
    wells: ["A1", "A2"],
    mode: "measure_height",
  });

  assert.match(protocol, /measure_liquid_height/);
  assert.match(protocol, /PROBE_RESULT:/);
  assert.match(protocol, /liquid_presence_detection=True/);
});

test("extractProbeResultsFromCommands reads comment payloads", () => {
  const results = extractProbeResultsFromCommands({
    data: [
      {
        commandType: "comment",
        params: {
          message: 'PROBE_RESULT:{"well":"A1","mode":"detect_presence","success":true,"value":true}',
        },
      },
      {
        commandType: "comment",
        params: {
          message: 'PROBE_RESULT:{"well":"A2","mode":"measure_height","success":true,"value":12.4}',
        },
      },
    ],
  });

  assert.equal(results.length, 2);
  assert.equal(results[0].well, "A1");
  assert.equal(results[1].value, 12.4);
});

test("probe_wells generates a protocol and simulates locally by default", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-probe-"));
  const fakeRunnerPath = createFakeSimulationRunner(tempDir, { simulatePass: true });

  const result = await TOOL_HANDLERS.probe_wells({
    pipette_name: "flex_1channel_1000",
    mount: "left",
    tiprack_load_name: "opentrons_flex_96_tiprack_1000ul",
    tiprack_slot: "D1",
    labware_load_name: "nest_12_reservoir_15ml",
    labware_slot: "C1",
    wells: ["A1", "A2"],
    mode: "detect_presence",
    output_path: path.join(tempDir, "probe_protocol.py"),
    python_executable: fakeRunnerPath,
  });

  assert.equal(result.data.execute_on_robot, false);
  assert.equal(result.data.parsed_simulation_output.success, true);
  assert.equal(fs.existsSync(result.data.generated_protocol_path), true);
});

test("probe_wells refuses live execution unless explicitly enabled", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-probe-live-"));
  const fakeRunnerPath = createFakeSimulationRunner(tempDir, { simulatePass: true });
  const originalFlag = process.env.OPENTRONS_ENABLE_PROBE_WELLS;

  delete process.env.OPENTRONS_ENABLE_PROBE_WELLS;
  try {
    await assert.rejects(
      () =>
        TOOL_HANDLERS.probe_wells({
          pipette_name: "flex_1channel_1000",
          mount: "left",
          tiprack_load_name: "opentrons_flex_96_tiprack_1000ul",
          tiprack_slot: "D1",
          labware_load_name: "nest_12_reservoir_15ml",
          labware_slot: "C1",
          wells: ["A1"],
          mode: "detect_presence",
          output_path: path.join(tempDir, "probe_protocol.py"),
          python_executable: fakeRunnerPath,
          execute_on_robot: true,
          robot_ip: "10.31.2.149:31950",
        }),
      /Live probe_wells execution is disabled by default/,
    );
  } finally {
    if (originalFlag === undefined) {
      delete process.env.OPENTRONS_ENABLE_PROBE_WELLS;
    } else {
      process.env.OPENTRONS_ENABLE_PROBE_WELLS = originalFlag;
    }
  }
});

test("probe_wells executes the live branch when enabled", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-probe-live-"));
  const fakeRunnerPath = createFakeSimulationRunner(tempDir, { simulatePass: true });
  const originalFlag = process.env.OPENTRONS_ENABLE_PROBE_WELLS;
  const originalRunProtocol = TOOL_HANDLERS.run_protocol;
  const originalFetch = global.fetch;

  process.env.OPENTRONS_ENABLE_PROBE_WELLS = "1";
  TOOL_HANDLERS.run_protocol = async () => ({
    data: { final_status: "succeeded" },
    hardwareSnapshot: { robot: "snapshot" },
    stateRevision: 7,
    sessionId: "probe-session",
    runId: "run-1",
  });
  global.fetch = async (url, options = {}) => {
    const requestUrl = new URL(url);
    const method = options.method || "GET";

    if (method === "GET" && requestUrl.pathname === "/runs/run-1/commands") {
      return jsonResponse({
        data: [
          {
            commandType: "comment",
            params: {
              message:
                'PROBE_RESULT:{"well":"A1","mode":"detect_presence","success":true,"value":true}',
            },
          },
        ],
      });
    }

    throw new Error(`Unexpected request: ${method} ${requestUrl.toString()}`);
  };

  try {
    const result = await TOOL_HANDLERS.probe_wells({
      pipette_name: "flex_1channel_1000",
      mount: "left",
      tiprack_load_name: "opentrons_flex_96_tiprack_1000ul",
      tiprack_slot: "D1",
      labware_load_name: "nest_12_reservoir_15ml",
      labware_slot: "C1",
      wells: ["A1"],
      mode: "detect_presence",
      output_path: path.join(tempDir, "probe_protocol.py"),
      python_executable: fakeRunnerPath,
      execute_on_robot: true,
      robot_ip: "10.31.2.149:31950",
    });

    assert.equal(result.data.execute_on_robot, true);
    assert.equal(result.data.run_protocol.final_status, "succeeded");
    assert.equal(result.data.probe_results.length, 1);
    assert.equal(result.data.probe_results[0].well, "A1");
    assert.equal(result.sessionId, "probe-session");
    assert.equal(result.runId, "run-1");
  } finally {
    TOOL_HANDLERS.run_protocol = originalRunProtocol;
    global.fetch = originalFetch;
    if (originalFlag === undefined) {
      delete process.env.OPENTRONS_ENABLE_PROBE_WELLS;
    } else {
      process.env.OPENTRONS_ENABLE_PROBE_WELLS = originalFlag;
    }
  }
});
