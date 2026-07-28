import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import test from "node:test";

import {
  assessTipRecoveryBudget,
  parseProtocolTipBudget,
} from "./protocol-tips.js";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "..", "..");
const protocol02 = readFileSync(
  join(repoRoot, "local", "02_triple_transfer_chain.py"),
  "utf8",
);

test("parseProtocolTipBudget reads constrained triple-transfer metadata", () => {
  const budget = parseProtocolTipBudget(protocol02);
  assert.equal(budget.constrained, true);
  assert.equal(budget.pick_up_tip_count, 3);
  assert.equal(budget.tips_loaded, 3);
  assert.equal(budget.spares, 0);
  assert.deepEqual(budget.loaded_wells, ["A1", "B1", "C1"]);
});

test("assessTipRecoveryBudget blocks recovery when A1 missing leaves too few tips", () => {
  const assessment = assessTipRecoveryBudget({
    protocolSource: protocol02,
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
  assert.equal(assessment.pickups_remaining, 3);
  assert.equal(assessment.available_tips, 2);
});

test("assessTipRecoveryBudget allows clean run when three loaded tips remain", () => {
  const assessment = assessTipRecoveryBudget({
    protocolSource: protocol02,
    commands: { data: [] },
    viableCandidates: [
      { tiprack_slot: "B2", well_name: "A1", status: "viable" },
      { tiprack_slot: "B2", well_name: "B1", status: "viable" },
      { tiprack_slot: "B2", well_name: "C1", status: "viable" },
    ],
  });

  assert.equal(assessment.enforced, true);
  assert.equal(assessment.sufficient, true);
  assert.equal(assessment.pickups_remaining, 3);
  assert.equal(assessment.available_tips, 3);
});

test("assessTipRecoveryBudget skips enforcement when protocol has no budget metadata", () => {
  const assessment = assessTipRecoveryBudget({
    protocolSource: "pipette.pick_up_tip()\npipette.pick_up_tip()",
    commands: { data: [] },
    viableCandidates: [{ tiprack_slot: "B2", well_name: "A1", status: "viable" }],
  });

  assert.equal(assessment.enforced, false);
  assert.equal(assessment.sufficient, true);
});
