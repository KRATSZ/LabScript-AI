import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  fabLit,
  checkStatus,
  forceRaiseOnlySim,
  inspectAnalyze,
  looksLikeRaiseOnly,
  refuseEmptySop,
  sanitizeLogicpass,
  shouldRunLlmreview,
  skippedLogic,
  unevaluableLogic,
  wrapChecks,
  compactChecks,
  isPatchBudgetRefusal,
  needsPatch,
  patchCapHit,
  patchInstruction,
  type LogicPassResult,
  type SimResult,
} from "../server/src/gate.ts";

const simOk: SimResult = { ok: true };
const simFail: SimResult = { ok: false, reason: "sim_failed" };
const lpPass: LogicPassResult = { outcome: "pass", logic_pass: true, final_pass_v2: true };
const lpFail: LogicPassResult = { outcome: "fail", logic_pass: false, issues: [{ code: "LP-L1" }] };
const lpUneval: LogicPassResult = { outcome: "unevaluable", logic_pass: false };

describe("FAB gate", () => {
  it("lights only when sim.ok && outcome pass && logic_pass && final_pass_v2 true", () => {
    assert.equal(fabLit(simOk, { outcome: "pass", logic_pass: true }), false);
    assert.equal(fabLit(simOk, lpPass), true);
    assert.equal(wrapChecks(simOk, lpPass, { issues: [] }).fab.lit, true);
  });

  it("sanitizes CLI outcomes and honors final_pass_v2", () => {
    const passUpper = sanitizeLogicpass({
      outcome: "PASS",
      logic_pass: true,
      final_pass_v2: true,
    });
    assert.equal(passUpper.outcome, "unevaluable");
    assert.equal(passUpper.logic_pass, false);
    assert.equal(wrapChecks(simOk, passUpper, { issues: [] }).fab.lit, false);

    const passButNoFinal = sanitizeLogicpass({
      outcome: "pass",
      logic_pass: true,
      final_pass_v2: false,
    });
    assert.equal(passButNoFinal.outcome, "unevaluable");
    assert.equal(passButNoFinal.final_pass_v2, false);
    assert.equal(fabLit(simOk, passButNoFinal), false);
    assert.equal(
      fabLit(simOk, { outcome: "pass", logic_pass: true, final_pass_v2: false }),
      false
    );

    const good = sanitizeLogicpass({
      outcome: "pass",
      logic_pass: true,
      final_pass_v2: true,
    });
    assert.equal(good.outcome, "pass");
    assert.equal(good.logic_pass, true);
    assert.equal(good.final_pass_v2, true);
    assert.equal(wrapChecks(simOk, good, { issues: [] }).fab.lit, true);

    const impliedFinal = sanitizeLogicpass({
      outcome: "pass",
      logic_pass: true,
    });
    assert.equal(impliedFinal.final_pass_v2, true);
    assert.equal(fabLit(simOk, impliedFinal), true);
  });

  it("stays gray on sim fail and does not mark unevaluable", () => {
    const checks = wrapChecks(simFail, skippedLogic("sim_failed"), { issues: [] });
    assert.equal(checks.fab.lit, false);
    assert.equal(checks.logicpass.outcome, "skipped");
    assert.notEqual(checks.logicpass.outcome, "unevaluable");
    assert.equal(fabLit(simFail, lpPass), false);
  });

  it("stays gray on LogicPass fail", () => {
    assert.equal(fabLit(simOk, lpFail), false);
  });

  it("stays gray on unevaluable", () => {
    assert.equal(fabLit(simOk, lpUneval), false);
    assert.equal(fabLit(simOk, unevaluableLogic("missing")), false);
  });

  it("never lights on sim-only (statepass is not a light)", () => {
    const checks = wrapChecks(simOk, unevaluableLogic("missing_analyze_artifact"), {
      issues: [{ code: "ledger" }],
      coverage: { evaluable_denominator: 3 },
    });
    assert.equal(checks.fab.lit, false);
    assert.ok(checks.statepass.issues);
  });

  it("analyze errors and empty commands are unevaluable, FAB gray", () => {
    assert.deepEqual(inspectAnalyze({ errors: [{ detail: "boom" }], commands: [{}] }), {
      ok: false,
      reason: "analyze_has_errors",
    });
    assert.deepEqual(inspectAnalyze({ commands: [] }), {
      ok: false,
      reason: "missing_commands",
    });
    assert.deepEqual(inspectAnalyze(null), { ok: false, reason: "missing_analyze_artifact" });
    assert.equal(inspectAnalyze({ commands: [{ commandType: "aspirate" }] }).ok, true);
    assert.equal(
      wrapChecks(simOk, unevaluableLogic("analyze_has_errors"), { issues: [] }).fab.lit,
      false
    );
    assert.equal(
      wrapChecks(simOk, unevaluableLogic("missing_commands"), { issues: [] }).fab.lit,
      false
    );
  });
});

