import test from "node:test";
import assert from "node:assert/strict";

import {
  applyLiquidSourceSubstitutionPatchToProtocol,
  assessReserveProbeVolume,
  buildLiquidSourceSubstitutionContinuationGuide,
  buildLiquidSourceSubstitutionPlan,
  commandHasLiquidNotFoundError,
  evaluateReuseAttachedTipEligibility,
  isSubstituteVolumeUnverified,
  generateLiquidSourceSubstitutionValidationProtocol,
  isProbeOnlyLiquidNotFoundFailure,
  renderLiquidSourceSubstitutionAttachedTipContinuationProtocol,
  renderLiquidSourceSubstitutionValidationProtocol,
} from "./liquid-source-substitution.js";

const sessionState = {
  state_revision: 1,
  liquid_tracking: {
    sources: {
      "C2.A1": {
        slot_name: "C2",
        well_name: "A1",
        labware_load_name: "nest_12_reservoir_15ml",
        liquid_name: "Assay Buffer",
        expected_presence: true,
      },
      "C2.A2": {
        slot_name: "C2",
        well_name: "A2",
        labware_load_name: "nest_12_reservoir_15ml",
        liquid_name: "Assay Buffer",
        expected_presence: true,
      },
    },
  },
};

test("isProbeOnlyLiquidNotFoundFailure accepts probe-only liquidNotFound after pickUpTip", () => {
  const failedCommand = {
    id: "probe-1",
    command_type: "liquidProbe",
    error: { errorType: "liquidNotFound", detail: "Liquid Not Found" },
  };
  const recentCommands = [
    { id: "pick-1", command_type: "pickUpTip" },
    failedCommand,
  ];
  assert.equal(isProbeOnlyLiquidNotFoundFailure(failedCommand, recentCommands), true);
});

test("isProbeOnlyLiquidNotFoundFailure rejects probe failure after aspirate", () => {
  const failedCommand = {
    id: "probe-2",
    command_type: "liquidProbe",
    error: { errorType: "liquidNotFound" },
  };
  const recentCommands = [
    { id: "pick-1", command_type: "pickUpTip" },
    { id: "asp-1", command_type: "aspirate" },
    failedCommand,
  ];
  assert.equal(isProbeOnlyLiquidNotFoundFailure(failedCommand, recentCommands), false);
});

test("commandHasLiquidNotFoundError accepts string error detail from run history", () => {
  assert.equal(
    commandHasLiquidNotFoundError({
      command_type: "liquidProbe",
      error: "Liquid Not Found",
    }),
    true,
  );
});

test("evaluateReuseAttachedTipEligibility is true for substitution + attached tip + probe-only failure", () => {
  const plan = buildLiquidSourceSubstitutionPlan({
    sessionState,
    failedSourceKey: "C2.A1",
    preferredSourceKey: "C2.A2",
  });
  const failedCommand = {
    id: "probe-1",
    command_type: "liquidProbe",
    error: { errorType: "liquidNotFound" },
  };
  const context = evaluateReuseAttachedTipEligibility({
    failedCommand,
    recentCommands: [{ id: "pick-1", command_type: "pickUpTip" }, failedCommand],
    substitutionPlan: plan,
    attachedTips: [{ mount: "left", instrument_name: "p1000_single_flex" }],
  });
  assert.equal(context.eligible, true);
  assert.deepEqual(context.recommended_validation_run_time_parameters, { reuse_attached_tip: true });
});

test("validation protocol supports reuse_attached_tip parameter and conditional pick_up_tip", () => {
  const plan = buildLiquidSourceSubstitutionPlan({
    sessionState,
    failedSourceKey: "C2.A1",
    preferredSourceKey: "C2.A2",
  });
  const protocolSource = renderLiquidSourceSubstitutionValidationProtocol({
    plan,
    pipetteName: "flex_1channel_1000",
    mount: "left",
    tiprackLoadName: "opentrons_flex_96_tiprack_1000ul",
    tiprackSlot: "B2",
  });
  assert.match(protocolSource, /reuse_attached_tip/);
  assert.match(protocolSource, /if not reuse_attached_tip:/);
  assert.match(protocolSource, /pipette\.pick_up_tip\(\)/);
  assert.match(protocolSource, /pipette\.require_liquid_presence\(target_well\)/);
  assert.match(protocolSource, /if not reuse_attached_tip:\s*\n\s*pipette\.drop_tip\(\)/);
});

