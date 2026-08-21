import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { buildPreflightRunSetupResult } from "./preflight-run-setup.js";

const FLEX_PROTOCOL = `
from opentrons import protocol_api
metadata = {"protocolName": "preflight fixture"}
requirements = {"robotType": "Flex", "apiLevel": "2.24"}
def run(protocol: protocol_api.ProtocolContext) -> None:
    protocol.load_trash_bin("A3")
    protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "B2")
    protocol.load_labware("nest_96_wellplate_200ul_flat", "C2")
`;

function writeProtocol() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "preflight-gate-"));
  const filePath = path.join(dir, "fixture.py");
  fs.writeFileSync(filePath, FLEX_PROTOCOL);
  return { dir, filePath };
}

function robotReady() {
  return {
    health_summary: { robot_model: "OT-3 Standard" },
    ready_for_physical_action: true,
    blockers: [],
  };
}

test("module_blockers_present stays a warning by default (published-number behaviour)", () => {
  const { dir, filePath } = writeProtocol();
  try {
    const result = buildPreflightRunSetupResult({
      filePath,
      robotStatusSnapshot: robotReady(),
      moduleStatusSnapshot: { blockers: ["heaterShakerLatchOpen"] },
      skipDeckDiff: true,
    });
    assert.equal(result.allowed_to_play, true);
    assert.equal(result.ok, true);
    assert.equal(result.errors.some(e => e.code === "module_blockers_present"), false);
    assert.equal(result.warnings.some(w => w.code === "module_blockers_present"), true);
    const warn = result.warning_checks.find(c => c.code === "module_blockers_present");
    assert.equal(warn.status, "warn");
    assert.equal(warn.error_leaf, "MODULE_NOT_READY");
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test("strictModuleBlockers promotes module_blockers_present to a blocking error", () => {
  const { dir, filePath } = writeProtocol();
  try {
    const result = buildPreflightRunSetupResult({
      filePath,
      robotStatusSnapshot: robotReady(),
      moduleStatusSnapshot: { blockers: ["heaterShakerLatchOpen"] },
      skipDeckDiff: true,
      strictModuleBlockers: true,
    });
    assert.equal(result.allowed_to_play, false);
    assert.equal(result.ok, false);
    assert.equal(result.errors.some(e => e.code === "module_blockers_present"), true);
    const fail = result.blocking_checks.find(c => c.code === "module_blockers_present");
    assert.equal(fail.status, "fail");
    assert.equal(fail.error_leaf, "MODULE_NOT_READY");
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test("offset coverage is skipped when labwareOffsets is omitted (backward compatible)", () => {
  const { dir, filePath } = writeProtocol();
  try {
    const result = buildPreflightRunSetupResult({
      filePath,
      robotStatusSnapshot: robotReady(),
      skipDeckDiff: true,
    });
    assert.equal(result.errors.some(e => String(e.code || "").startsWith("offset_")), false);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test("offset coverage blocks play when a declared labware has no stored offset", () => {
  const { dir, filePath } = writeProtocol();
  try {
    const result = buildPreflightRunSetupResult({
      filePath,
      robotStatusSnapshot: robotReady(),
      labwareOffsets: [],
      offsetMaxAgeDays: 30,
    });
    assert.equal(result.allowed_to_play, false);
    const codes = result.errors.map(e => e.code);
    assert.equal(codes.includes("offset_missing"), true);
    const check = result.blocking_checks.find(c => c.code === "offset_missing");
    assert.equal(check.status, "fail");
    assert.equal(check.error_leaf, "STALE_LABWARE_OFFSET");
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test("offset coverage blocks stale slot-matched offsets using the explicit threshold", () => {
  const { dir, filePath } = writeProtocol();
  try {
    const result = buildPreflightRunSetupResult({
      filePath,
      robotStatusSnapshot: robotReady(),
      offsetMaxAgeDays: 30,
      labwareOffsets: [
        {
          id: "tip",
          createdAt: "2026-08-17T08:33:58.669Z",
          definitionUri: "opentrons/opentrons_flex_96_tiprack_1000ul/1",
          locationSequence: [{ kind: "onAddressableArea", addressableAreaName: "B2" }],
          vector: { x: 0.25, y: -0.1, z: 0.4 },
        },
        {
          id: "plate-stale",
          createdAt: "2026-06-09T07:40:47.905Z",
          definitionUri: "opentrons/nest_96_wellplate_200ul_flat/3",
          locationSequence: [{ kind: "onAddressableArea", addressableAreaName: "C2" }],
          vector: { x: 0, y: 0, z: 5 },
        },
      ],
    });
    assert.equal(result.allowed_to_play, false);
    const stale = result.errors.find(e => e.code === "offset_stale");
    assert.ok(stale);
    assert.equal(stale.max_age_days, 30);
    assert.equal(stale.load_name, "nest_96_wellplate_200ul_flat");
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