describe("raise-only / empty sop", () => {
  it("detects raise-only scripts", () => {
    assert.equal(looksLikeRaiseOnly("raise RuntimeError('no')\n"), true);
    assert.equal(looksLikeRaiseOnly(""), true);
    const raiseInRun = `
from opentrons import protocol_api

def run(protocol):
    """doc"""
    # comment
    raise RuntimeError("ok")
`;
    assert.equal(looksLikeRaiseOnly(raiseInRun), true);
    const forged = forceRaiseOnlySim({ ok: true, reason: "success" });
    const raiseChecks = wrapChecks(forged, skippedLogic("raise_only"), { issues: [] });
    assert.equal(forged.ok, false);
    assert.equal(forged.reason, "raise_only");
    assert.equal(raiseChecks.sim.ok, false);
    assert.equal(raiseChecks.logicpass.outcome, "skipped");
    assert.equal(raiseChecks.fab.lit, false);
    assert.equal(
      looksLikeRaiseOnly(
        "from opentrons import protocol_api\n\ndef run(protocol):\n    protocol.home()\n"
      ),
      false
    );
    assert.equal(
      looksLikeRaiseOnly(
        "from opentrons import protocol_api\n\ndef run(protocol):\n    protocol.home()\n    raise RuntimeError('x')\n"
      ),
      false
    );
  });

  it("refuses empty sop", () => {
    assert.match(refuseEmptySop("") || "", /refused/);
    assert.match(refuseEmptySop("none") || "", /refused/);
    assert.match(refuseEmptySop(undefined) || "", /refused/);
    assert.equal(refuseEmptySop("# SOP\n1. Aspirate"), null);
  });
});

describe("llmreview skip helpers", () => {
  it("skips review on sim fail / raise-only / skipped", () => {
    assert.equal(shouldRunLlmreview(simFail, skippedLogic("sim_failed")), false);
    assert.equal(shouldRunLlmreview(simFail, lpPass), false);
    assert.equal(
      shouldRunLlmreview({ ok: false, reason: "raise_only" }, skippedLogic("raise_only")),
      false
    );
  });

  it("skips review on LogicPass fail and package/cli errors", () => {
    assert.equal(shouldRunLlmreview(simOk, lpFail), false);
    assert.equal(shouldRunLlmreview(simOk, unevaluableLogic("logicpass_package_missing")), false);
    assert.equal(shouldRunLlmreview(simOk, unevaluableLogic("logicpass_cli_spawn_failed")), false);
    assert.equal(shouldRunLlmreview(simOk, unevaluableLogic("logicpass_cli_bad_json")), false);
    assert.equal(
      shouldRunLlmreview({ ok: false, reason: "plr_unavailable" }, skippedLogic("plr_unavailable")),
      false
    );
    assert.equal(shouldRunLlmreview(simOk, unevaluableLogic("plr_unavailable")), false);
  });

  it("runs review on pass or unevaluable missing_analyze", () => {
    assert.equal(shouldRunLlmreview(simOk, lpPass), true);
    assert.equal(shouldRunLlmreview(simOk, unevaluableLogic("missing_analyze_artifact")), true);
    assert.equal(shouldRunLlmreview(simOk, unevaluableLogic("analyze_has_errors")), false);
  });
});

