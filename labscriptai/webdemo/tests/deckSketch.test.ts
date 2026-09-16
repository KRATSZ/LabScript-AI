import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { deckLabware, deckSketchRows } from "../web/src/deckSketch.ts";

describe("deckSketchRows", () => {
  it("draws the OT-2 11-slot plus trash grid", () => {
    const rows = deckSketchRows("OT-2", {
      "1": "opentrons_96_tiprack_300ul",
      "2": "nest_96_wellplate_200ul_flat",
      "3": "nest_12_reservoir_15ml",
    });
    assert.deepEqual(rows[0], ["10", "11", "trash"]);
    assert.deepEqual(rows[3], ["1", "2", "3"]);
    assert.equal(deckLabware({ "1": "tips" }, "1"), "tips");
    assert.equal(deckLabware({ "1": "tips" }, "10"), "");
  });

  it("draws Flex A–D / 1–3", () => {
    const rows = deckSketchRows("Flex", { A1: "tips", D2: "plate" });
    assert.deepEqual(rows[0], ["A3", "B3", "C3", "D3"]);
    assert.deepEqual(rows[2], ["A1", "B1", "C1", "D1"]);
  });
});
