import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { labwareLabel, planStepDisplay, sanitizeAssistantText } from "../web/src/display.ts";

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
    assert.equal(sanitizeAssistantText("Is that 50 L vs 50 µL?"), "Is that 50 µL?");
    assert.equal(
      sanitizeAssistantText("Using the assumed deck for this run."),
      "Using the standard deck for this run."
    );
    assert.equal(
      sanitizeAssistantText("After the analyze pass the script is ready."),
      "After the checks passed the script is ready."
    );
  });
});