describe("compactChecks", () => {
  it("next=patch when FAB is dark or llmreview.match is false", () => {
    const done = wrapChecks(simOk, lpPass, { issues: [] });
    assert.equal(done.fab.lit, true);
    assert.equal(compactChecks(done).next, "done");
    assert.equal(needsPatch(done), false);

    const patchSim = wrapChecks(simFail, skippedLogic("sim_failed"), { issues: [] });
    assert.equal(patchSim.fab.lit, false);
    assert.equal(compactChecks(patchSim).next, "patch");

    const patchLp = wrapChecks(simOk, lpFail, { issues: [] });
    const compactLp = compactChecks(patchLp);
    assert.equal(compactLp.next, "patch");
    assert.equal(compactLp.logicpass.outcome, "fail");
    assert.ok(compactLp.logicpass.issues.length >= 1);
    assert.equal(compactLp.logicpass.issues.some((line) => line.includes("LP-")), false);
    assert.ok(compactLp.consequences.length >= 1);
    assert.equal(compactLp.consequences.some((line) => line.includes("LP-")), false);

    const patchSimCompact = compactChecks(patchSim);
    assert.match(patchSimCompact.sim.consequence || "", /cannot run/i);
    assert.equal("reason" in patchSimCompact.sim, false);

    const overflow = wrapChecks(
      simOk,
      {
        outcome: "fail",
        logic_pass: false,
        issues: [{ code: "LP-OVERFLOW", detail_text: "dispense 50 µL into plate:B1 would exceed 200 µL", step_id: "3" }],
      },
      { issues: [] }
    );
    assert.match(overflow.consequences?.[0] || "", /spill/i);
    assert.equal(overflow.consequences?.[0]?.includes("LP-"), false);
    const patch = patchInstruction(overflow);
    assert.match(patch, /spill/i);
    assert.doesNotMatch(patch, /LP-OVERFLOW/);
    assert.doesNotMatch(patch, /Sim failed:/);

    const uneval = wrapChecks(simOk, unevaluableLogic("capacity_unknown"), { issues: [] });
    assert.match(uneval.consequences?.[0] || "", /^Cannot verify:/);
    const simUneval = wrapChecks(
      { ok: false, reason: "plr_unavailable" },
      skippedLogic("plr_unavailable"),
      { issues: [] }
    );
    assert.match(simUneval.consequences?.[0] || "", /^Cannot verify:/);

    const withReview = wrapChecks(simOk, lpPass, { issues: [] }, {
      match: false,
      findings: [{ claim: "volume", suggestion: "use 50 uL" }],
    });
    assert.equal(withReview.fab.lit, true);
    assert.equal(needsPatch(withReview), true);
    assert.equal(compactChecks(withReview).next, "patch");
    assert.equal(compactChecks(withReview).review.match, false);
    assert.ok(compactChecks(withReview).review.findings.length >= 1);
    assert.equal(compactChecks(withReview, 1).next, "done");
  });

  it("patchCapHit after the one allowed patch while checks still fail", () => {
    const fail = wrapChecks(simFail, skippedLogic("sim_failed"), { issues: [] });
    const pass = wrapChecks(simOk, lpPass, { issues: [] });
    assert.equal(patchCapHit(0, fail), false);
    assert.equal(patchCapHit(1, fail), true);
    assert.equal(patchCapHit(1, undefined), true);
    assert.equal(patchCapHit(1, pass), false);
    assert.equal(isPatchBudgetRefusal({ refused: true }), true);
    assert.equal(isPatchBudgetRefusal({ payload: {} }), false);
  });
});

describe("checkStatus", () => {
  it("maps pass, fail, unevaluable, sim-failed, and plr-unavailable", () => {
    const pass = wrapChecks(simOk, lpPass, { issues: [] });
    assert.equal(pass.status, "pass");
    assert.equal(checkStatus(pass), "pass");

    const fail = wrapChecks(simOk, lpFail, { issues: [] });
    assert.equal(fail.status, "fail");
    assert.equal(fail.fab.lit, false);

    const uneval = wrapChecks(simOk, unevaluableLogic("missing_analyze_artifact"), { issues: [] });
    assert.equal(uneval.status, "unevaluable");
    assert.equal(uneval.fab.lit, false);

    const simFailed = wrapChecks(simFail, skippedLogic("sim_failed"), { issues: [] });
    assert.equal(simFailed.status, "fail");
    assert.equal(simFailed.logicpass.outcome, "skipped");

    const plr = wrapChecks(
      { ok: false, reason: "plr_unavailable" },
      skippedLogic("plr_unavailable"),
      { issues: [] }
    );
    assert.equal(plr.status, "unevaluable");
    assert.equal(plr.fab.lit, false);

    const invalid = wrapChecks(
      { ok: false, reason: "invalid_plan" },
      skippedLogic("invalid_plan"),
      { issues: [] }
    );
    assert.equal(invalid.status, "fail");
  });
});
