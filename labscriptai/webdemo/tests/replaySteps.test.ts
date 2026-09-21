import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  actionStepCount,
  analyzeReplaySteps,
  clampStepIndex,
  planReplaySteps,
  replayStepsFor,
} from "../web/src/replaySteps.ts";

describe("replaySteps", () => {
  it("labels analyze commands and keeps setup plus liquid-handling rows", () => {
    const steps = analyzeReplaySteps({
      commands: [
        { id: "c1", commandType: "loadLabware", params: { loadName: "plate" } },
        { id: "c2", commandType: "pickUpTip", params: { wellName: "A1" } },
        { id: "c3", commandType: "aspirate", params: { wellName: "A1", volume: 20 } },
        { id: "c4", commandType: "dispense", params: { wellName: "B1", volume: 20 } },
      ],
    });
    assert.equal(steps.length, 4);
    assert.equal(steps[0].setup, true);
    assert.equal(steps[1].label, "Pick up tip");
    assert.match(steps[2].detail, /20 µL/);
    assert.equal(actionStepCount(steps), 3);
  });

  it("formats plan IR steps for the demo list", () => {
    const steps = planReplaySteps({
      steps: [
        { step_id: "1", primitive_type: "PICK_TIPS", tip_positions: ["A1"] },
        { step_id: "2", primitive_type: "ASPIRATE", source: "res:A1", volume_ul: 20 },
      ],
    });
    assert.equal(steps.length, 2);
    assert.match(steps[1].label, /Aspirate/);
    assert.equal(replayStepsFor({ plan: { steps: steps.map((s) => ({ step_id: s.id })) } }).length, 2);
  });

  it("clamps the scrubber index", () => {
    assert.equal(clampStepIndex(-2, 5), 0);
    assert.equal(clampStepIndex(9, 5), 4);
    assert.equal(clampStepIndex(2.6, 5), 3);
    assert.equal(clampStepIndex(1, 0), 0);
  });
});
