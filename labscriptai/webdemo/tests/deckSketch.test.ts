import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  deckLabware,
  deckSketchAxes,
  deckSketchRows,
  hamiltonStarSketch,
  hamiltonVantageSketch,
  sketchOriginSlot,
  usesStarSketch,
  usesVantageSketch,
} from "../web/src/deckSketch.ts";

describe("deckSketchRows", () => {
  it("draws the OT-2 11-slot plus trash grid with slot 10 at the back-left", () => {
    const rows = deckSketchRows("OT-2", {
      "1": "opentrons_96_tiprack_300ul",
      "2": "nest_96_wellplate_200ul_flat",
      "3": "nest_12_reservoir_15ml",
    });
    assert.deepEqual(rows[0], ["10", "11", "trash"]);
    assert.deepEqual(rows[3], ["1", "2", "3"]);
    assert.equal(sketchOriginSlot("OT-2"), "10");
    assert.equal(deckLabware({ "1": "tips" }, "1"), "tips");
    assert.equal(deckLabware({ "1": "tips" }, "10"), "");
  });

  it("draws Flex with A1 at the back-left, letters as rows and numbers as columns", () => {
    const rows = deckSketchRows("Flex", { A1: "tips", D2: "plate" });
    assert.deepEqual(rows[0], ["A1", "A2", "A3"]);
    assert.deepEqual(rows[3], ["D1", "D2", "D3"]);
    assert.equal(rows[0][0], "A1");
    assert.equal(sketchOriginSlot("Flex"), "A1");
    const axes = deckSketchAxes("Flex");
    assert.deepEqual(axes?.rows, ["A", "B", "C", "D"]);
    assert.deepEqual(axes?.cols, ["1", "2", "3"]);
    assert.equal(deckSketchAxes("OT-2"), null);
  });

  it("draws a STAR carrier layout instead of three OT-style slots", () => {
    const carriers = hamiltonStarSketch({
      "1": "hamilton_96_tiprack_300ul",
      "2": "corning_96_wellplate_360ul_flat",
      "3": "nest_12_reservoir_15ml",
    });
    const sites = carriers.flatMap((carrier) => carrier.sites);
    assert.ok(carriers.length >= 4);
    assert.ok(sites.length >= 10);
    assert.equal(carriers[0].id, "tip_car");
    assert.equal(carriers[0].sites.length, 5);
    assert.ok(carriers[0].sites.every((site) => site.labware));
    const waste = carriers.find((carrier) => carrier.id === "waste");
    assert.ok(waste);
    assert.equal(waste.sites.length, 3);
    assert.ok(waste.sites.every((site) => !site.labware));
    assert.equal(waste.sites[0].label, "Trash");
  });

  it("draws a Vantage 1.3 m rail bed instead of three OT-style slots or STAR carriers", () => {
    const sketch = hamiltonVantageSketch({
      "1": "hamilton_96_tiprack_300ul",
      "2": "corning_96_wellplate_360ul_flat",
      "3": "nest_12_reservoir_15ml",
    });
    assert.equal(sketch.size, "1.3 m");
    assert.equal(sketch.rails, 54);
    assert.equal(sketch.items.length, 4);
    assert.deepEqual(
      sketch.items.map((item) => item.label),
      ["Tips", "Plate", "Reservoir", "Trash"]
    );
    assert.ok(sketch.items[0].labware);
    assert.equal(sketch.items[3].label, "Trash");
    assert.equal(usesStarSketch("Vantage"), false);
    assert.equal(usesVantageSketch("Vantage"), true);
    assert.equal(usesVantageSketch("Hamilton"), false);
  });
});
