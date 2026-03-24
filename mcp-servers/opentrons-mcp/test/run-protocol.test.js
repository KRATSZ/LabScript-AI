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

test("run_protocol uploads, plays, and returns final run snapshot", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-run-"));
  const protocolPath = path.join(tempDir, "noop_protocol.py");
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
      timeout_ms: 10,
      poll_interval_ms: 1,
    });

    assert.equal(result.runId, "run-1");
    assert.equal(result.data.final_status, "succeeded");
    assert.equal(result.data.requires_attention, false);
    assert.equal(result.data.final_run_history.run_id, "run-1");
    assert.equal(result.hardwareSnapshot.run.data.id, "run-1");
    assert.equal(result.hardwareSnapshot.health.robot_serial, "FLX-1");
  } finally {
    global.fetch = originalFetch;
  }
});