test("attached-tip continuation retains tip through probe and transfer", () => {
  const plan = buildLiquidSourceSubstitutionPlan({
    sessionState,
    failedSourceKey: "C2.A1",
    preferredSourceKey: "C2.A2",
  });
  const protocolSource = renderLiquidSourceSubstitutionAttachedTipContinuationProtocol({
    plan,
    transferHints: {
      destination_wells: ["A1", "A2", "A3"],
      transfer_volume: 100,
      liquid_class_name: "water",
      reservoir_load_name: "nest_12_reservoir_15ml",
      reservoir_slot: "C2",
      plate_load_name: "nest_96_wellplate_200ul_flat",
      plate_slot: "D2",
      trash_slot: "A3",
      has_confirm_probe_cycle: true,
      confirm_destination_well: "D2.A1",
    },
    pipetteName: "flex_1channel_1000",
    mount: "left",
    tiprackLoadName: "opentrons_flex_96_tiprack_1000ul",
    tiprackSlot: "B2",
  });
  assert.match(protocolSource, /reuse_attached_tip/);
  assert.match(protocolSource, /require_liquid_presence\(replacement\)/);
  assert.match(protocolSource, /transfer_with_liquid_class/);
  assert.match(protocolSource, /"attached_tip_continuation": True/);
  assert.match(protocolSource, /default=False,\s*\n\s*\)\s*\n\s*parameters\.add_bool\(\s*\n\s*display_name="Dry run: return tips"/);
  assert.doesNotMatch(protocolSource, /:true\b|:false\b|:null\b/);
  const probeIndex = protocolSource.indexOf("require_liquid_presence(replacement)");
  const transferIndex = protocolSource.indexOf("transfer_with_liquid_class");
  const dropIndex = protocolSource.indexOf("pipette.drop_tip(trash)");
  assert.ok(probeIndex >= 0 && transferIndex > probeIndex && dropIndex > transferIndex);
});

test("generateLiquidSourceSubstitutionValidationProtocol keeps liquid guard analysis passing", () => {
  const generated = generateLiquidSourceSubstitutionValidationProtocol({
    sessionState,
    failedSourceKey: "C2.A1",
    preferredSourceKey: "C2.A2",
    pipetteName: "flex_1channel_1000",
    mount: "left",
    tiprackLoadName: "opentrons_flex_96_tiprack_1000ul",
    tiprackSlot: "B2",
  });
  assert.equal(generated.validation_protocol.liquid_guard_analysis.status, "pass");
  assert.equal(generated.validation_protocol.no_aspirate_or_dispense, true);
  assert.equal(commandHasLiquidNotFoundError({ error: { errorType: "liquidNotFound" } }), true);
});

test("applyLiquidSourceSubstitutionPatchToProtocol prefers attached-tip continuation for primary_well protocols", () => {
  const source = `
def add_parameters(parameters):
    parameters.add_str(variable_name="primary_well", default="A1", choices=[{"value": "A1"}, {"value": "A2"}])

def run(protocol):
    primary = reservoir["A1"]
`;
  const result = applyLiquidSourceSubstitutionPatchToProtocol(source, {
    failedSourceKey: "C2.A1",
    replacementSourceKey: "C2.A2",
  });
  assert.equal(result.continuation_mode, "in_run_fixit");
  assert.equal(result.recommended_run_time_parameters, null);
  assert.equal(result.patch_applied, false);
  assert.match(result.operator_steps[0], /awaiting-recovery/i);
});

test("applyLiquidSourceSubstitutionPatchToProtocol rewrites hardcoded well access", () => {
  const source = 'primary = reservoir["A1"]\nreserve = reservoir["A2"]';
  const result = applyLiquidSourceSubstitutionPatchToProtocol(source, {
    failedSourceKey: "C2.A1",
    replacementSourceKey: "C2.A2",
  });
  assert.equal(result.continuation_mode, "patched_protocol");
  assert.equal(result.patch_applied, true);
  assert.match(result.protocol_source, /reservoir\["A2"\]/);
  assert.doesNotMatch(result.protocol_source, /primary = reservoir\["A1"\]/);
});

