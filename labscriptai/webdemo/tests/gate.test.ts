import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  fabLit,
  checkStatus,
  forceRaiseOnlySim,
  inspectAnalyze,
  looksLikeRaiseOnly,
  logicpassFromPlanCli,
  refuseEmptySop,
  sanitizeLogicpass,
  shouldRunLlmreview,
  skippedLogic,
  unevaluableLogic,
  wrapChecks,
  animationAllowed,
  compactChecks,
  isPatchBudgetRefusal,
  isReviewMismatch,
  isReviewerUnavailable,
  isInventedLihaTipSizeFinding,
  needsPatch,
  patchCapHit,
  patchInstruction,
  withCompile,
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

  it("logicpassFromPlanCli keeps skipped on sim fail unless deck failed", () => {
    const skipped = logicpassFromPlanCli(simFail, { outcome: "skipped", reason: "sim_failed" });
    assert.equal(skipped.outcome, "skipped");
    const overflow = logicpassFromPlanCli(simFail, {
      outcome: "fail",
      logic_pass: false,
      issues: [{ code: "LP-OVERFLOW" }],
    });
    assert.equal(overflow.outcome, "fail");
    assert.equal((overflow.issues as Array<{ code: string }>)[0]?.code, "LP-OVERFLOW");
    const pass = logicpassFromPlanCli(simOk, {
      outcome: "pass",
      logic_pass: true,
      final_pass_v2: true,
    });
    assert.equal(pass.outcome, "pass");
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
  it("next=patch when FAB is dark; review-only mismatch does not patch", () => {
    const done = wrapChecks(simOk, lpPass, { issues: [] });
    assert.equal(done.fab.lit, true);
    assert.equal(compactChecks(done).next, "done");
    assert.equal(compactChecks(done).status, "pass");
    assert.equal(compactChecks(done).download, "ready");
    assert.equal(needsPatch(done), false);

    const patchSim = wrapChecks(simFail, skippedLogic("sim_failed"), { issues: [] });
    assert.equal(patchSim.fab.lit, false);
    assert.equal(compactChecks(patchSim).next, "patch");

    const patchLp = wrapChecks(simOk, lpFail, { issues: [] });
    const compactLp = compactChecks(patchLp);
    assert.equal(compactLp.next, "patch");
    assert.equal(compactLp.status, "fail");
    assert.equal(compactLp.download, "withheld");
    assert.match(compactLp.hint || "", /withheld/i);
    assert.match(compactLp.hint || "", /do not say \.gwl/i);
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
      findings: [{ claim: "destination volume differs", suggestion: "use 50 uL" }],
    });
    assert.equal(withReview.status, "fail");
    assert.equal(withReview.fab.lit, false);
    assert.equal(needsPatch(withReview), false);
    assert.equal(isReviewMismatch(withReview.llmreview), true);
    const compactReview = compactChecks(withReview);
    assert.equal(compactReview.next, "done");
    assert.equal(compactReview.review.match, false);
    assert.equal(Object.keys(compactReview)[0], "review");
    assert.ok(compactReview.review.findings.length >= 1);
    assert.match(compactReview.consequences[0] || "", /destination volume/i);
    assert.match(compactReview.hint || "", /review mismatch.*destination volume/i);
    assert.match(compactReview.hint || "", /artifacts and animation are blocked/i);
    assert.equal(compactChecks(withReview, 1).next, "done");
    assert.equal(animationAllowed(withReview, 1), false);
  });

  it("reviewer_exception is unavailable: no patch, no mismatch, does not block animation", () => {
    const exception = wrapChecks(simOk, lpPass, { issues: [] }, {
      match: false,
      reason: "llmreview_cli_bad_json",
      findings: [
        {
          claim: "reviewer_exception",
          evidence: "boom",
          suggestion: "Return JSON {match, findings}.",
        },
      ],
    });
    assert.equal(exception.fab.lit, true);
    assert.equal(exception.status, "pass");
    assert.equal(isReviewerUnavailable(exception.llmreview), true);
    assert.equal(isReviewMismatch(exception.llmreview), false);
    assert.equal(needsPatch(exception), false);
    const compact = compactChecks(exception);
    assert.equal(compact.next, "done");
    assert.equal(compact.review.status, "unavailable");
    assert.equal(compact.review.match, undefined);
    assert.match(compact.review.findings[0] || "", /semantic review is unverified/i);
    assert.match(compact.hint || "", /semantic review is unverified/i);
    assert.match(compact.hint || "", /not a mismatch/i);
    assert.match(compact.hint || "", /does not block/i);
    assert.equal(compact.consequences.some((line) => /reviewer_exception/i.test(line)), false);
    assert.ok(compact.consequences.some((line) => /Cannot verify/.test(line)));
    assert.doesNotMatch(patchInstruction(exception), /patch even if simulation passed/);
    assert.doesNotMatch(patchInstruction(exception), /reviewer_exception/);
    assert.equal(animationAllowed(exception, 1), true);
    assert.equal(animationAllowed(exception, 0), false);
  });

  it("does not fail review when the reviewer treats LiHa 1000 as a 1000 µL DiTi rack", () => {
    const invented = {
      severity: "error" as const,
      claim:
        "Tip type does not match the stated intent: the SOP uses a 200 µL DiTi tip rack, but the intent specifies 1000 µL DiTi.",
      evidence:
        "Intent: '1000 µL DiTi'. Generated SOP deck: '1 → tecan_diti_200ul_tiprack'; step 1: 'pick up new 200 µL DiTi from slot 1'.",
      suggestion: "Change the tip rack and pickup to 1000 µL DiTi to match the requested setup.",
    };
    assert.equal(isInventedLihaTipSizeFinding(invented), true);
    const checks = wrapChecks(simOk, lpPass, { issues: [] }, {
      match: false,
      findings: [invented],
    });
    assert.equal(checks.llmreview?.match, true);
    assert.equal(isReviewMismatch(checks.llmreview), false);
    assert.equal(checks.status, "pass");
    assert.equal(checks.fab.lit, true);
    const compiled = withCompile(checks, { ok: true, command_count: 6 });
    assert.equal(compiled.status, "pass");

    const volume = wrapChecks(simOk, lpPass, { issues: [] }, {
      match: false,
      findings: [{ claim: "destination volume differs", suggestion: "use 50 uL" }],
    });
    assert.equal(volume.status, "fail");
    assert.equal(isReviewMismatch(volume.llmreview), true);

    const quotedIntent = wrapChecks(simOk, lpPass, { issues: [] }, {
      match: false,
      findings: [
        {
          claim: "destination volume differs from the chosen 50 µL transfer",
          evidence:
            "Intent: 'liha_1000 is the LiHa pipette. Assumed Tecan tips are 200 µL DiTi. Transfer 50 µL'. SOP dispenses 250 µL.",
          suggestion: "use 50 uL not 250 uL",
        },
      ],
    });
    assert.equal(isInventedLihaTipSizeFinding(quotedIntent.llmreview?.findings?.[0] ?? {}), false);
    assert.equal(quotedIntent.llmreview?.match, false);
    assert.equal(quotedIntent.status, "fail");
    assert.equal(isReviewMismatch(quotedIntent.llmreview), true);

    const mixed = {
      severity: "error" as const,
      claim:
        "Tip type does not match: the SOP uses a 200 µL DiTi tip rack, but the intent specifies 1000 µL DiTi; destination volume 250 vs 50.",
      evidence: "SOP dispenses 250 µL. Chosen transfer is 50 µL.",
      suggestion: "Keep the 200 µL DiTi rack and use 50 µL, not 250 µL.",
    };
    assert.equal(isInventedLihaTipSizeFinding(mixed), false);
    const mixedChecks = wrapChecks(simOk, lpPass, { issues: [] }, {
      match: false,
      findings: [mixed],
    });
    assert.equal(mixedChecks.llmreview?.match, false);
    assert.equal(isReviewMismatch(mixedChecks.llmreview), true);
    assert.equal(mixedChecks.status, "fail");
    assert.equal(mixedChecks.fab.lit, false);
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

  it("Tecan compile fail dims FAB and is fail; compile ok does not change Hamilton-style pass", () => {
    const basePass = wrapChecks(simOk, lpPass, { issues: [] });
    assert.equal("compile" in compactChecks(basePass), false);

    const compileFail = withCompile(basePass, {
      ok: false,
      stage: "state_machine",
      error: "Step 2 aspirates before any PICK_TIPS — the head has no tips on.",
      hint: "Add a PICK_TIPS step before ASPIRATE.",
    });
    assert.equal(compileFail.fab.lit, false);
    assert.equal(compileFail.status, "fail");
    assert.equal(needsPatch(compileFail), true);
    const compactFail = compactChecks(compileFail);
    assert.equal(compactFail.next, "patch");
    assert.equal(compactFail.compile?.ok, false);
    assert.equal(compactFail.compile?.stage, "state_machine");
    assert.match(compactFail.compile?.hint || "", /PICK_TIPS/);
    assert.match(patchInstruction(compileFail), /Fluent compile/);
    assert.match(patchInstruction(compileFail), /PICK_TIPS/);

    const compileOk = withCompile(basePass, { ok: true, command_count: 4, warnings: [] });
    assert.equal(compileOk.fab.lit, true);
    assert.equal(compileOk.status, "pass");
    assert.equal(compactChecks(compileOk).compile?.ok, true);
    assert.equal(compactChecks(compileOk).next, "done");

    const plr = wrapChecks(
      { ok: false, reason: "plr_unavailable" },
      skippedLogic("plr_unavailable"),
      { issues: [] }
    );
    const plrCompileOk = withCompile(plr, { ok: true, command_count: 2 });
    assert.equal(plrCompileOk.status, "unevaluable");
    assert.equal(plrCompileOk.fab.lit, false);

    const plrCompileFail = withCompile(plr, {
      ok: false,
      stage: "mapping",
      error: "plate:Z9 is not on the worktable.",
      hint: "Declare the labware in resources[].",
    });
    assert.equal(plrCompileFail.status, "fail");
    assert.equal(plrCompileFail.fab.lit, false);
  });
});
