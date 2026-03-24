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

test("recover_tip_pickup enqueues fixit pickup and resumes the run", async () => {
  const originalFetch = global.fetch;
  let commandStatusReads = 0;
  let resumed = false;

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
            { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutC2" },
            { cutoutFixtureId: "trashBinAdapter", cutoutId: "cutoutA3" },
          ],
        },
      });
    }
    if (method === "GET" && pathname === "/modules") {
      return jsonResponse({ data: [] });
    }
    if (method === "GET" && pathname === "/runs/run-1") {
      return jsonResponse({
        data: {
          id: "run-1",
          protocolId: "protocol-1",
          status: resumed ? "succeeded" : "awaiting-recovery",
          currentlyRecoveringFrom: resumed ? null : "cmd-failed",
          hasEverEnteredErrorRecovery: true,
          labware: [
            {
              id: "tiprack-1",
              loadName: "opentrons_flex_96_tiprack_1000ul",
              location: { slotName: "C2" },
            },
          ],
        },
      });
    }
    if (method === "GET" && pathname === "/runs/run-1/commands") {
      return jsonResponse({
        data: [
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
      });
    }
    if (method === "POST" && pathname === "/runs/run-1/commands") {
      const payload = JSON.parse(options.body);
      assert.equal(payload.data.commandType, "pickUpTip");
      assert.equal(payload.data.intent, "fixit");
      assert.equal(payload.data.params.pipetteId, "pipette-left-1");
      assert.equal(payload.data.params.labwareId, "tiprack-1");
      assert.equal(payload.data.params.wellName, "B1");
      return jsonResponse({ data: { id: "cmd-fixit", status: "queued" } });
    }
    if (method === "GET" && pathname === "/runs/run-1/commands/cmd-fixit") {
      commandStatusReads += 1;
      return jsonResponse({
        data: {
          id: "cmd-fixit",
          commandType: "pickUpTip",
          status: commandStatusReads > 1 ? "succeeded" : "running",
          params: {
            pipetteId: "pipette-left-1",
            labwareId: "tiprack-1",
            wellName: "B1",
          },
        },
      });
    }
    if (method === "POST" && pathname === "/runs/run-1/actions") {
      const payload = JSON.parse(options.body);
      assert.equal(payload.data.actionType, "resume-from-recovery");
      resumed = true;
      return jsonResponse({ data: { id: "action-resume", actionType: "resume-from-recovery" } });
    }

    throw new Error(`Unexpected request: ${method} ${requestUrl.toString()}`);
  };

  try {
    const result = await TOOL_HANDLERS.recover_tip_pickup({
      robot_ip: "10.31.2.149:31950",
      run_id: "run-1",
      session_id: "recover-tip-test",
      tiprack_slots: ["C2"],
      timeout_ms: 10,
      poll_interval_ms: 1,
    });

    assert.equal(result.data.recovered_well, "B1");
    assert.equal(result.data.final_run_history.status, "succeeded");
    assert.equal(result.data.resume_action.data.actionType, "resume-from-recovery");
    assert.equal(result.runId, "run-1");
  } finally {
    global.fetch = originalFetch;
  }
});
