import test from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import os from "os";
import path from "path";

import { TOOL_HANDLERS } from "../index.js";
import {
  extractDeclaredProtocolLoads,
  extractRobotTypeFromProtocolSource,
} from "../lib/protocol-deck.js";
import { buildPreflightRunSetupResult } from "../lib/preflight-run-setup.js";

test("extractRobotTypeFromProtocolSource reads requirements robotType", () => {
  const src = 'requirements = {"robotType": "Flex", "apiLevel": "2.16"}';
  assert.equal(extractRobotTypeFromProtocolSource(src), "Flex");
});

test("extractDeclaredProtocolLoads finds labware trash and module slots", () => {
  const src = `
    protocol.load_labware("nest_12_reservoir_15ml", "B3")
    protocol.load_trash_bin("A3")
    protocol.load_module(SomeModule, "D1")
  `;
  const loads = extractDeclaredProtocolLoads(src);
  const slots = new Set(loads.map(l => `${l.kind}:${l.slot}`));
  assert.ok(slots.has("labware:B3"));
  assert.ok(slots.has("trash_bin:A3"));
  assert.ok(slots.has("module:D1"));
});

test("buildPreflightRunSetupResult blocks when needs_reconciliation", () => {
  const result = buildPreflightRunSetupResult({
    filePath: null,
    sessionState: { needs_reconciliation: true },
    robotStatusSnapshot: { ready_for_physical_action: true, blockers: [] },
    moduleStatusSnapshot: { blockers: [] },
    skipDeckDiff: true,
  });
  assert.equal(result.ok, false);
  assert.ok(result.errors.some(e => e.code === "needs_reconciliation"));
});

test("preflight_run_setup handler returns ok with mocked robot", async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "preflight-"));
  const protocolPath = path.join(dir, "noop.py");
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

  const jsonResponse = (payload, status = 200) =>
    new Response(JSON.stringify(payload), {
      status,
      headers: { "content-type": "application/json" },
    });

  const originalFetch = global.fetch;
  global.fetch = async (url, options = {}) => {
    const requestUrl = new URL(url);
    const pathname = requestUrl.pathname;
    const method = options.method || "GET";

    if (method === "GET" && pathname === "/health") {
      return jsonResponse({ name: "Flex", robot_model: "OT-3 Standard", robot_serial: "FLX-1" });
    }
    if (method === "GET" && pathname === "/instruments") {
      return jsonResponse({ data: [{ mount: "left", instrumentName: "flex_1channel_1000", ok: true }] });
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
    const out = await TOOL_HANDLERS.preflight_run_setup({
      robot_ip: "10.31.2.149:31950",
      file_path: protocolPath,
      skip_deck_diff: true,
    });
    assert.equal(out.data.ok, true);
    assert.equal(out.data.allowed_to_play, true);
  } finally {
    global.fetch = originalFetch;
  }
});

test("buildPreflightRunSetupResult does not hard-block when deck configuration is empty", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "preflight-empty-deck-"));
  const protocolPath = path.join(dir, "protocol.py");
  fs.writeFileSync(
    protocolPath,
    [
      "from opentrons import protocol_api",
      "",
      'requirements = {"robotType": "Flex", "apiLevel": "2.24"}',
      "",
      "def run(protocol: protocol_api.ProtocolContext) -> None:",
      '    protocol.load_labware("nest_96_wellplate_200ul_flat", "B2")',
      "",
    ].join("\n"),
  );

  const result = buildPreflightRunSetupResult({
    filePath: protocolPath,
    sessionState: {},
    robotStatusSnapshot: {
      ready_for_physical_action: true,
      blockers: [],
      deck_configuration: { cutout_fixtures: [], raw: {} },
    },
    deckConfigurationPayload: { cutout_fixtures: [], raw: {} },
    moduleStatusSnapshot: { blockers: [] },
    skipDeckDiff: false,
  });

  assert.equal(result.ok, true);
  assert.equal(result.allowed_to_play, true);
  assert.ok(result.warnings.some(w => w.code === "labware_placement_unknown"));
});

test("buildPreflightRunSetupResult hard-blocks unknown labware placement in strict mode", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "preflight-strict-unknown-"));
  const protocolPath = path.join(dir, "protocol.py");
  fs.writeFileSync(
    protocolPath,
    [
      "from opentrons import protocol_api",
      "",
      'requirements = {"robotType": "Flex", "apiLevel": "2.24"}',
      "",
      "def run(protocol: protocol_api.ProtocolContext) -> None:",
      '    protocol.load_labware("nest_96_wellplate_200ul_flat", "B2")',
      "",
    ].join("\n"),
  );

  const result = buildPreflightRunSetupResult({
    filePath: protocolPath,
    sessionState: {},
    robotStatusSnapshot: {
      ready_for_physical_action: true,
      blockers: [],
      deck_configuration: { cutout_fixtures: [], raw: {} },
    },
    deckConfigurationPayload: { cutout_fixtures: [], raw: {} },
    moduleStatusSnapshot: { blockers: [] },
    skipDeckDiff: false,
    strictEmptyLabwareSlots: true,
  });

  assert.equal(result.ok, false);
  assert.equal(result.allowed_to_play, false);
  assert.ok(result.errors.some(e => e.code === "labware_placement_unknown"));
  assert.equal(result.warnings.some(w => w.code === "labware_placement_unknown"), false);
});
