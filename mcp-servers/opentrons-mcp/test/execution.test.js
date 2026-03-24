import test from "node:test";
import assert from "node:assert/strict";

import {
  CONTEXT_TYPES,
  buildCaptureImageCommand,
  buildCommandPayload,
  buildContextPaths,
  buildCreateRunContextRequest,
  buildHeaterShakerCommand,
  buildHomeCommand,
  buildLoadLabwareCommand,
  buildLoadModuleCommand,
  buildLoadPipetteCommand,
  buildMoveLabwareCommand,
  buildMoveToMaintenancePositionCommand,
  buildOpenGripperJawCommand,
  buildTemperatureModuleCommand,
  buildThermocyclerCommand,
  deriveCleanupPendingActions,
  isHeaterShakerLatchClosed,
  isTerminalCommandStatus,
  normalizeContextType,
  shouldPreflightCloseHeaterShakerLatch,
  shouldRetryHeaterShakerAfterLatchError,
} from "../lib/execution.js";

test("normalizeContextType prefers protocol when protocol id is present", () => {
  assert.equal(normalizeContextType(undefined, { protocolId: "protocol-1" }), CONTEXT_TYPES.PROTOCOL);
  assert.equal(normalizeContextType(undefined, {}), CONTEXT_TYPES.MAINTENANCE);
});

test("buildCreateRunContextRequest builds protocol payload", () => {
  const request = buildCreateRunContextRequest({
    contextType: "protocol",
    protocolId: "protocol-1",
    runTimeParameters: { cycles: 3 },
  });

  assert.equal(request.path, "/runs");
  assert.equal(request.body.data.protocolId, "protocol-1");
  assert.equal(request.body.data.runTimeParameterValues.cycles, 3);
});

test("buildCreateRunContextRequest builds maintenance payload", () => {
  const request = buildCreateRunContextRequest({
    contextType: "maintenance",
  });

  assert.equal(request.path, "/maintenance_runs");
  assert.deepEqual(request.body, { data: {} });
});

test("buildContextPaths returns run and maintenance endpoints", () => {
  const runPaths = buildContextPaths("protocol", "run-1");
  const maintenancePaths = buildContextPaths("maintenance", "maint-1");

  assert.equal(runPaths.commandsPath, "/runs/run-1/commands");
  assert.equal(maintenancePaths.commandsPath, "/maintenance_runs/maint-1/commands");
  assert.equal(runPaths.commandPath("cmd-1"), "/runs/run-1/commands/cmd-1");
});

test("buildLoadPipetteCommand matches API shape", () => {
  const payload = buildLoadPipetteCommand({
    pipetteName: "p1000_single_flex",
    mount: "left",
    liquidPresenceDetection: false,
  });

  assert.equal(payload.data.commandType, "loadPipette");
  assert.equal(payload.data.params.pipetteName, "p1000_single_flex");
  assert.equal(payload.data.params.mount, "left");
});

test("buildLoadLabwareCommand matches API shape", () => {
  const payload = buildLoadLabwareCommand({
    location: { slotName: "C2" },
    loadName: "opentrons_flex_96_tiprack_1000ul",
    namespace: "opentrons",
    version: 1,
  });

  assert.equal(payload.data.commandType, "loadLabware");
  assert.equal(payload.data.params.location.slotName, "C2");
});

test("buildLoadModuleCommand matches API shape", () => {
  const payload = buildLoadModuleCommand({
    model: "temperatureModuleV2",
    location: { slotName: "C1" },
  });

  assert.equal(payload.data.commandType, "loadModule");
  assert.equal(payload.data.params.model, "temperatureModuleV2");
  assert.equal(payload.data.params.location.slotName, "C1");
});

test("buildMoveLabwareCommand defaults to gripper strategy", () => {
  const payload = buildMoveLabwareCommand({
    labwareId: "labware-1",
    newLocation: { slotName: "C3" },
  });

  assert.equal(payload.data.commandType, "moveLabware");
  assert.equal(payload.data.params.strategy, "usingGripper");
});

test("module command builders match API shapes", () => {
  assert.equal(
    buildTemperatureModuleCommand({
      action: "set_target_temperature",
      moduleId: "temp-1",
      celsius: 37,
    }).data.commandType,
    "temperatureModule/setTargetTemperature",
  );
  assert.equal(
    buildHeaterShakerCommand({
      action: "set_shake_speed",
      moduleId: "hs-1",
      rpm: 300,
    }).data.params.rpm,
    300,
  );
  assert.equal(
    buildThermocyclerCommand({
      action: "set_block_temperature",
      moduleId: "tc-1",
      celsius: 95,
      holdTimeSeconds: 30,
    }).data.params.holdTimeSeconds,
    30,
  );
});

test("heater-shaker latch helpers capture preflight and retry cases", () => {
  assert.equal(isHeaterShakerLatchClosed("idle_closed"), true);
  assert.equal(isHeaterShakerLatchClosed("open"), false);
  assert.equal(
    shouldPreflightCloseHeaterShakerLatch({
      action: "deactivate_shaker",
      latchStatus: "open",
    }),
    true,
  );
  assert.equal(
    shouldPreflightCloseHeaterShakerLatch({
      action: "deactivate_shaker",
      latchStatus: "idle_closed",
    }),
    false,
  );
  assert.equal(
    shouldRetryHeaterShakerAfterLatchError(
      "CannotPerformModuleAction: labware latch has not been set to closed",
    ),
    true,
  );
});

test("buildCaptureImageCommand matches API shape", () => {
  const payload = buildCaptureImageCommand({
    fileName: "deck-shot.jpg",
    resolution: [1280, 720],
    zoom: 1.1,
  });

  assert.equal(payload.data.commandType, "captureImage");
  assert.deepEqual(payload.data.params.resolution, [1280, 720]);
  assert.equal(payload.data.params.fileName, "deck-shot.jpg");
});

test("cleanup and motion commands use verified command types", () => {
  assert.equal(buildOpenGripperJawCommand().data.commandType, "robot/openGripperJaw");
  assert.equal(
    buildMoveToMaintenancePositionCommand({ mount: "extension" }).data.commandType,
    "calibration/moveToMaintenancePosition",
  );
  assert.equal(buildHomeCommand().data.commandType, "home");
});

test("isTerminalCommandStatus recognizes only terminal states", () => {
  assert.equal(isTerminalCommandStatus("succeeded"), true);
  assert.equal(isTerminalCommandStatus("failed"), true);
  assert.equal(isTerminalCommandStatus("queued"), false);
});

test("deriveCleanupPendingActions tracks gripper cleanup chain", () => {
  assert.deepEqual(deriveCleanupPendingActions("moveLabware"), [
    "open_gripper_jaw",
    "move_to_maintenance_position",
  ]);
  assert.deepEqual(deriveCleanupPendingActions("calibration/moveToMaintenancePosition"), []);
  assert.equal(deriveCleanupPendingActions("loadLabware"), null);
});

test("buildCommandPayload enforces command type", () => {
  assert.throws(() => buildCommandPayload({}), /commandType is required/);
});
