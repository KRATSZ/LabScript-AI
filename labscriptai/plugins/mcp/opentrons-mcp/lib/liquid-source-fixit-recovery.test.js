import test from "node:test";
import assert from "node:assert/strict";

import {
  buildInRunLiquidSubstitutionRecord,
  extractLiquidProbeHeightMm,
  findLastSucceededProtocolPickUpTipWell,
  findRunLabwareIdBySlot,
  planConfirmProbeFixitSteps,
  planInRunLiquidSourceSubstitutionFixitSteps,
  readPendingInRunLiquidSubstitutionConfirm,
  selectDropTipCleanupSteps,
  splitLiquidSubstitutionFixitSteps,
  splitReplacementProbeStep,
} from "./liquid-source-fixit-recovery.js";

const protocolSource = `
  B2  opentrons_flex_96_tiprack_1000ul
  C2  nest_12_reservoir_15ml
  D2  nest_96_wellplate_200ul_flat
  A3  trash bin

def run(protocol):
    trash = protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "B2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "C2")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "D2")
    pipette.pick_up_tip()
    liquid_class = protocol.get_liquid_class(name="water")
    pipette.transfer_with_liquid_class(
        liquid_class=liquid_class, volume=100, source=reservoir["A1"], dest=plate["A1"],
    )
    pipette.transfer_with_liquid_class(
        liquid_class=liquid_class, volume=100, source=reservoir["A1"], dest=plate["A2"],
    )
    pipette.transfer_with_liquid_class(
        liquid_class=liquid_class, volume=100, source=reservoir["A1"], dest=plate["A3"],
    )
    protocol.comment("Confirm D2.A1")
    pipette.pick_up_tip()
`;

test("findRunLabwareIdBySlot resolves labware id from run detail", () => {
  const runDetail = {
    labware: [
      { id: "reservoir-1", location: { slotName: "C2" } },
      { id: "plate-1", location: { slotName: "D2" } },
      { id: "tiprack-1", location: { slotName: "B2" } },
    ],
  };
  assert.equal(findRunLabwareIdBySlot(runDetail, "D2"), "plate-1");
  assert.equal(findRunLabwareIdBySlot(runDetail, "B2"), "tiprack-1");
});

test("planInRunLiquidSourceSubstitutionFixitSteps keeps attached tip through probe and transfers", () => {
  const plan = planInRunLiquidSourceSubstitutionFixitSteps({
    failedCommand: {
      params: {
        pipetteId: "pipette-left",
        labwareId: "reservoir-1",
        wellName: "A1",
      },
    },
    runDetail: {
      labware: [
        { id: "reservoir-1", location: { slotName: "C2" } },
        { id: "plate-1", location: { slotName: "D2" } },
        { id: "tiprack-1", location: { slotName: "B2" } },
      ],
    },
    preferredSourceKey: "C2.A2",
    protocolSource,
    nextTipWell: "A2",
    tiprackSlot: "B2",
  });

  assert.equal(plan.replacement_well, "A2");
  assert.deepEqual(plan.destination_wells, ["A1", "A2", "A3"]);
  const stepNames = plan.steps.map(step => step.name);
  assert.equal(stepNames[0], "replacement_liquid_probe");
  assert.ok(stepNames.includes("transfer_aspirate_A1"));
  assert.ok(stepNames.includes("transfer_dispense_A3"));
  assert.ok(stepNames.indexOf("replacement_liquid_probe") < stepNames.indexOf("transfer_aspirate_A1"));
  assert.ok(stepNames.indexOf("transfer_dispense_A3") < stepNames.indexOf("drop_attached_tip"));
  assert.ok(stepNames.includes("confirm_pick_up_tip"));
  assert.equal(plan.steps[0].payload.data.commandType, "liquidProbe");
  assert.equal(plan.steps[0].payload.data.intent, "fixit");
  assert.equal(plan.steps[0].payload.data.params.wellName, "A2");
  assert.equal(plan.steps.find(step => step.name === "transfer_aspirate_A1").payload.data.params.flowRate, 716);
  assert.equal(plan.steps.find(step => step.name === "confirm_pick_up_tip").payload.data.params.wellName, "A2");
});

test("findLastSucceededProtocolPickUpTipWell skips fixit pickUpTip commands", () => {
  const well = findLastSucceededProtocolPickUpTipWell([
    { commandType: "pickUpTip", status: "succeeded", params: { wellName: "A1" } },
    { commandType: "liquidProbe", status: "failed", params: { wellName: "A1" } },
    {
      commandType: "pickUpTip",
      status: "succeeded",
      intent: "fixit",
      params: { wellName: "B1" },
    },
  ]);
  assert.equal(well, "A1");
});

