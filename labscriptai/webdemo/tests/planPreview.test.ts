import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { deckFromPlan, PLAN_PREVIEW_GAP, planPreviewGap, sessionForPlanSketch } from "../web/src/planPreview.ts";
import { phaseLabel } from "../web/src/pipelineLogic.ts";
import type { SessionSnapshot } from "../web/src/types.ts";

function snap(over: Partial<SessionSnapshot> = {}): SessionSnapshot {
  return {
    id: "s",
    phase: "ready",
    missing: [],
    goal: "Transfer 50 µL A1 to B1",
    doc: "none",
    robot: "Hamilton",
    hardware: { deck: { "1": "hamilton_96_tiprack_300ul", "2": "corning_96_wellplate_360ul_flat" } },
    hardware_config: "",
    sop: "# s",
    code: "",
    plan: {
      resources: [{ id: "tips", type: "tiprack", slot: "1" }],
      steps: [{ step_id: "1", primitive_type: "PICK_TIPS" }],
    },
    analyze: null,
    checks: { status: "pass", sim: { ok: true }, logicpass: { outcome: "pass" }, statepass: {} },
    fab: { lit: false },
    ...over,
  };
}

describe("planPreview", () => {
  it("builds a deck map from plan resources", () => {
    assert.deepEqual(
      deckFromPlan({
        resources: [
          { id: "tips", type: "tiprack", slot: "1" },
          { id: "plate", type: "plate", slot: "2" },
        ],
      }),
      { "1": "tips", "2": "plate" }
    );
  });

  it("reports a gap when neither deck nor plan labware exist, and keeps the copy stable", () => {
    assert.equal(planPreviewGap(null, {}), PLAN_PREVIEW_GAP);
    assert.equal(planPreviewGap({ steps: [{ step_id: "1" }] }, {}), PLAN_PREVIEW_GAP);
    assert.equal(planPreviewGap({ resources: [{ id: "tips", slot: "1" }] }, {}), null);
    assert.equal(planPreviewGap(null, { "1": "tips" }), null);
  });

  it("fills an empty session deck from the plan so the sketch can render", () => {
    const session = sessionForPlanSketch(
      snap({ hardware: { deck: {} } }),
      { resources: [{ id: "tips", type: "tiprack", slot: "1" }] },
      "Hamilton"
    );
    assert.equal(session?.hardware.deck["1"], "tips");
  });

  it("does not call a passing plan-backend run Ready to watch", () => {
    assert.equal(phaseLabel("ready", "pass", false, true, undefined, undefined, undefined, true), "Checks passed");
    assert.equal(phaseLabel("ready", "pass", true, false), "Ready to watch");
  });
});
