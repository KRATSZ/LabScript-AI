import test from "node:test";
import assert from "node:assert/strict";

import { TOOL_HANDLERS } from "../index.js";

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json",
    },
  });
}

function installCommonRecoveryFetch({
  commands,
  modules = [],
  labware = [],
  onPostCommand,
  onRunAction,
} = {}) {
  let resumed = false;
  let commandStatusReads = 0;
  const postedCommands = [];

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
      return jsonResponse({
        data: {
          cutoutFixtures: [
            { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutB2" },
            { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutC2" },
            { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutD2" },
            { cutoutFixtureId: "trashBinAdapter", cutoutId: "cutoutA3" },
          ],
        },
      });
    }
    if (method === "GET" && pathname === "/modules") {
      return jsonResponse({ data: resumed ? [] : modules });
    }
    if (method === "GET" && pathname === "/runs/run-1") {
      return jsonResponse({
        data: {
          id: "run-1",
          protocolId: "protocol-1",
          status: resumed ? "succeeded" : "awaiting-recovery",
          currentlyRecoveringFrom: resumed ? null : "cmd-failed",
          hasEverEnteredErrorRecovery: true,
          labware,
        },
      });
    }
    if (method === "GET" && pathname === "/runs/run-1/commands") {
      return jsonResponse({ data: commands });
    }
    if (method === "POST" && pathname === "/runs/run-1/commands") {
      const payload = JSON.parse(options.body);
      postedCommands.push(payload);
      onPostCommand?.(payload);
      return jsonResponse({ data: { id: "cmd-fixit", status: "queued" } });
    }
    if (method === "GET" && pathname === "/runs/run-1/commands/cmd-fixit") {
      commandStatusReads += 1;
      const lastPosted = postedCommands.at(-1);
      return jsonResponse({
        data: {
          id: "cmd-fixit",
          commandType: lastPosted?.data?.commandType || "pickUpTip",
          status: commandStatusReads > 1 ? "succeeded" : "running",
          params: lastPosted?.data?.params || {},
          intent: lastPosted?.data?.intent || null,
        },
      });
    }
    if (method === "POST" && pathname === "/runs/run-1/actions") {
      const payload = JSON.parse(options.body);
      assert.equal(payload.data.actionType, "resume-from-recovery");
      resumed = true;
      onRunAction?.(payload);
      return jsonResponse({ data: { id: "action-resume", actionType: "resume-from-recovery" } });
    }

    throw new Error(`Unexpected request: ${method} ${requestUrl.toString()}`);
  };
}

test("execute_protocol_recovery retries pickUpTip with fixit and resumes the run", async () => {
  const originalFetch = global.fetch;
  installCommonRecoveryFetch({
    commands: [
      {
        id: "cmd-failed",
        commandType: "pickUpTip",
        status: "failed",
        params: {
          pipetteId: "pipette-left-1",
          labwareId: "tiprack-1",
          wellName: "A1",
        },
        error: {
          errorType: "tipPhysicallyMissing",
          detail: "No Tip Detected",
        },
      },
      {
        id: "cmd-drop",
        commandType: "dropTipInPlace",
        status: "succeeded",
        params: {},
      },
    ],
    labware: [
      {
        id: "tiprack-1",
        loadName: "opentrons_flex_96_tiprack_1000ul",
        location: { slotName: "C2" },
      },
    ],
    onPostCommand(payload) {
      assert.equal(payload.data.commandType, "pickUpTip");
      assert.equal(payload.data.intent, "fixit");
      assert.equal(payload.data.params.pipetteId, "pipette-left-1");
      assert.equal(payload.data.params.labwareId, "tiprack-1");
      assert.equal(payload.data.params.wellName, "B1");
    },
  });

  try {
    const result = await TOOL_HANDLERS.execute_protocol_recovery({
      robot_ip: "10.31.2.149:31950",
      run_id: "run-1",
      session_id: "recover-tip-test",
      tiprack_slots: ["C2"],
      timeout_ms: 10,
      poll_interval_ms: 1,
    });

    assert.equal(result.data.executed_action, "retry_pick_up_tip_with_next_candidate");
    assert.equal(result.data.executed_params.well, "B1");
    assert.equal(result.data.final_run_history.status, "succeeded");
    assert.equal(result.data.resume_action.data.actionType, "resume-from-recovery");
    assert.equal(result.runId, "run-1");
  } finally {
    global.fetch = originalFetch;
  }
});

test("execute_protocol_recovery can reissue moveLabware to a chosen alternative slot", async () => {
  const originalFetch = global.fetch;
  installCommonRecoveryFetch({
    commands: [
      {
        id: "cmd-failed",
        commandType: "moveLabware",
        status: "failed",
        params: {
          labwareId: "plate-1",
          newLocation: { slotName: "B1" },
          strategy: "usingGripper",
        },
        error: {
          errorType: "LocationIsOccupiedError",
          detail: "LocationIsOccupiedError: destination occupied",
        },
      },
    ],
    labware: [
      {
        id: "plate-1",
        loadName: "corning_96_wellplate_360ul_flat",
        location: { slotName: "C3" },
      },
    ],
    onPostCommand(payload) {
      assert.equal(payload.data.commandType, "moveLabware");
      assert.equal(payload.data.intent, "fixit");
      assert.equal(payload.data.params.labwareId, "plate-1");
      assert.equal(payload.data.params.newLocation.slotName, "D2");
    },
  });

  try {
    const result = await TOOL_HANDLERS.execute_protocol_recovery({
      robot_ip: "10.31.2.149:31950",
      run_id: "run-1",
      session_id: "recover-move-test",
      destination_slot: "D2",
      timeout_ms: 10,
      poll_interval_ms: 1,
    });

    assert.equal(result.data.executed_action, "suggest_new_destination_slot");
    assert.equal(result.data.executed_params.destination_slot, "D2");
    assert.equal(result.data.final_run_history.status, "succeeded");
  } finally {
    global.fetch = originalFetch;
  }
});

test("execute_protocol_recovery handles module blocker reconciliation by waiting, then resuming", async () => {
  const originalFetch = global.fetch;
  let modulePolls = 0;

  installCommonRecoveryFetch({
    commands: [
      {
        id: "cmd-module-wait",
        commandType: "aspirate",
        status: "failed",
        params: {},
        error: {
          errorType: "ModuleNotReadyError",
          detail: "module is still heating",
        },
      },
    ],
    modules: [
      {
        id: "temp-1",
        moduleModel: "temperatureModuleV2",
        moduleOffset: { slot: "C1" },
        data: {
          status: "heating",
          currentTemperature: 25,
          targetTemperature: 37,
        },
      },
    ],
    onRunAction() {
      assert.ok(modulePolls >= 4);
    },
  });

  const originalFetchWithModuleReady = global.fetch;
  global.fetch = async (url, options = {}) => {
    const requestUrl = new URL(url);
    if ((options.method || "GET") === "GET" && requestUrl.pathname === "/modules") {
      modulePolls += 1;
      if (modulePolls >= 4) {
        return jsonResponse({
          data: [
            {
              id: "temp-1",
              moduleModel: "temperatureModuleV2",
              moduleOffset: { slot: "C1" },
              data: {
                status: "idle",
                currentTemperature: 37,
                targetTemperature: 37,
              },
            },
          ],
        });
      }
    }
    return originalFetchWithModuleReady(url, options);
  };

  try {
    const result = await TOOL_HANDLERS.execute_protocol_recovery({
      robot_ip: "10.31.2.149:31950",
      run_id: "run-1",
      session_id: "recover-module-test",
      timeout_ms: 10,
      poll_interval_ms: 1,
      module_wait_timeout_ms: 20,
      module_poll_interval_ms: 1,
    });

    assert.equal(result.data.executed_action, "reconcile_state_first");
    assert.equal(result.data.module_wait.ready, true);
    assert.equal(result.data.final_run_history.status, "succeeded");
  } finally {
    global.fetch = originalFetch;
  }
});

test("recover_tip_pickup remains as a compatibility wrapper", async () => {
  const originalFetch = global.fetch;
  installCommonRecoveryFetch({
    commands: [
      {
        id: "cmd-failed",
        commandType: "pickUpTip",
        status: "failed",
        params: {
          pipetteId: "pipette-left-1",
          labwareId: "tiprack-1",
          wellName: "A1",
        },
        error: {
          errorType: "tipPhysicallyMissing",
          detail: "No Tip Detected",
        },
      },
    ],
    labware: [
      {
        id: "tiprack-1",
        loadName: "opentrons_flex_96_tiprack_1000ul",
        location: { slotName: "C2" },
      },
    ],
  });

  try {
    const result = await TOOL_HANDLERS.recover_tip_pickup({
      robot_ip: "10.31.2.149:31950",
      run_id: "run-1",
      session_id: "recover-tip-compat",
      timeout_ms: 10,
      poll_interval_ms: 1,
    });

    assert.equal(result.data.recovered_well, "B1");
    assert.equal(result.data.executed_action, "retry_pick_up_tip_with_next_candidate");
  } finally {
    global.fetch = originalFetch;
  }
});
