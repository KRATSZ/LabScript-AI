import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  DOWNLOAD_LABELS,
  downloadHint,
  downloadable,
  downloadSuffix,
  planStepLine,
  planSteps,
} from "../web/src/artifacts.ts";

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

  it("shows tip rack and well after TIPS:A1 was stored as A1", () => {
    assert.equal(
      planStepLine({
        step_id: "1",
        primitive_type: "PICK_TIPS",
        tip_rack: "tips",
        tip_positions: ["A1"],
      }),
      "1 PICK_TIPS tips:A1"
    );
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
    assert.deepEqual(
      downloadable({
        sop: "# Tecan SOP",
        code: "",
        plan: { steps: [{ step_id: "1" }] },
        artifacts: { worklistGwl: "C; plan\nA;plate;;;A1;;50;Water Free Single;;1;\nB;\n" },
      }),
      ["sop", "plan", "gwl"]
    );
    assert.deepEqual(
      downloadable({ sop: "", code: "", plan: null, artifacts: { worklistGwl: "  " } }),
      []
    );
  });

  it("lists OT-2 / Flex / Hamilton / Tecan deliverables by device", () => {
    assert.deepEqual(
      downloadable({ robot: "OT-2", sop: "# SOP", code: "def run(): pass", plan: null }),
      ["sop", "python"]
    );
    assert.deepEqual(
      downloadable({ robot: "Flex", sop: "# SOP", code: "def run(): pass", plan: null }),
      ["sop", "python"]
    );
    assert.deepEqual(
      downloadable({
        robot: "OT-2",
        sop: "# SOP",
        code: "def run(): pass",
        plan: { steps: [{ step_id: "1" }] },
      }),
      ["sop", "python"]
    );
    assert.deepEqual(
      downloadable({
        robot: "Hamilton",
        sop: "# HAM SOP",
        code: "def leftover(): pass",
        plan: { steps: [{ step_id: "1" }] },
        artifacts: { hamiltonScript: "async def main():\n    pass\n" },
      }),
      ["sop", "plan", "plr"]
    );
    assert.deepEqual(
      downloadable({
        robot: "Vantage",
        sop: "# VAN SOP",
        code: "def leftover(): pass",
        plan: { steps: [{ step_id: "1" }] },
        artifacts: { hamiltonScript: "async def main():\n    pass\n" },
      }),
      ["sop", "plan", "plr"]
    );
    assert.deepEqual(
      downloadable({
        robot: "Tecan",
        sop: "# SOP",
        code: "",
        plan: { steps: [{ step_id: "1" }] },
        artifacts: { worklistGwl: "C;A;\nB;\n" },
      }),
      ["sop", "plan", "gwl"]
    );
    assert.deepEqual(
      downloadable({
        robot: "Tecan",
        sop: "# SOP",
        code: "",
        plan: { steps: [{ step_id: "1" }] },
        artifacts: { worklistGwl: "" },
      }),
      ["sop", "plan"]
    );
    assert.deepEqual(
      downloadable({
        robot: "OT-2",
        sop: "# SOP",
        code: "",
        plan: { steps: [{ step_id: "1" }] },
      }),
      ["sop", "plan"]
    );
    assert.deepEqual(
      downloadable({
        robot: "OT-2",
        sop: "# SOP uses a reservoir",
        code: "def run(): pass",
        plan: null,
        downloads_withheld: true,
      }),
      []
    );
  });
});

describe("downloadSuffix", () => {
  it("marks pass, fail, and unevaluable", () => {
    assert.equal(downloadSuffix("pass"), " (checks passed)");
    assert.equal(downloadSuffix(undefined), "");
    assert.equal(downloadSuffix("fail"), " (checks failed)");
    assert.equal(downloadSuffix("unevaluable"), " (cannot verify)");
  });
});

describe("downloadHint", () => {
  it("explains each file next to the download", () => {
    assert.match(downloadHint("python", "OT-2"), /opentrons_simulate/);
    assert.match(downloadHint("gwl", "Tecan"), /FluentControl/);
    assert.match(downloadHint("plan", "Hamilton"), /robot script/);
    assert.match(downloadHint("plr", "Hamilton"), /STAR-connected PC/);
    assert.match(downloadHint("plr", "Vantage"), /Vantage-connected PC/);
    assert.equal(DOWNLOAD_LABELS.plan, "Steps");
    assert.equal(DOWNLOAD_LABELS.gwl, "Fluent worklist");
    assert.equal(DOWNLOAD_LABELS.plr, "Robot script");
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
      downloadable({ robot: "OT-2", sop: "# OT SOP", code: "def run(): pass", plan: null }),
      ["sop", "python"]
    );
    assert.deepEqual(
      downloadable({ robot: "Hamilton", sop: "# HAM SOP", code: "", plan: { steps: [{ step_id: "1" }] } }),
      ["sop", "plan"]
    );
  });
});