test("attached-tip continuation guide prioritizes recover_liquid_source_substitution when reuse eligible", () => {
  const guide = buildLiquidSourceSubstitutionContinuationGuide({
    failedSourceKey: "C2.A1",
    replacementSourceKey: "C2.A2",
    reuseAttachedTipEligible: true,
  });
  assert.equal(guide.recommended_next_tools[0], "recover_liquid_source_substitution");
  assert.match(guide.steps[0], /in-run fixit/i);
});

test("continuation guide without attached tip routes to manual intervention", () => {
  const guide = buildLiquidSourceSubstitutionContinuationGuide({
    failedSourceKey: "C2.A1",
    replacementSourceKey: "C2.A2",
    reuseAttachedTipEligible: false,
  });
  assert.equal(guide.steps[0], "manual_intervention");
  assert.deepEqual(guide.recommended_next_tools, ["safe_next_action", "parse_error"]);
});

test("volume_check blocks substitution when usable volume is below remaining transfers", () => {
  const session = {
    state_revision: 1,
    liquid_tracking: {
      sources: {
        "C2.A1": {
          slot_name: "C2",
          well_name: "A1",
          labware_load_name: "nest_12_reservoir_15ml",
          liquid_name: "Assay Buffer",
          expected_presence: true,
          volume_ul: 0,
        },
        "C2.A2": {
          slot_name: "C2",
          well_name: "A2",
          labware_load_name: "nest_12_reservoir_15ml",
          liquid_name: "Assay Buffer",
          expected_presence: true,
          declared_volume: 300,
          dead_volume: 0,
          consumed_volume_ul: 0,
        },
      },
    },
  };
  const protocolSource = `
reservoir = protocol.load_labware("nest_12_reservoir_15ml", "C2")
plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "D2")
pipette.transfer_with_liquid_class(liquid_class=water, volume=200, source=buf, dest=plate["A1"])
pipette.transfer_with_liquid_class(liquid_class=water, volume=200, source=buf, dest=plate["A2"])
pipette.transfer_with_liquid_class(liquid_class=water, volume=200, source=buf, dest=plate["A3"])
`;
  const plan = buildLiquidSourceSubstitutionPlan({
    sessionState: session,
    failedSourceKey: "C2.A1",
    preferredSourceKey: "C2.A2",
    protocolSource,
  });
  assert.equal(plan.status, "blocked");
  assert.equal(plan.same_liquid_source_substitution_allowed, false);
  assert.equal(plan.blocked_reason, "substitute_volume_insufficient");
  assert.equal(plan.required_next_step, "refill_source_or_escalate");
  assert.equal(plan.volume_check.basis, "declared_source_map");
  assert.equal(plan.volume_check.sufficient, false);
  assert.equal(plan.volume_check.required_ul, 600);
  assert.equal(plan.volume_check.usable_ul, 300);
  assert.equal(plan.volume_check.candidate_key, "C2.A2");
});

test("volume_check allows substitution when usable volume covers remaining transfers", () => {
  const session = {
    state_revision: 1,
    liquid_tracking: {
      sources: {
        "C2.A1": {
          slot_name: "C2",
          well_name: "A1",
          labware_load_name: "nest_12_reservoir_15ml",
          liquid_name: "Assay Buffer",
          expected_presence: true,
        },
        "C2.A2": {
          slot_name: "C2",
          well_name: "A2",
          labware_load_name: "nest_12_reservoir_15ml",
          liquid_name: "Assay Buffer",
          expected_presence: true,
          observed_presence: true,
          declared_volume: 1000,
          dead_volume: 50,
          consumed_volume_ul: 0,
        },
      },
    },
  };
  const plan = buildLiquidSourceSubstitutionPlan({
    sessionState: session,
    failedSourceKey: "C2.A1",
    preferredSourceKey: "C2.A2",
    transferHints: {
      destination_wells: ["A1", "A2", "A3"],
      transfer_volume: 200,
    },
  });
  assert.equal(plan.status, "planned");
  assert.equal(plan.same_liquid_source_substitution_allowed, true);
  assert.equal(plan.volume_check.basis, "declared_source_map");
  assert.equal(plan.volume_check.sufficient, true);
  assert.equal(plan.volume_check.required_ul, 600);
  assert.equal(plan.volume_check.usable_ul, 950);
});

