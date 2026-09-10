import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  attachFluentCompile,
  parseFluentCompileStdout,
  runFluentCompile,
  type FluentCompileResult,
  type StdinJsonSpawn,
} from "../server/src/backend.ts";
import { emptyStatepass, skippedLogic, wrapChecks } from "../server/src/gate.ts";

const PLAN = { schema: "bpl.plan_ir.lh.v0", steps: [{ step_id: "1" }] };

const passChecks = () =>
  wrapChecks(
    { ok: true },
    { outcome: "pass", logic_pass: true, final_pass_v2: true },
    emptyStatepass()
  );

describe("parseFluentCompileStdout", () => {
  it("accepts a successful compiler payload", () => {
    const parsed = parseFluentCompileStdout(
      JSON.stringify({
        ok: true,
        worklist_gwl: "C; plan\nA;plate;;;A1;;50;Water Free Single;;1;\nB;\n",
        script_xml: "B;<ScriptGroup>",
        command_count: 3,
        warnings: ["MIX is XML only"],
      })
    );
    assert.equal(parsed.ok, true);
    if (parsed.ok) {
      assert.match(parsed.worklist_gwl, /^C;/);
      assert.equal(parsed.command_count, 3);
      assert.deepEqual(parsed.warnings, ["MIX is XML only"]);
    }
  });

  it("keeps compiler fail stage/error/hint without traceback", () => {
    const parsed = parseFluentCompileStdout(
      JSON.stringify({
        ok: false,
        stage: "state_machine",
        error: "Step 2 aspirates before any PICK_TIPS — the head has no tips on.",
        hint: "Add a PICK_TIPS step before ASPIRATE.",
      })
    );
    assert.equal(parsed.ok, false);
    if (!parsed.ok) {
      assert.equal(parsed.stage, "state_machine");
      assert.match(parsed.error, /no tips/);
      assert.match(parsed.hint, /PICK_TIPS/);
      assert.equal(parsed.error.includes("Traceback"), false);
    }
  });

  it("covers timeout, spawn failure, bad JSON, and empty worklist", () => {
    const timeout = parseFluentCompileStdout("", { timedOut: true });
    assert.equal(timeout.ok, false);
    if (!timeout.ok) {
      assert.equal(timeout.stage, "internal");
      assert.match(timeout.error, /timed out/i);
    }
    const spawn = parseFluentCompileStdout("", { spawnError: "ENOENT" });
    assert.equal(spawn.ok, false);
    if (!spawn.ok) assert.match(spawn.error, /did not start/i);
    const bad = parseFluentCompileStdout("not-json");
    assert.equal(bad.ok, false);
    if (!bad.ok) assert.match(bad.error, /invalid JSON/i);
    const empty = parseFluentCompileStdout(JSON.stringify({ ok: true, worklist_gwl: "", script_xml: "B;" }));
    assert.equal(empty.ok, false);
    if (!empty.ok) assert.match(empty.error, /no worklist/i);
  });
});

describe("runFluentCompile", () => {
  it("uses the injected spawn and never throws", async () => {
    const spawnFn: StdinJsonSpawn = async ({ stdin }) => {
      assert.match(stdin, /bpl\.plan_ir/);
      return {
        stdout: JSON.stringify({
          ok: true,
          worklist_gwl: "C;ok\nB;\n",
          script_xml: "B;<ScriptGroup>",
          command_count: 1,
          warnings: [],
        }),
      };
    };
    const ok = await runFluentCompile(PLAN, spawnFn);
    assert.equal(ok.ok, true);

    const timed = await runFluentCompile(PLAN, async () => ({ stdout: "", timedOut: true }));
    assert.equal(timed.ok, false);
    if (!timed.ok) assert.equal(timed.stage, "internal");

    const spawned = await runFluentCompile(PLAN, async () => ({ stdout: "", spawnError: "spawn_failed" }));
    assert.equal(spawned.ok, false);

    const boom = await runFluentCompile(PLAN, async () => {
      throw new Error("unexpected");
    });
    assert.equal(boom.ok, false);
    if (!boom.ok) assert.equal(boom.error.includes("unexpected"), false);
  });
});

describe("attachFluentCompile", () => {
  it("skips compile for Hamilton and OT-2 plan fallback", async () => {
    let called = 0;
    const compileFn = async (): Promise<FluentCompileResult> => {
      called += 1;
      return { ok: true, worklist_gwl: "C;\n", script_xml: "B;", command_count: 1, warnings: [] };
    };
    const ham = await attachFluentCompile(passChecks(), PLAN, "Hamilton", compileFn);
    assert.equal(called, 0);
    assert.equal(ham.artifacts, undefined);
    assert.equal(ham.checks.compile, undefined);
    assert.equal(ham.checks.status, "pass");

    const ot = await attachFluentCompile(passChecks(), PLAN, "OT-2", compileFn);
    assert.equal(called, 0);
    assert.equal(ot.artifacts, undefined);
  });

  it("stores .gwl artifacts on Tecan compile ok and fails the check on compile error", async () => {
    const ok = await attachFluentCompile(passChecks(), PLAN, "Tecan", async () => ({
      ok: true,
      worklist_gwl: "C; Plan IR\nA;plate;;;A1;;50;Water Free Single;;1;\nB;\n",
      script_xml: "B;<ScriptGroup>",
      command_count: 4,
      warnings: [],
    }));
    assert.equal(ok.checks.status, "pass");
    assert.equal(ok.checks.fab.lit, true);
    assert.equal(ok.checks.compile?.ok, true);
    assert.match(ok.artifacts?.worklistGwl || "", /^C;/);
    assert.match(ok.artifacts?.scriptXml || "", /^B;/);

    const fail = await attachFluentCompile(passChecks(), PLAN, "tecan_fluent", async () => ({
      ok: false,
      stage: "mapping",
      error: "Step 2 ASPIRATE source plate:Z9 is not on the worktable.",
      hint: "Declare plate in resources[].",
    }));
    assert.equal(fail.checks.status, "fail");
    assert.equal(fail.checks.fab.lit, false);
    assert.equal(fail.artifacts, undefined);
    assert.equal(fail.checks.compile?.ok, false);
    assert.equal(fail.checks.compile?.hint, "Declare plate in resources[].");
    assert.match((fail.checks.consequences ?? [])[0] || "", /Fluent deck/i);

    const plr = wrapChecks(
      { ok: false, reason: "plr_unavailable" },
      skippedLogic("plr_unavailable"),
      emptyStatepass("plr_unavailable")
    );
    const plrOk = await attachFluentCompile(plr, PLAN, "Tecan", async () => ({
      ok: true,
      worklist_gwl: "C;ok\nB;\n",
      script_xml: "B;",
      command_count: 1,
      warnings: [],
    }));
    assert.equal(plrOk.checks.status, "unevaluable");
    assert.equal(plrOk.checks.fab.lit, false);
    assert.equal(plrOk.artifacts, undefined);

    const simFail = wrapChecks(
      { ok: false, reason: "sim_failed", errors: ["ValueError: invalid literal for int() with base 10: 'IPS'"] },
      skippedLogic("sim_failed"),
      emptyStatepass("sim_failed")
    );
    const leaked = await attachFluentCompile(simFail, PLAN, "Tecan", async () => ({
      ok: true,
      worklist_gwl: "C; should not leak\nB;\n",
      script_xml: "B;",
      command_count: 1,
      warnings: [],
    }));
    assert.equal(leaked.checks.status, "fail");
    assert.equal(leaked.artifacts, undefined);
    assert.equal(leaked.checks.compile?.ok, true);
  });
});
