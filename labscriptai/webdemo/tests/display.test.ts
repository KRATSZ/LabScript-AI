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
    assert.doesNotMatch(sanitizeAssistantText("Done. The protocol and the deck animation are ready. No Watch for Fluent."), /deck animation are ready|No Watch for Fluent/i);
    assert.doesNotMatch(
      sanitizeAssistantText("Downloadables: steps and the script (no Watch on Hamilton)."),
      /Watch/i
    );
    assert.equal(
      sanitizeAssistantText("Python script and on-screen deck are ready to download"),
      "Python script is ready to download. The deck is on Stage"
    );
    assert.doesNotMatch(
      sanitizeAssistantText("Python script and on-screen deck are ready to download."),
      /on-screen deck are ready to download/i
    );
    assert.match(
      sanitizeAssistantText("Python script and on-screen deck are ready to download."),
      /ready to download/i
    );
    assert.match(
      sanitizeAssistantText("Python script and on-screen deck are ready to download."),
      /deck is on Stage/i
    );
    assert.equal(
      sanitizeAssistantText("Watch is open too if you want to see the run."),
      "The deck is on Stage."
    );
    assert.equal(
      sanitizeAssistantText("Done. Watch/animation is ready for this run too."),
      "Done. The deck is on Stage."
    );
    assert.equal(sanitizeAssistantText("Watch is up."), "The deck is on Stage.");
    assert.equal(
      sanitizeAssistantText("Done. 20 µL moved from A1 to B1 — script is available for download. Watch is up."),
      "Done. 20 µL moved from A1 to B1 — script is available for download. The deck is on Stage."
    );
    assert.equal(
      sanitizeAssistantText("Done. Watch is up. Watch/animation is ready for this run too."),
      "Done. The deck is on Stage."
    );
    assert.equal(
      sanitizeAssistantText("Deck confirmed: 300 µL tips in slot 1, 96-well plate in slot 2."),
      "Standard deck — 300 µL tips in slot 1, 96-well plate in slot 2."
    );
    assert.equal(
      sanitizeAssistantText(": 300 µL tips in slot 1, 96-well plate in slot 2, 12-well reservoir in slot 3."),
      "Standard deck — 300 µL tips in slot 1, 96-well plate in slot 2, 12-well reservoir in slot 3."
    );
    assert.doesNotMatch(
      sanitizeAssistantText("Watch is up: 300 µL tips in slot 1."),
      /^:|\bWatch\b/i
    );
    assert.equal(
      sanitizeAssistantText("Watch is up: 300 µL tips in slot 1."),
      "The deck is on Stage. 300 µL tips in slot 1."
    );
    assert.doesNotMatch(sanitizeAssistantText("Python.py is ready to download."), /Python\.py/);
    assert.match(sanitizeAssistantText("Python.py is ready to download."), /Python file is ready to download/);
    assert.equal(sanitizeAssistantText("Python (.py) is ready to download."), "Python file is ready to download.");
    assert.equal(
      sanitizeAssistantText("Your Python script (.py) is ready to download."),
      "Your Python file is ready to download."
    );
    assert.doesNotMatch(
      sanitizeAssistantText("output is a FluentControl worklist plus a steps."),
      /FluentControl|plus a steps/i
    );
    assert.doesNotMatch(
      sanitizeAssistantText("Got it. Standard — writing the SOP and the step plan."),
      /\bSOP\b/
    );
    assert.match(
      sanitizeAssistantText("tips in slot 1, plate in slot 2, reservoir in slot 3", "Hamilton"),
      /tip carrier/
    );
    assert.doesNotMatch(
      sanitizeAssistantText("tips in slot 1, plate in slot 2, reservoir in slot 3", "Hamilton"),
      /slot 1|slot 2|slot 3/
    );
    assert.equal(
      sanitizeAssistantText("Done. Download the Python script from the panel. Want anything changed?"),
      "Done. Download the Python script from the panel."
    );
    assert.equal(
      sanitizeAssistantText("Done. Want anything changed."),
      "Done."
    );
    assert.equal(
      sanitizeAssistantText("96-well plate in D2/A1 on Flex."),
      "96-well plate in D2, well A1 on Flex."
    );
    assert.match(
      sanitizeAssistantText("300 µL tips in slot 1, 96-well plate in slot 2", "OT-2"),
      /slot 1/
    );
    assert.match(
      sanitizeAssistantText("the code service is down, so Python stays off."),
      /preview service is down/
    );
    assert.doesNotMatch(
      sanitizeAssistantText("the code service is down, so Python stays off."),
      /code service/
    );
    assert.match(
      sanitizeAssistantText(
        "300 µL tips on the tip carrier (rails 1–6), plate on the plate carrier (rails 8–13)",
        "Vantage"
      ),
      /1\.3 m deck/
    );
    assert.doesNotMatch(
      sanitizeAssistantText(
        "300 µL tips on the tip carrier (rails 1–6), plate on the plate carrier (rails 8–13)",
        "Vantage"
      ),
      /rails 1–6|tip carrier/
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
    assert.equal(
      headerGoalPreview("OT-2", "Transfer 20 µL from well A1 to well B1, using the OT-2"),
      "Transfer 20 µL from well A1 to well B1"
    );
    assert.equal(
      headerGoalPreview("OT-2", "Transfer 20 µL from well A1 to well B1, using the"),
      "Transfer 20 µL from well A1 to well B1"
    );
    assert.equal(
      headerGoalPreview("Tecan Fluent", "Transfer 50 µL from well A1 to B1 ()"),
      "Transfer 50 µL from well A1 to B1"
    );
    assert.equal(
      headerGoalPreview("Tecan Fluent", "Transfer 50 µL from well A1 to B1 (1 sample)"),
      "Transfer 50 µL from well A1 to B1"
    );
    assert.doesNotMatch(
      headerGoalPreview("Tecan Fluent", "Transfer 50 µL from well A1 to B1 (Tecan Fluent, 1 sample)"),
      /\(\s*\)/
    );
    assert.equal(
      headerGoalPreview("OT-2", "Transfer 20 µL from well A1 to B1;"),
      "Transfer 20 µL from well A1 to B1"
    );
    assert.doesNotMatch(headerGoalPreview("OT-2", "Transfer 20 µL from well A1 to B1;"), /;$/);
    assert.equal(
      headerGoalPreview("Tecan Fluent", "Transfer 50 µL from plate A1 to B1, Tecan Fluent"),
      "Transfer 50 µL from plate A1 to B1"
    );
    assert.doesNotMatch(
      headerGoalPreview("Tecan Fluent", "Transfer 50 µL from plate A1 to B1, Tecan Fluent"),
      /, Tecan Fluent/i
    );
    assert.equal(
      headerGoalPreview("OT-2", "Transfer 20 µL from well A1 to B1 on an OT-2"),
      "Transfer 20 µL from well A1 to B1"
    );
    assert.doesNotMatch(
      headerGoalPreview("OT-2", "Transfer 20 µL from well A1 to B1 on an OT-2"),
      /on an OT-2/i
    );
    assert.equal(
      headerGoalPreview("Flex", "Transfer 20 µL from well A1 to B1 with the Flex"),
      "Transfer 20 µL from well A1 to B1"
    );
    assert.equal(
      headerGoalPreview("Flex", "Transfer 20 µL from well A1 to B1 with the"),
      "Transfer 20 µL from well A1 to B1"
    );
    assert.equal(
      headerGoalPreview("Flex", "Transfer 20 µL from well A1 to B1 with the standard deck."),
      "Transfer 20 µL from well A1 to B1"
    );
    assert.doesNotMatch(
      headerGoalPreview("Flex", "Transfer 20 µL from well A1 to B1 with the standard deck."),
      /with the/i
    );
    assert.equal(
      headerGoalPreview("Tecan Fluent", "Transfer 50 µL from well A1 to well B1 (Tecan Fluent"),
      "Transfer 50 µL from well A1 to well B1"
    );
    assert.doesNotMatch(
      headerGoalPreview("Tecan Fluent", "Transfer 50 µL from well A1 to well B1 (Tecan Fluent"),
      /\(Tecan Fluent/i
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
