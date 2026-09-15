import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { labwareLabel, planStepDisplay, sanitizeAssistantText } from "../web/src/display.ts";
import { playBeatsFromAnalyze, playBeatsFromSteps } from "../web/src/playBeats.ts";

describe("labwareLabel", () => {
  it("maps standard deck ids to short names", () => {
    assert.equal(labwareLabel("tecan_diti_200ul_tiprack"), "200 µL DiTi tips");
    assert.equal(labwareLabel("tecan_96_wellplate"), "96-well plate");
    assert.equal(labwareLabel("opentrons_96_tiprack_300ul"), "300 µL tips");
    assert.equal(labwareLabel("nest_12_reservoir_15ml"), "12-well reservoir");
  });
});

describe("planStepDisplay", () => {
  it("uses lab verbs instead of schema primitives", () => {
    assert.equal(planStepDisplay({ step_id: "pick", primitive_type: "PICK_TIPS" }), "Pick tips");
    assert.equal(
      planStepDisplay({
        step_id: "asp1",
        primitive_type: "ASPIRATE",
        volume_ul: 50,
        source: "reservoir:A1",
        destination: "plate:B2",
      }),
      "Aspirate — 50 µL — reservoir A1 → plate B2"
    );
  });
});

describe("sanitizeAssistantText", () => {
  it("strips assumed_deck and tool-schema leftovers", () => {
    assert.equal(
      sanitizeAssistantText("Using the standard deck assumed_deck=true for this run."),
      "Using the standard deck for this run."
    );
    assert.doesNotMatch(
      sanitizeAssistantText("next_tool=generate_sop after code_service=up"),
      /generate_sop|code_service|next_tool/
    );
  });
});

describe("playBeatsFromSteps", () => {
  it("walks pick → aspirate → dispense", () => {
    const beats = playBeatsFromSteps([
      { primitive_type: "PICK_TIPS", tip_positions: ["A1"] },
      { primitive_type: "ASPIRATE", volume_ul: 50, source: "reservoir:A1" },
      { primitive_type: "DISPENSE", volume_ul: 50, destination: "plate:B1" },
      { primitive_type: "DROP_TIPS" },
    ]);
    assert.deepEqual(
      beats.map((b) => b.slot),
      ["tips", "reservoir", "plate", "tips"]
    );
    assert.match(beats[0].label, /Pick tips/);
  });
});

describe("playBeatsFromAnalyze", () => {
  it("maps 8010 command types without inventing Watch", () => {
    const beats = playBeatsFromAnalyze({
      commands: [
        { commandType: "pickUpTip" },
        { commandType: "aspirate" },
        { commandType: "dispense" },
        { commandType: "dropTip" },
      ],
    });
    assert.deepEqual(
      beats.map((b) => b.slot),
      ["tips", "reservoir", "plate", "tips"]
    );
  });
});
