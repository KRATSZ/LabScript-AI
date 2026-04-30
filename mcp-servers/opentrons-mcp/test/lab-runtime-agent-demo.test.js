import test from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import os from "os";
import path from "path";

import { loadExperienceStore, runRuntimeAgentDemo } from "../scripts/lab-runtime-agent-demo.mjs";

function makeTempArtifactRoot(name) {
  return fs.mkdtempSync(path.join(os.tmpdir(), `${name}-`));
}

test("missing-tip demo marks A1 unavailable and selects the next candidate tip", async () => {
  const artifactRoot = makeTempArtifactRoot("lab-runtime-missing-tip");

  const result = await runRuntimeAgentDemo({
    scenario: "missing-tip",
    mode: "mock",
    artifactRoot,
    now: new Date("2026-04-30T00:00:00.000Z"),
  });

  assert.equal(result.runtime_state.outcome, "recovered");
  assert.equal(result.next_tip.tiprack_slot, "C2");
  assert.equal(result.next_tip.well_name, "B1");
  assert.deepEqual(
    result.runtime_state.committed_state.tip_tracking.tipracks.C2.missing_wells,
    ["A1"],
  );
  assert.equal(fs.existsSync(result.artifacts.event_log_path), true);
  assert.equal(fs.existsSync(result.artifacts.state_trace_path), true);

  const store = loadExperienceStore(artifactRoot);
  assert.deepEqual(store.policies.missing_tip.C2.avoid_wells, ["A1"]);
});

test("occupied-destination live demo blocks gripper motion without confirmation and context", async () => {
  const artifactRoot = makeTempArtifactRoot("lab-runtime-occupied");
  const fakeTools = {
    move_labware() {
      throw new Error("move_labware should not be called without confirmation and context");
    },
  };

  const result = await runRuntimeAgentDemo({
    scenario: "occupied-destination",
    mode: "live",
    robotIp: "192.168.66.103",
    confirmLive: false,
    artifactRoot,
    toolHandlers: fakeTools,
    now: new Date("2026-04-30T00:01:00.000Z"),
  });

  assert.equal(result.runtime_state.outcome, "blocked");
  assert.equal(result.execution_result.executed, false);
  assert.equal(result.runtime_state.risk_state.requires_human_confirmation, true);
  assert.equal(result.runtime_state.risk_state.reason, "gripper_move_requires_confirm_live_and_context_id");
  assert.equal(result.slot_occupation.status, "occupied");
});

test("liquid-sensing mock demo records measured height and adjusted aspiration plan", async () => {
  const artifactRoot = makeTempArtifactRoot("lab-runtime-liquid");

  const result = await runRuntimeAgentDemo({
    scenario: "liquid-sensing",
    mode: "mock",
    artifactRoot,
    mockLiquidHeightMm: 6.2,
    now: new Date("2026-04-30T00:02:00.000Z"),
  });

  const liquidState = result.runtime_state.observed_state.liquid_sensor["B3.A1"];
  assert.equal(result.runtime_state.outcome, "replanned");
  assert.equal(liquidState.status, "present");
  assert.equal(liquidState.height_mm, 6.2);
  assert.equal(result.adjusted_plan.aspirate_depth_mm, 5.2);
  assert.match(fs.readFileSync(result.artifacts.summary_path, "utf8"), /6\.2/);
});

test("self-evolution demo reuses experience to preblock the failed tip well", async () => {
  const artifactRoot = makeTempArtifactRoot("lab-runtime-self-evolution");

  const result = await runRuntimeAgentDemo({
    scenario: "self-evolution",
    mode: "mock",
    artifactRoot,
    now: new Date("2026-04-30T00:03:00.000Z"),
  });

  assert.equal(result.runtime_state.outcome, "improved");
  assert.deepEqual(result.second_episode.avoided_wells, ["A1"]);
  assert.equal(result.second_episode.selected_tip.tiprack_slot, "C2");
  assert.equal(result.second_episode.selected_tip.well_name, "B1");
  assert.deepEqual(
    result.runtime_state.committed_state.tip_tracking.tipracks.C2.missing_wells,
    ["A1"],
  );

  const store = loadExperienceStore(artifactRoot);
  assert.equal(store.cases.length, 1);
  assert.deepEqual(store.policies.missing_tip.C2.avoid_wells, ["A1"]);
});