test("volume_check uses insufficient_data without inventing a new auto-allow path", () => {
  const plan = buildLiquidSourceSubstitutionPlan({
    sessionState,
    failedSourceKey: "C2.A1",
    preferredSourceKey: "C2.A2",
  });
  assert.equal(plan.status, "planned");
  assert.equal(plan.volume_check.basis, "insufficient_data");
  assert.equal(plan.volume_check.sufficient, false);
  assert.equal(plan.same_liquid_source_substitution_allowed, true);
  assert.notEqual(plan.blocked_reason, "substitute_volume_insufficient");
});

test("isSubstituteVolumeUnverified when demand known but usable volume unknown", () => {
  const plan = buildLiquidSourceSubstitutionPlan({
    sessionState,
    failedSourceKey: "C2.A1",
    preferredSourceKey: "C2.A2",
    transferHints: {
      destination_wells: ["A1", "A2", "A3"],
      transfer_volume: 200,
    },
  });
  assert.equal(plan.volume_check.basis, "insufficient_data");
  assert.equal(plan.volume_check.required_ul, 600);
  assert.equal(isSubstituteVolumeUnverified(plan.volume_check), true);
});

test("isSubstituteVolumeUnverified is false for conclusive declared shortfall", () => {
  assert.equal(
    isSubstituteVolumeUnverified({
      basis: "declared_source_map",
      sufficient: false,
      required_ul: 600,
      usable_ul: 100,
    }),
    false,
  );
  assert.equal(
    isSubstituteVolumeUnverified({
      basis: "insufficient_data",
      sufficient: false,
      required_ul: null,
    }),
    false,
  );
});

test("assessReserveProbeVolume passes for tall nest_12 fill vs 3x100 uL", () => {
  const check = assessReserveProbeVolume({
    height_mm: 16.11,
    labware_load_name: "nest_12_reservoir_15ml",
    candidateKey: "C2.A2",
    transferHints: {
      transfer_volume: 100,
      destination_wells: ["A1", "A2", "A3"],
    },
  });
  assert.equal(check.basis, "approximate_lpd_height");
  assert.equal(check.sufficient, true);
  assert.equal(check.blocked_reason, null);
  assert.ok(check.estimated_ul > 9000);
  assert.equal(check.required_ul, 100 * 3 * 1.2);
});

test("assessReserveProbeVolume fails for shallow nest_12 fill", () => {
  const check = assessReserveProbeVolume({
    height_mm: 1.0,
    labware_load_name: "nest_12_reservoir_15ml",
    candidateKey: "C2.A2",
    transferHints: {
      transfer_volume: 100,
      destination_wells: ["A1", "A2", "A3"],
    },
  });
  assert.equal(check.basis, "approximate_lpd_height");
  assert.equal(check.sufficient, false);
  assert.equal(check.blocked_reason, "substitute_reserve_volume_insufficient");
  // estimated ≈ 584, dead 1900 → usable 0
  assert.equal(check.usable_ul, 0);
});

test("assessReserveProbeVolume fails closed when height is missing", () => {
  const check = assessReserveProbeVolume({
    height_mm: null,
    labware_load_name: "nest_12_reservoir_15ml",
    candidateKey: "C2.A2",
    transferHints: {
      transfer_volume: 100,
      destination_wells: ["A1", "A2", "A3"],
    },
  });
  assert.equal(check.sufficient, false);
  assert.equal(check.blocked_reason, "substitute_reserve_volume_insufficient");
});

test("assessReserveProbeVolume fails closed for unknown labware geometry", () => {
  const check = assessReserveProbeVolume({
    height_mm: 10,
    labware_load_name: "unknown_reservoir",
    candidateKey: "C2.A2",
    transferHints: {
      transfer_volume: 100,
      destination_wells: ["A1"],
    },
  });
  assert.equal(check.sufficient, false);
  assert.equal(check.estimated_ul, null);
  assert.equal(check.blocked_reason, "substitute_reserve_volume_insufficient");
});
