import test from "node:test";
import assert from "node:assert/strict";

import {
  buildModuleStatusSnapshot,
  buildRobotStatusSnapshot,
  buildRunHistorySnapshot,
} from "../lib/live-state.js";

test("buildRobotStatusSnapshot derives blockers and readiness", () => {
  const snapshot = buildRobotStatusSnapshot({
    health: { name: "Flex", api_version: "4", robot_model: "Flex" },
    instruments: {
      data: [{ mount: "left", instrumentName: "flex_1channel_50", ok: true }],
    },
    doorStatus: { data: { status: "closed" } },
    estopStatus: { data: { status: "disengaged" } },
    deckConfiguration: { data: { cutoutFixtures: [] } },
  });

  assert.equal(snapshot.ready_for_physical_action, true);
  assert.equal(snapshot.blockers.length, 0);
  assert.equal(snapshot.instruments_summary[0].instrument_name, "flex_1channel_50");
});

test("buildModuleStatusSnapshot flags modules that are not ready", () => {
  const snapshot = buildModuleStatusSnapshot({
    data: [
      {
        id: "tempmod-1",
        moduleModel: "temperatureModuleV2",
        location: { slotName: "D1" },
        currentTemperature: 25,
        targetTemperature: 37,
        status: "heating",
      },
    ],
  });

  assert.equal(snapshot.module_count, 1);
  assert.equal(snapshot.modules[0].ready, false);
  assert.equal(snapshot.blockers[0], "module_not_ready:tempmod-1");
});

test("buildRobotStatusSnapshot reads real instrument tipDetected shape", () => {
  const snapshot = buildRobotStatusSnapshot({
    health: { name: "Flex", api_version: "8.8.1", robot_model: "OT-3 Standard" },
    instruments: {
      data: [
        {
          mount: "left",
          instrumentName: "p1000_single_flex",
          ok: true,
          state: { tipDetected: true },
        },
      ],
    },
    doorStatus: { data: { status: "closed" } },
    estopStatus: { data: { status: "disengaged" } },
    deckConfiguration: { data: { cutoutFixtures: [] } },
  });

  assert.equal(snapshot.instruments_summary[0].tip_detected, true);
});

test("buildModuleStatusSnapshot reads real moduleOffset slot", () => {
  const snapshot = buildModuleStatusSnapshot({
    data: [
      {
        id: "thermocycler-1",
        moduleModel: "thermocyclerModuleV2",
        moduleOffset: { slot: "B1" },
        data: {
          status: "holding at target",
          currentTemperature: 95.02,
          targetTemperature: 95.0,
        },
      },
    ],
  });

  assert.equal(snapshot.modules[0].slot, "B1");
  assert.equal(snapshot.modules[0].ready, true);
});

test("buildRunHistorySnapshot summarizes failed commands and recovery", () => {
  const snapshot = buildRunHistorySnapshot(
    {
      data: {
        id: "run-123",
        protocolId: "protocol-1",
        status: "awaiting-recovery",
        currentlyRecoveringFrom: "command-2",
        commandErrors: [{ id: "err-1", detail: "No Tip Detected" }],
      },
    },
    {
      data: [
        { id: "command-1", commandType: "pickUpTip", status: "succeeded" },
        {
          id: "command-2",
          commandType: "pickUpTip",
          status: "failed",
          error: { detail: "No Tip Detected" },
        },
      ],
    },
  );

  assert.equal(snapshot.awaiting_recovery, true);
  assert.equal(snapshot.command_counts.failed, 1);
  assert.equal(snapshot.latest_failed_command.id, "command-2");
  assert.equal(snapshot.command_errors[0].detail, "No Tip Detected");
});

test("buildRunHistorySnapshot reads live run errors array", () => {
  const snapshot = buildRunHistorySnapshot(
    {
      data: {
        id: "run-live-1",
        protocolId: "protocol-live-1",
        status: "failed",
        errors: [{ id: "err-live-1", detail: "No trash container has been defined" }],
      },
    },
    {
      data: [],
    },
  );

  assert.equal(snapshot.command_errors[0].detail, "No trash container has been defined");
});
