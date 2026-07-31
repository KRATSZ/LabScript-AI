import assert from "node:assert/strict";
import test from "node:test";

import {
  assessTipRecoveryBudget,
  parseProtocolTipBudget,
} from "./protocol-tips.js";

const constrainedProtocol = `
# tip_budget: pick_up_tip_count=3; tips_loaded=3 (B2.A1, B2.B1, B2.C1); spares=0
def run(protocol):
    pipette.pick_up_tip()
    pipette.pick_up_tip()
    pipette.pick_up_tip()
`;

const liveScanProtocol = `
def run(protocol):
    pipette.pick_up_tip()
    pipette.pick_up_tip()
    pipette.pick_up_tip()
`;

test("parseProtocolTipBudget reads constrained tip budget metadata", () => {
  const budget = parseProtocolTipBudget(constrainedProtocol);
  assert.equal(budget.constrained, true);
  assert.equal(budget.pick_up_tip_count, 3);
  assert.equal(budget.tips_loaded, 3);
  assert.equal(budget.spares, 0);
  assert.deepEqual(budget.loaded_wells, ["A1", "B1", "C1"]);
});

test("assessTipRecoveryBudget blocks recovery when A1 missing leaves too few tips", () => {
  const assessment = assessTipRecoveryBudget({
    protocolSource: constrainedProtocol,
    commands: {
      data: [
        {
          commandType: "pickUpTip",
          status: "failed",
        },
      ],
    },
    viableCandidates: [
      { tiprack_slot: "B2", well_name: "B1", status: "viable" },
      { tiprack_slot: "B2", well_name: "C1", status: "viable" },
    ],
  });

  assert.equal(assessment.enforced, true);
  assert.equal(assessment.sufficient, false);
  assert.equal(assessment.basis, "protocol_metadata");
  assert.equal(assessment.pickups_remaining, 3);
  assert.equal(assessment.available_tips, 2);
});

test("assessTipRecoveryBudget allows clean run when three loaded tips remain", () => {
  const assessment = assessTipRecoveryBudget({
    protocolSource: constrainedProtocol,
    commands: { data: [] },
    viableCandidates: [
      { tiprack_slot: "B2", well_name: "A1", status: "viable" },
      { tiprack_slot: "B2", well_name: "B1", status: "viable" },
      { tiprack_slot: "B2", well_name: "C1", status: "viable" },
    ],
  });

  assert.equal(assessment.enforced, true);
  assert.equal(assessment.sufficient, true);
  assert.equal(assessment.basis, "protocol_metadata");
  assert.equal(assessment.pickups_remaining, 3);
  assert.equal(assessment.available_tips, 3);
});

test("assessTipRecoveryBudget skips enforcement only when no pickup count is available", () => {
  const assessment = assessTipRecoveryBudget({
    protocolSource: "def run(protocol):\n    protocol.comment('no tips')\n",
    commands: { data: [] },
    viableCandidates: [{ tiprack_slot: "B2", well_name: "A1", status: "viable" }],
  });

  assert.equal(assessment.enforced, false);
  assert.equal(assessment.sufficient, true);
  assert.equal(assessment.basis, "none");
});

test("assessTipRecoveryBudget enforces from live scan without tip_budget comments", () => {
  const assessment = assessTipRecoveryBudget({
    protocolSource: liveScanProtocol,
    commands: { data: [] },
    viableCandidates: [
      { tiprack_slot: "B2", well_name: "A1", status: "viable" },
      { tiprack_slot: "B2", well_name: "B1", status: "viable" },
      { tiprack_slot: "B2", well_name: "C1", status: "viable" },
    ],
  });

  assert.equal(assessment.enforced, true);
  assert.equal(assessment.sufficient, true);
  assert.equal(assessment.basis, "live_scan");
  assert.equal(assessment.total_pickups, 3);
  assert.equal(assessment.pickups_remaining, 3);
  assert.equal(assessment.available_tips, 3);
});

test("assessTipRecoveryBudget live scan insufficient when candidates < remaining pickups", () => {
  const assessment = assessTipRecoveryBudget({
    protocolSource: liveScanProtocol,
    commands: {
      data: [{ commandType: "pickUpTip", status: "succeeded" }],
    },
    viableCandidates: [{ tiprack_slot: "B2", well_name: "B1", status: "viable" }],
  });

  assert.equal(assessment.enforced, true);
  assert.equal(assessment.sufficient, false);
  assert.equal(assessment.basis, "live_scan");
  assert.equal(assessment.succeeded_pickups, 1);
  assert.equal(assessment.pickups_remaining, 2);
  assert.equal(assessment.available_tips, 1);
});
