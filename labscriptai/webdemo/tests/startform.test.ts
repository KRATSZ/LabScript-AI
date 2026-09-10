import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { EXAMPLES } from "../web/src/startExamples.ts";

describe("StartForm examples", () => {
  it("three chips fill goal and optional notes, and do not imply auto-submit", () => {
    assert.equal(EXAMPLES.length, 3);
    assert.equal(EXAMPLES[0].label, "Transfer 50 µL A1→B1");
    assert.equal(EXAMPLES[0].goal, "Transfer 50 µL from well A1 to B1 on a 96-well plate.");
    assert.equal(EXAMPLES[0].doc, "");
    assert.equal(EXAMPLES[1].label, "Prepare a PCR mix");
    assert.match(EXAMPLES[1].goal, /PCR mix/);
    assert.match(EXAMPLES[1].doc, /master mix/);
    assert.equal(EXAMPLES[2].label, "No protocol — common deck");
    assert.match(EXAMPLES[2].goal, /common deck/);
    const blob = EXAMPLES.map((item) => `${item.label}\n${item.goal}\n${item.doc}`).join("\n");
    assert.doesNotMatch(blob, /standard3|standard 3-slot/i);
    assert.match(EXAMPLES[2].goal, /Hamilton/);
    assert.match(EXAMPLES[2].goal, /Tecan/);
  });
});
