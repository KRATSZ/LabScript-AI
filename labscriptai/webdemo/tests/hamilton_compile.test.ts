import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  attachHamiltonCompile,
  parseHamiltonCompileStdout,
  runHamiltonCompile,
  type HamiltonCompileResult,
  type StdinJsonSpawn,
} from "../server/src/backend.ts";
import { emptyStatepass, skippedLogic, wrapChecks } from "../server/src/gate.ts";

const PLAN = { schema: "bpl.plan_ir.lh.v0", steps: [{ step_id: "1" }] };
const SCRIPT = "async def main():\n    await lh.pick_up_tips(tips['A1'])\n";

const passChecks = () =>
  wrapChecks(
    { ok: true },
    { outcome: "pass", logic_pass: true, final_pass_v2: true },
    emptyStatepass()
  );

describe("parseHamiltonCompileStdout", () => {
  it("accepts a successful compiler payload", () => {
    const parsed = parseHamiltonCompileStdout(
      JSON.stringify({
        ok: true,
        script: SCRIPT,
        command_count: 4,
        warnings: [],
      })
    );
    assert.equal(parsed.ok, true);
    if (parsed.ok) {
      assert.match(parsed.script, /pick_up_tips/);
      assert.equal(parsed.command_count, 4);
    }
  });

  it("keeps compiler fail stage/error/hint without traceback", () => {
    const parsed = parseHamiltonCompileStdout(
      JSON.stringify({
        ok: false,
        stage: "mapping",
        error: "Step 2 ASPIRATE source missing:A1 is not in resources.",
        hint: "Add a resource with id 'missing'.",
      })
    );
    assert.equal(parsed.ok, false);
    if (!parsed.ok) {
      assert.equal(parsed.stage, "mapping");
      assert.match(parsed.error, /missing/);
      assert.equal(parsed.error.includes("Traceback"), false);
    }
  });

  it("covers timeout, spawn failure, bad JSON, and empty script", () => {
    const timeout = parseHamiltonCompileStdout("", { timedOut: true });
    assert.equal(timeout.ok, false);
    if (!timeout.ok) assert.match(timeout.error, /timed out/i);
    const spawn = parseHamiltonCompileStdout("", { spawnError: "ENOENT" });
    assert.equal(spawn.ok, false);
    if (!spawn.ok) assert.match(spawn.error, /did not start/i);
    const bad = parseHamiltonCompileStdout("not-json");
    assert.equal(bad.ok, false);
    if (!bad.ok) assert.match(bad.error, /invalid JSON/i);
    const empty = parseHamiltonCompileStdout(JSON.stringify({ ok: true, script: "  " }));
    assert.equal(empty.ok, false);
    if (!empty.ok) assert.match(empty.error, /no script/i);
  });
});

describe("runHamiltonCompile", () => {
  it("uses the injected spawn and never throws", async () => {
    const spawnFn: StdinJsonSpawn = async ({ stdin, argv }) => {
      assert.match(stdin, /bpl\.plan_ir/);
      assert.ok(argv.includes("--family"));
      return { stdout: JSON.stringify({ ok: true, script: SCRIPT, command_count: 1, warnings: [] }) };
    };
    const ok = await runHamiltonCompile(PLAN, spawnFn);
    assert.equal(ok.ok, true);

    const timed = await runHamiltonCompile(PLAN, async () => ({ stdout: "", timedOut: true }));
    assert.equal(timed.ok, false);

    const boom = await runHamiltonCompile(PLAN, async () => {
      throw new Error("unexpected");
    });
    assert.equal(boom.ok, false);
    if (!boom.ok) assert.equal(boom.error.includes("unexpected"), false);
  });
});

describe("attachHamiltonCompile", () => {
  it("skips Tecan and OT-2", async () => {
    let called = 0;
    const compileFn = async (): Promise<HamiltonCompileResult> => {
      called += 1;
      return { ok: true, script: SCRIPT, command_count: 1, warnings: [] };
    };
    const tecan = await attachHamiltonCompile(passChecks(), PLAN, "Tecan", compileFn);
    assert.equal(called, 0);
    assert.equal(tecan.artifacts, undefined);
    const ot = await attachHamiltonCompile(passChecks(), PLAN, "OT-2", compileFn);
    assert.equal(called, 0);
    assert.equal(ot.artifacts, undefined);
  });

  it("stores the script on pass and does not fail the check on compile error", async () => {
    const ok = await attachHamiltonCompile(passChecks(), PLAN, "Hamilton", async () => ({
      ok: true,
      script: SCRIPT,
      command_count: 4,
      warnings: [],
    }));
    assert.equal(ok.checks.status, "pass");
    assert.equal(ok.checks.fab.lit, true);
    assert.equal(ok.checks.compile, undefined);
    assert.match(ok.artifacts?.hamiltonScript || "", /pick_up_tips/);

    const fail = await attachHamiltonCompile(passChecks(), PLAN, "hamilton_star", async () => ({
      ok: false,
      stage: "mapping",
      error: "Step 2 ASPIRATE source plate:Z9 is not in resources.",
      hint: "Declare plate in resources[].",
    }));
    assert.equal(fail.checks.status, "pass");
    assert.equal(fail.checks.fab.lit, true);
    assert.equal(fail.artifacts, undefined);
    assert.equal(fail.checks.compile, undefined);

    const simFail = wrapChecks(
      { ok: false, reason: "sim_failed" },
      skippedLogic("sim_failed"),
      emptyStatepass("sim_failed")
    );
    const skipped = await attachHamiltonCompile(simFail, PLAN, "Hamilton", async () => ({
      ok: true,
      script: "should not run",
      command_count: 1,
      warnings: [],
    }));
    assert.equal(skipped.checks.status, "fail");
    assert.equal(skipped.artifacts, undefined);
  });
});
