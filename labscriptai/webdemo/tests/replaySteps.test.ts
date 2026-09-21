import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  actionStepCount,
  analyzeReplaySteps,
  clampStepIndex,
  isVisualizerPlayCommand,
  planReplaySteps,
  replayStepsFor,
} from "../web/src/replaySteps.ts";
import {
  clientXForTrackPercent,
  visualizerIndexFromPercent,
  visualizerPlayPercent,
} from "../web/src/otPlaybackSync.ts";

describe("replaySteps", () => {
  it("lists only Watch-playable analyze commands so Home/load stay off the scrubber", () => {
    const steps = analyzeReplaySteps({
      commands: [
        { id: "c0", commandType: "home" },
        { id: "c1", commandType: "loadLabware", params: { loadName: "plate" } },
        { id: "c1b", commandType: "loadPipette" },
        { id: "c2", commandType: "pickUpTip", params: { wellName: "A1" } },
        { id: "c3", commandType: "aspirate", params: { wellName: "A1", volume: 20 } },
        { id: "c4", commandType: "dispense", params: { wellName: "B1", volume: 20 } },
      ],
    });
    assert.equal(steps.length, 3);
    assert.equal(steps[0].label, "Pick up tip");
    assert.equal(steps[0].index, 0);
    assert.match(steps[1].detail, /20 µL/);
    assert.equal(actionStepCount(steps), 3);
    assert.equal(isVisualizerPlayCommand("loadLabware"), false);
    assert.equal(isVisualizerPlayCommand("home"), false);
    assert.equal(isVisualizerPlayCommand("pickUpTip"), true);
    assert.equal(isVisualizerPlayCommand("moveLabware"), true);
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

  it("maps visualizer percent 1:1 onto playable command indices", () => {
    assert.equal(visualizerPlayPercent(0, 32), 0);
    assert.equal(visualizerPlayPercent(31, 32), 100);
    assert.equal(visualizerIndexFromPercent(0, 32), 0);
    assert.equal(visualizerIndexFromPercent(100, 32), 31);
    for (let i = 0; i < 32; i++) {
      assert.equal(visualizerIndexFromPercent(visualizerPlayPercent(i, 32), 32), i);
    }
    const track = { getBoundingClientRect: () => ({ x: 10, width: 112, left: 10, top: 0, height: 8 }) } as HTMLElement;
    assert.equal(clientXForTrackPercent(track, 0), 16);
    assert.equal(clientXForTrackPercent(track, 100), 116);
  });
});
