import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  CONSEQUENCE_BY_CODE,
  collectConsequences,
  formatIssue,
  formatReason,
} from "../server/src/consequences.ts";

describe("consequences", () => {
  it("maps every covered code to a non-empty sentence with no LP- prefix", () => {
    for (const [code, sentence] of Object.entries(CONSEQUENCE_BY_CODE)) {
      assert.ok(sentence.trim().length > 0, code);
      assert.equal(sentence.includes("LP-"), false, `${code} sentence contains LP-`);
      const rendered = formatReason(code);
      assert.ok(rendered.trim().length > 0, code);
      assert.equal(rendered.includes("LP-"), false, `${code} render contains LP-`);
      if (code === "LP-OVERFLOW" || code === "LP-L4") {
        assert.match(rendered, /spill/i);
      }
    }
  });

  it("unknown code falls back to detail_text without a code prefix", () => {
    const text = formatIssue({
      code: "LP-UNKNOWN-XYZ",
      detail_text: "well A1 is dry",
    });
    assert.equal(text, "well A1 is dry");
    assert.equal(text.includes("LP-"), false);
    const bare = formatReason("NO_SUCH_CODE");
    assert.ok(bare.trim().length > 0);
    assert.equal(bare.includes("NO_SUCH_CODE"), false);
    assert.equal(bare.includes("LP-"), false);
  });

  it("unevaluable codes start with Cannot verify", () => {
    assert.match(formatReason("capacity_unknown"), /^Cannot verify:/);
    assert.match(formatReason("plr_unavailable"), /^Cannot verify:/);
    assert.match(
      formatIssue({
        code: "LP-CAPACITY-UNKNOWN",
        detail_text: "capacity unknown for plate:B1 — cannot verify overflow",
      }),
      /^Cannot verify:/
    );
    assert.equal(formatReason("sim_failed").startsWith("Cannot verify:"), false);
  });

  it("overflow folds detail after the spill sentence", () => {
    const text = formatIssue({
      code: "LP-OVERFLOW",
      detail_text: "dispense 50 µL into plate:B1 would exceed 200 µL",
      step_id: "3",
    });
    assert.match(text, /spill/i);
    assert.match(text, /plate:B1/);
    assert.match(text, /Step 3/);
    assert.equal(text.includes("LP-OVERFLOW"), false);
  });

  it("collectConsequences is consequence-first, deduped, and capped", () => {
    const overflow = {
      code: "LP-OVERFLOW",
      detail_text: "dispense 250 µL into plate:A1 would exceed 200 µL",
    };
    const list = collectConsequences({
      sim: { ok: true },
      logicpass: { outcome: "fail", issues: [overflow, overflow, overflow, overflow, overflow, overflow] },
    });
    assert.ok(list.length >= 1);
    assert.ok(list.length <= 5);
    assert.equal(list.length, 1);
    assert.match(list[0], /spill/i);
    for (const line of list) assert.equal(line.includes("LP-"), false);
  });
});
