import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ticksFromSlotRects } from "../web/src/flexDeckTicks.ts";

function grid(): Array<{ x: number; y: number; w: number; h: number }> {
  const cells: Array<{ x: number; y: number; w: number; h: number }> = [];
  // Screen Y grows down. A (back) is the top row.
  for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 3; c++) {
      cells.push({ x: 80 + c * 130, y: 40 + r * 90, w: 120, h: 80 });
    }
  }
  return cells;
}

describe("flexDeckTicks", () => {
  it("puts A at the top row and 1 at the left column", () => {
    const ticks = ticksFromSlotRects(grid());
    assert.ok(ticks);
    assert.deepEqual(
      ticks.rows.map((tick) => tick.label),
      ["A", "B", "C", "D"]
    );
    assert.ok(ticks.rows[0].y < ticks.rows[3].y);
    assert.deepEqual(
      ticks.cols.map((tick) => tick.label),
      ["1", "2", "3"]
    );
    assert.ok(ticks.cols[0].x < ticks.cols[2].x);
    assert.ok(ticks.rows[0].x < ticks.cols[0].x);
    assert.ok(ticks.cols[0].y > ticks.rows[3].y);
  });

  it("ignores a small A1 expansion pad above the back row", () => {
    const cells = grid();
    cells.push({ x: 80, y: 0, w: 120, h: 30 });
    const ticks = ticksFromSlotRects(cells);
    assert.ok(ticks);
    assert.equal(ticks.rows[0].label, "A");
    assert.ok(ticks.rows[0].y > 40);
  });
});
