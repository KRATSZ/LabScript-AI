import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { collectConsequences, formatIssue } from "../server/src/consequences.ts";
import { compactChecks, skippedLogic, wrapChecks, emptyStatepass } from "../server/src/gate.ts";
import { knownHamiltonWellUl } from "../server/src/devices.ts";

function stubPlrFail(error: string, reason = "sim_failed") {
  return wrapChecks(
    { ok: false, reason, errors: [error] },
    skippedLogic(reason),
    emptyStatepass(reason)
  );
}

function assertHuman(lines: string[]) {
  const blob = lines.join(" ");
  assert.ok(lines.length >= 1);
  for (const line of lines) {
    assert.equal(line.includes("LP-"), false, line);
    assert.doesNotMatch(line, /\b(?:NoTip|HasTip|TooLittle|ResourceNotFound|NoLocation|Key|Value|Attribute)Error\b/);
  }
  assert.doesNotMatch(blob, /\bLP-[A-Z]/);
}

describe("Hamilton PLR failure → human consequences", () => {
  it("stubbed PLR shapes compact to bench talk plus a fix", () => {
    const shapes: Array<{ err: string; bench: RegExp; fix: RegExp }> = [
      {
        err: "NoTipError: Channel 0 does not have a tip.",
        bench: /nothing transfers|pipette can get wet/i,
        fix: /PICK_TIPS/,
      },
      {
        err: "HasTipError: Channel 0 already has a tip.",
        bench: /crash or a stuck tip/i,
        fix: /Drop the current tip/i,
      },
      {
        err: "TooLittleVolumeError: not enough free volume in the container",
        bench: /spill/i,
        fix: /Lower the volume|split the transfer/i,
      },
      {
        err: "TooLittleLiquidError: trying to aspirate more than is present",
        bench: /air gets aspirated/i,
        fix: /more reagent/i,
      },
      {
        err: "KeyError: 'Z9'",
        bench: /not on that plate/i,
        fix: /A1/,
      },
      {
        err: "ResourceNotFoundError: Resource 'buffer' was not found",
        bench: /cannot find it/i,
        fix: /resources\[\]/,
      },
      {
        err: "RuntimeError: unexpected tracker state",
        bench: /cannot run as written/i,
        fix: /tip order, well names, and volumes/i,
      },
    ];

    for (const { err, bench, fix } of shapes) {
      const checks = stubPlrFail(err);
      const compact = compactChecks(checks);
      const lines = compact.consequences;
      assertHuman(lines);
      const blob = lines.join(" ");
      assert.match(blob, bench, err);
      assert.match(blob, fix, err);
      assert.equal(compact.fab.lit, false);
      assert.equal(compact.next, "patch");
      assert.equal(compact.sim.ok, false);
      assert.ok(compact.sim.consequence);
      assert.equal((compact.sim.consequence || "").includes("NoTipError"), false);
    }
  });

  it("plr_unavailable is cannot-verify, not a fake pass", () => {
    const checks = stubPlrFail("pylabrobot is not installed (pip install pylabrobot)", "plr_unavailable");
    const compact = compactChecks(checks);
    assert.equal(checks.status, "unevaluable");
    assert.equal(compact.fab.lit, false);
    const blob = compact.consequences.join(" ");
    assert.match(blob, /^Cannot verify:|Cannot verify:/);
    assert.match(blob, /not installed|partial checks/i);
    assert.equal(blob.includes("plr_unavailable"), false);
    assert.equal(blob.includes("LP-"), false);
  });

  it("LogicPass LP-NO-TIP still uses the existing mapping (old key unchanged)", () => {
    const checks = wrapChecks(
      { ok: true },
      {
        outcome: "fail",
        logic_pass: false,
        issues: [{ code: "LP-NO-TIP", detail_text: "ASPIRATE without a tip", step_id: "2" }],
      },
      emptyStatepass()
    );
    const compact = compactChecks(checks);
    assert.match(compact.consequences[0], /contaminate the pipette/i);
    assert.match(compact.consequences[0], /Step 2/);
    assert.equal(compact.consequences[0].includes("LP-NO-TIP"), false);
  });

  it("PLR sim fail still surfaces virtual-deck overflow as a spill", () => {
    const checks = wrapChecks(
      {
        ok: false,
        reason: "sim_failed",
        errors: ["ValueError: invalid literal for int() with base 10: 'IPS'"],
      },
      {
        outcome: "fail",
        logic_pass: false,
        issues: [
          {
            code: "LP-OVERFLOW",
            detail_text: "dispense 500 µL into plate:B1 would exceed 360 µL",
            step_id: "3",
          },
        ],
      },
      emptyStatepass("sim_failed")
    );
    const compact = compactChecks(checks);
    assert.equal(checks.status, "fail");
    assert.equal(compact.fab.lit, false);
    assert.match(compact.consequences.join(" "), /spill/i);
    assert.equal(compact.consequences.join(" ").includes("LP-OVERFLOW"), false);
  });

  it("unknown well capacity stays unevaluable, never a silent pass", () => {
    assert.equal(knownHamiltonWellUl("mystery_custom_plate"), undefined);
    const checks = wrapChecks(
      { ok: true },
      {
        outcome: "unevaluable",
        logic_pass: false,
        reason: "LP-CAPACITY-UNKNOWN",
        issues: [
          {
            code: "LP-CAPACITY-UNKNOWN",
            detail_text: "capacity unknown for plate:B1 — cannot verify overflow",
            step_id: "3",
          },
        ],
      },
      emptyStatepass()
    );
    const compact = compactChecks(checks);
    assert.equal(checks.status, "unevaluable");
    assert.equal(compact.fab.lit, false);
    assert.match(compact.consequences[0], /^Cannot verify:/);
    assert.equal(compact.consequences[0].includes("LP-CAPACITY-UNKNOWN"), false);
  });

  it("collectConsequences never leaks a stubbed PLR class name", () => {
    const lines = collectConsequences({
      sim: {
        ok: false,
        reason: "sim_failed",
        errors: ["NoTipError: Channel 0 does not have a tip.", "HasTipError: already has a tip"],
      },
      logicpass: { outcome: "skipped", reason: "sim_failed" },
    });
    assertHuman(lines);
    assert.ok(lines.some((line) => /PICK_TIPS/.test(line)));
    assert.ok(formatIssue("NoTipError: Channel 0 does not have a tip.").includes("PICK_TIPS"));
  });
});
