import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  spotForTime,
  stepIndexAt,
  timeForSpot,
  type TimelineStep,
} from "../web/src/flex3dTimeline.ts";

const STEPS: TimelineStep[] = [
  { commandId: "home", kind: "home", t0: 0, t1: 0.76 },
  { commandId: "liq", kind: "loadLiquid", t0: 0.76, t1: 0.76 },
  { commandId: "pick", kind: "pickUpTip", t0: 0.76, t1: 3.0 },
  { commandId: "asp", kind: "aspirate", t0: 3.0, t1: 5.0 },
];

describe("stepIndexAt", () => {
  it("picks the last started step and skips loadLiquid", () => {
    assert.equal(stepIndexAt(STEPS, 0.1), 0);
    assert.equal(stepIndexAt(STEPS, 0.76), 2);
    assert.equal(stepIndexAt(STEPS, 4.0), 3);
  });

  it("returns -1 before the first step", () => {
    assert.equal(stepIndexAt(STEPS, -1), -1);
    assert.equal(stepIndexAt([], 1), -1);
  });
});

describe("spotForTime and timeForSpot", () => {
  it("maps a time inside a step to its command and progress", () => {
    assert.deepEqual(spotForTime(STEPS, 4.0), { commandId: "asp", fraction: 0.5 });
  });

  it("holds progress at 1 after the step's end until the next step starts", () => {
    assert.deepEqual(spotForTime(STEPS, 9.0), { commandId: "asp", fraction: 1 });
  });

  it("maps a command and progress back to a time", () => {
    assert.equal(timeForSpot(STEPS, "asp", 0.5), 4.0);
    assert.equal(timeForSpot(STEPS, "asp", 2), 5.0);
    assert.equal(timeForSpot(STEPS, null, 0.3), 0);
    assert.equal(timeForSpot(STEPS, "missing", 0.3), 0);
  });

  it("round-trips every step and fraction", () => {
    for (const step of STEPS) {
      if (step.kind === "loadLiquid") continue;
      for (const fraction of [0, 0.25, 0.9]) {
        const t = timeForSpot(STEPS, step.commandId, fraction);
        const spot = spotForTime(STEPS, t);
        assert.equal(spot.commandId, step.commandId);
        assert.ok(Math.abs(spot.fraction - fraction) < 1e-9, `${step.commandId} ${fraction}`);
      }
    }
  });

  it("gives a zero-length step full progress", () => {
    assert.deepEqual(spotForTime([{ commandId: "x", kind: "dropTip", t0: 2, t1: 2 }], 2), {
      commandId: "x",
      fraction: 1,
    });
  });
});
