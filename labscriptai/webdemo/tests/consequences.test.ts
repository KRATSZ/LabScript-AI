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

  it("maps Fluent compile stages to bench consequences and keeps mapping detail", () => {
    assert.match(formatReason("compile_state_machine"), /spraying or nothing happens/i);
    assert.match(formatReason("state_machine"), /spraying or nothing happens/i);
    const mapping = collectConsequences({
      sim: { ok: true },
      logicpass: { outcome: "pass" },
      compile: {
        ok: false,
        stage: "mapping",
        error: "Step 2 ASPIRATE source plate:Z9 is not on the worktable.",
        hint: "Declare plate in resources[].",
      },
    });
    assert.ok(mapping.length >= 1);
    assert.match(mapping[0], /does not match the Fluent deck/i);
    assert.match(mapping[0], /plate:Z9/);
    const state = collectConsequences({
      sim: { ok: true },
      logicpass: { outcome: "pass" },
      compile: {
        ok: false,
        stage: "state_machine",
        error: "Step 2 aspirates before any PICK_TIPS — the head has no tips on.",
        hint: "Add a PICK_TIPS step before ASPIRATE.",
      },
    });
    assert.match(state[0], /spraying or nothing happens/i);
    assert.equal(state[0].includes("Add a PICK_TIPS"), false);
    const internal = collectConsequences({
      sim: { ok: true },
      logicpass: { outcome: "pass" },
      compile: { ok: false, stage: "internal", error: "Fluent compiler timed out." },
    });
    assert.match(internal[0], /no worklist was produced/i);
  });

  it("maps PLR sim exception classes to bench consequence plus a fix, never the class name", () => {
    const cases: Array<{ err: string; bench: RegExp; fix: RegExp }> = [
      {
        err: "NoTipError: Channel 0 does not have a tip.",
        bench: /nothing transfers/i,
        fix: /PICK_TIPS/,
      },
      {
        err: "HasTipError: Channel 0 already has a tip.",
        bench: /crash or a stuck tip/i,
        fix: /Drop the current tip/i,
      },
      {
        err: "TooLittleVolumeError: Container has 10 µL free, trying to add 50.",
        bench: /spill/i,
        fix: /Lower the volume/i,
      },
      {
        err: "TooLittleLiquidError: Container has 10 µL, trying to aspirate 50.",
        bench: /air gets aspirated/i,
        fix: /more reagent/i,
      },
      {
        err: "ResourceNotFoundError: Resource 'source' was not found.",
        bench: /cannot find it/i,
        fix: /resources\[\]/,
      },
      {
        err: "NoLocationError: Resource 'plate' has no location.",
        bench: /cannot go there/i,
        fix: /slot/i,
      },
      {
        err: "KeyError: 'Z9'",
        bench: /not on that plate/i,
        fix: /A1–H12|A1-H12|A1/,
      },
      {
        err: "ValueError: not enough values to unpack (expected 2)",
        bench: /cannot find it/i,
        fix: /plate:A1/,
      },
      {
        err: "AttributeError: 'NoneType' object has no attribute 'aspirate'",
        bench: /cannot run as written/i,
        fix: /tip order, well names, and volumes/i,
      },
    ];
    for (const { err, bench, fix } of cases) {
      const text = formatIssue(err);
      assert.match(text, bench, err);
      assert.match(text, fix, err);
      assert.equal(text.includes(err.split(":")[0]), false, err);
      assert.equal(text.includes("LP-"), false, err);
    }
    assert.match(formatReason("planir_package_missing"), /^Cannot verify:/);
    assert.match(formatReason("plan_cli_spawn_failed"), /^Cannot verify:/);
  });
});
