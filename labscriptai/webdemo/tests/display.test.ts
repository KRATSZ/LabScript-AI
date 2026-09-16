import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { labwareLabel, planStepDisplay, sanitizeAssistantText, headerGoalPreview, hasAttachedNotes } from "../web/src/display.ts";

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
    assert.equal(
      sanitizeAssistantText("Writing it up now.Checks are clean."),
      "Checks are clean."
    );
    assert.equal(
      sanitizeAssistantText("20 µL (microliters, not liters) from A1 to B1."),
      "20 µL from A1 to B1."
    );
    assert.equal(
      sanitizeAssistantText("Checks passed — sim clean, logic pass, review matches your ask."),
      "Checks passed — the run matches what you asked."
    );
    assert.equal(
      sanitizeAssistantText("Building the SOP now. Checks pass — clean run."),
      "Checks pass — clean run."
    );
    assert.equal(
      sanitizeAssistantText("15 mL reservoir on slot 3."),
      "12-well reservoir on slot 3."
    );
    assert.equal(
      sanitizeAssistantText(
        "Confirm volume, wells, mix, and the standard deck — nothing is written yet."
      ),
      ""
    );
    assert.equal(
      sanitizeAssistantText("Done — script is ready. Want me to open the run animation?"),
      "Done — script is ready."
    );
    assert.equal(
      sanitizeAssistantText("Writing it up now. Deck confirmed. Checks pass."),
      "Checks pass."
    );
    assert.equal(
      sanitizeAssistantText("— slot 1 tiprack. Writing it now."),
      "slot 1 tip rack. Writing it now."
    );
    assert.doesNotMatch(
      sanitizeAssistantText("Download the FluentControl.gwl and Step JSON."),
      /FluentControl\.gwl|Step JSON|\.gwl/
    );
    assert.equal(
      sanitizeAssistantText("the FluentControl.gwl worklist is ready."),
      "the Fluent worklist is ready."
    );
    assert.doesNotMatch(
      sanitizeAssistantText("Done. The protocol and the deck animation are ready. No Watch for Fluent."),
      /deck animation are ready|No Watch for Fluent/i
    );
    assert.equal(
      sanitizeAssistantText("The protocol and the deck animation are ready."),
      "The protocol is ready."
    );
    assert.equal(
      sanitizeAssistantText("Watch is open too if you want to see the run."),
      ""
    );
  });
});

describe("headerGoalPreview", () => {
  it("drops a duplicated robot name and a standard-deck recap", () => {
    assert.equal(
      headerGoalPreview(
        "Tecan Fluent",
        "Tecan Fluent. Transfer 50 µL from plate well A1 to plate well B1. One sample, no mix. Standard deck: slot 1 200 µL DiTi tiprack, slot 2 96-well plate, slot 3 12-well reservoir."
      ),
      "Transfer 50 µL from well A1 to well B1"
    );
    assert.equal(
      headerGoalPreview("OT-2", "Transfer 20 µL from well A1 to B1. One sample. No mix."),
      "Transfer 20 µL from well A1 to B1"
    );
    assert.equal(
      headerGoalPreview("OT-2", "Transfer 20 µL from well A1 to well B1 on the OT-2"),
      "Transfer 20 µL from well A1 to well B1"
    );
    assert.equal(
      headerGoalPreview(
        "Tecan Fluent",
        "Transfer 50 µL from plate well A1 to plate well B1. One sample, no mix (Tecan Fluent)."
      ),
      "Transfer 50 µL from well A1 to well B1"
    );
    assert.equal(
      headerGoalPreview("OT-2", "Transfer 20 µL from well A1 to B1 on the 96-well plate"),
      "Transfer 20 µL from well A1 to B1"
    );
    assert.equal(
      headerGoalPreview("Tecan Fluent", "Transfer 50 µL from well A1 to B1 on a Tecan Fluent"),
      "Transfer 50 µL from well A1 to B1"
    );
    assert.equal(
      headerGoalPreview(
        "Tecan Fluent",
        "Transfer 50 µL from plate well A1 to plate well B1 on Tecan Fluent, 1 sample, no mix"
      ),
      "Transfer 50 µL from well A1 to well B1"
    );
    assert.equal(
      headerGoalPreview(
        "Tecan Fluent",
        "Transfer 50 µL from well A1 to B1 on the Tecan Fluent, one sample"
      ),
      "Transfer 50 µL from well A1 to B1"
    );
    assert.doesNotMatch(
      headerGoalPreview(
        "Tecan Fluent",
        "Transfer 50 µL from plate well A1 to plate well B1 on the Tecan Fluent, 1 sample, no mix"
      ),
      /on(?: the)? Tecan Fluent/i
    );
  });
});

describe("hasAttachedNotes", () => {
  it("treats none/empty as no notes", () => {
    assert.equal(hasAttachedNotes(""), false);
    assert.equal(hasAttachedNotes("none"), false);
    assert.equal(hasAttachedNotes("None"), false);
    assert.equal(hasAttachedNotes("  n/a  "), false);
    assert.equal(hasAttachedNotes("Use 50 µL master mix"), true);
  });
});