test("splitLiquidSubstitutionFixitSteps separates transfer and confirm phases", () => {
  const plan = planInRunLiquidSourceSubstitutionFixitSteps({
    failedCommand: {
      params: { pipetteId: "pipette-left", labwareId: "reservoir-1", wellName: "A1" },
    },
    runDetail: {
      labware: [
        { id: "reservoir-1", location: { slotName: "C2" } },
        { id: "plate-1", location: { slotName: "D2" } },
        { id: "tiprack-1", location: { slotName: "B2" } },
      ],
    },
    preferredSourceKey: "C2.A2",
    protocolSource,
    nextTipWell: "B1",
    tiprackSlot: "B2",
  });
  const { transferSteps, confirmSteps } = splitLiquidSubstitutionFixitSteps(plan.steps);
  assert.ok(transferSteps.some(step => step.name === "drop_attached_tip"));
  assert.ok(!transferSteps.some(step => step.name.startsWith("confirm_")));
  assert.ok(confirmSteps.every(step => step.name.startsWith("confirm_")));
  assert.equal(
    confirmSteps.find(step => step.name === "confirm_pick_up_tip").payload.data.params.wellName,
    "B1",
  );

  const { probeStep, postProbeSteps } = splitReplacementProbeStep(transferSteps);
  assert.equal(probeStep.name, "replacement_liquid_probe");
  assert.ok(!postProbeSteps.some(step => step.name === "replacement_liquid_probe"));
  assert.ok(postProbeSteps.some(step => step.name === "transfer_aspirate_A1"));
  assert.deepEqual(
    selectDropTipCleanupSteps(postProbeSteps).map(step => step.name),
    ["move_to_trash_for_drop", "drop_attached_tip"],
  );
});

test("extractLiquidProbeHeightMm reads z_position aliases", () => {
  assert.equal(
    extractLiquidProbeHeightMm({ terminal: { data: { status: "succeeded", result: { z_position: 16.11 } } } }),
    16.11,
  );
  assert.equal(
    extractLiquidProbeHeightMm({ status: "succeeded", result: { zPosition: 4.8 } }),
    4.8,
  );
  assert.equal(extractLiquidProbeHeightMm({ status: "succeeded", result: {} }), null);
});

test("readPendingInRunLiquidSubstitutionConfirm detects unfinished confirm after transfers", () => {
  const sessionState = {
    in_run_liquid_substitution: {
      run_id: "run-1",
      transfers_completed: true,
      confirm_completed: false,
    },
  };
  assert.ok(readPendingInRunLiquidSubstitutionConfirm(sessionState, "run-1"));
  assert.equal(readPendingInRunLiquidSubstitutionConfirm(sessionState, "run-2"), null);
  assert.equal(
    readPendingInRunLiquidSubstitutionConfirm(
      {
        in_run_liquid_substitution: {
          run_id: "run-1",
          transfers_completed: true,
          confirm_completed: true,
        },
      },
      "run-1",
    ),
    null,
  );
});

test("buildInRunLiquidSubstitutionRecord captures fixit continuation context", () => {
  const record = buildInRunLiquidSubstitutionRecord({
    runId: "run-1",
    fixitPlan: {
      pipette_id: "pipette-left",
      plate_labware_id: "plate-1",
      tiprack_labware_id: "tiprack-1",
      tiprack_slot: "B2",
      destination_wells: ["A1", "A2", "A3"],
    },
    failedSourceKey: "C2.A1",
    preferredSourceKey: "C2.A2",
    transfersCompleted: true,
    confirmCompleted: false,
  });
  assert.equal(record.run_id, "run-1");
  assert.equal(record.transfers_completed, true);
  assert.equal(record.confirm_completed, false);
  assert.equal(record.confirm_destination_well, "A1");
});

test("planConfirmProbeFixitSteps builds confirm-only fixit chain", () => {
  const plan = planConfirmProbeFixitSteps({
    pipetteId: "pipette-left",
    tiprackLabwareId: "tiprack-1",
    plateLabwareId: "plate-1",
    tipWell: "B1",
    confirmWell: "A1",
  });
  assert.equal(plan.steps.length, 4);
  assert.equal(plan.steps[0].name, "confirm_pick_up_tip");
  assert.equal(plan.steps[0].payload.data.params.wellName, "B1");
  assert.equal(plan.steps[1].name, "confirm_liquid_probe");
});
