import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { downloadable, downloadSuffix, planStepLine, planSteps } from "../web/src/artifacts.ts";

describe("planStepLine", () => {
  it("formats aspirate with volume and route", () => {
    assert.equal(
      planStepLine({
        step_id: "asp1",
        primitive_type: "ASPIRATE",
        volume_ul: 50,
        source: "reservoir:A1",
        destination: "plate:B2",
      }),
      "asp1 ASPIRATE 50µL reservoir:A1→plate:B2"
    );
  });

  it("uses location when no source or destination", () => {
    assert.equal(
      planStepLine({ step_id: "mix1", primitive_type: "MIX", volume_ul: 20, location: "plate:A1" }),
      "mix1 MIX 20µL plate:A1"
    );
  });

  it("handles pick tips without volume", () => {
    assert.equal(planStepLine({ step_id: "pick", primitive_type: "PICK_TIPS" }), "pick PICK_TIPS");
  });
});

describe("downloadable", () => {
  it("returns only kinds with content", () => {
    assert.deepEqual(downloadable({ sop: "", code: "", plan: null }), []);
    assert.deepEqual(downloadable({ sop: "# SOP", code: "", plan: null }), ["sop"]);
    assert.deepEqual(
      downloadable({ sop: "", code: "def run(): pass", plan: { steps: [] } }),
      ["python", "plan"]
    );
    assert.deepEqual(
      downloadable({ sop: "x", code: "y", plan: { steps: [{ step_id: "1" }] } }),
      ["sop", "python", "plan"]
    );
  });
});

describe("downloadSuffix", () => {
  it("marks fail and unevaluable without blocking", () => {
    assert.equal(downloadSuffix("pass"), "");
    assert.equal(downloadSuffix(undefined), "");
    assert.equal(downloadSuffix("fail"), " (checks failed)");
    assert.equal(downloadSuffix("unevaluable"), " (cannot verify)");
  });
});

describe("planSteps", () => {
  it("returns steps array or empty", () => {
    assert.deepEqual(planSteps(null), []);
    assert.deepEqual(planSteps({}), []);
    assert.deepEqual(planSteps({ steps: [{ step_id: "1" }] }), [{ step_id: "1" }]);
  });
});

describe("robot switch downloads", () => {
  it("lists only the new snapshot files", () => {
    assert.deepEqual(
      downloadable({ sop: "# OT SOP", code: "def run(): pass", plan: null }),
      ["sop", "python"]
    );
    assert.deepEqual(
      downloadable({ sop: "# HAM SOP", code: "", plan: { steps: [{ step_id: "1" }] } }),
      ["sop", "plan"]
    );
  });
});
