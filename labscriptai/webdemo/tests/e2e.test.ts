import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { isPlayableAnalyze } from "../web/src/analysis.ts";
import { downloadable, downloadSuffix } from "../web/src/artifacts.ts";
import { loadDemoEnv } from "../server/src/env.ts";
import {
  emptyStatepass,
  sanitizeLogicpass,
  wrapChecks,
  type ChecksResult,
} from "../server/src/gate.ts";
import { applyForm, createSession, missingList, snapshot } from "../server/src/session.ts";
import { buildTools } from "../server/src/tools.ts";
import { nextToolHint } from "../server/src/turn.ts";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (rel: string) => readFileSync(path.join(root, rel), "utf8");

const SOP = "# SOP\n1. Transfer as stated in the goal.";

const HAPPY_PLAN = {
  schema: "bpl.plan_ir.lh.v0",
  plan_id: "e2e-happy",
  backend: "hamilton",
  resources: [
    { id: "tips", type: "tiprack", slot: "1" },
    { id: "plate", type: "plate", slot: "2", max_volume_ul: 200 },
  ],
  initial_volumes_ul: { "plate:A1": 100, "plate:B1": 0 },
  steps: [
    { step_id: "1", primitive_type: "PICK_TIPS", tip_rack: "tips", tip_positions: ["A1"], dependencies: [] },
    { step_id: "2", primitive_type: "ASPIRATE", source: "plate:A1", volume_ul: 50, dependencies: ["1"] },
    { step_id: "3", primitive_type: "DISPENSE", destination: "plate:B1", volume_ul: 50, dependencies: ["2"] },
    { step_id: "4", primitive_type: "DROP_TIPS", to_waste: true, dependencies: ["3"] },
  ],
};

const OVERFLOW_VOL = 250;
const OVERFLOW_PLAN = {
  ...HAPPY_PLAN,
  plan_id: "e2e-overflow",
  initial_volumes_ul: { "plate:A1": OVERFLOW_VOL, "plate:B1": 0 },
  steps: [
    HAPPY_PLAN.steps[0],
    { ...HAPPY_PLAN.steps[1], volume_ul: OVERFLOW_VOL },
    { ...HAPPY_PLAN.steps[2], volume_ul: OVERFLOW_VOL },
    HAPPY_PLAN.steps[3],
  ],
};

const UNKNOWN_CAP_PLAN = {
  schema: "bpl.plan_ir.lh.v0",
  plan_id: "e2e-unknown-cap",
  backend: "serializing",
  resources: [
    { id: "tips", type: "tiprack", slot: "1" },
    { id: "plate", type: "plate", slot: "2" },
  ],
  initial_volumes_ul: { "plate:A1": 100, "plate:B1": 0 },
  steps: HAPPY_PLAN.steps,
};

function tool(session: ReturnType<typeof createSession>, name: string) {
  const found = buildTools(session, { write() {}, close() {} }).find((t) => t.name === name);
  assert.ok(found);
  return found;
}

function payload(result: { content: Array<{ type?: string; text?: string }> }): Record<string, unknown> {
  const block = result.content.find((item) => item.type === "text") ?? result.content[0];
  return JSON.parse(typeof block?.text === "string" ? block.text : "{}") as Record<string, unknown>;
}

function stepVolumes(plan: Record<string, unknown> | undefined | null): number[] {
  const steps = Array.isArray(plan?.steps) ? plan.steps : [];
  return steps
    .map((step) =>
      step && typeof step === "object" ? Number((step as { volume_ul?: number }).volume_ul) : NaN
    )
    .filter((n) => Number.isFinite(n));
}

/** Real virtual-deck LogicPass. PLR sim and llmreview are stubbed (no DeepSeek, no 8010). */
function virtualDeckChecks(plan: Record<string, unknown>): ChecksResult {
  const env = loadDemoEnv();
  const py = [
    "import json, sys",
    "from labscriptai.planir import run_plan_checks",
    "plan = json.loads(sys.stdin.read())",
    'print(json.dumps(run_plan_checks(plan, sim={"ok": True, "backend": "stub"}, skip_review=True), default=str))',
  ].join("\n");
  const out = spawnSync(env.python, ["-c", py], {
    input: JSON.stringify(plan),
    encoding: "utf8",
    env: { ...process.env, PYTHONPATH: env.repoRoot },
  });
  assert.equal(out.status, 0, out.stderr || "virtual-deck spawn failed");
  const raw = JSON.parse(out.stdout) as {
    sim?: { ok?: boolean; reason?: string; errors?: string[] };
    logicpass?: Record<string, unknown>;
  };
  return wrapChecks(
    {
      ok: raw.sim?.ok === true,
      reason: raw.sim?.reason,
      errors: raw.sim?.errors,
    },
    sanitizeLogicpass(raw.logicpass),
    emptyStatepass()
  );
}

describe("e2e regression (buildTools + session; runChatTurn needs DeepSeek)", () => {
  it("ask_user with robot already in args is not a chat question bubble", () => {
    assert.doesNotMatch(read("web/src/ChatPane.tsx"), /ask_user/);
    assert.match(read("server/src/prompt.ts"), /do not write a question/);
  });

  it("Hamilton happy path: SOP → plan → pass → download-ready, zero asks", async () => {
    const session = createSession();
    applyForm(session, {
      goal: "Hamilton STAR: transfer 50 µL from A1 to B1 on a 96-well plate.",
      doc: SOP,
    });
    assert.equal(session.robot, "Hamilton");
    assert.equal(session.phase, "ready");
    assert.deepEqual(missingList(session), []);
    assert.equal(nextToolHint(session), "emit_plan");

    const emitted = await tool(session, "emit_plan").execute("1", { plan: HAPPY_PLAN });
    assert.equal(payload(emitted).ok, true);
    session.lastChecks = virtualDeckChecks(session.plan as Record<string, unknown>);
    assert.equal(session.lastChecks.status, "pass");

    const snap = snapshot(session);
    assert.deepEqual(downloadable(snap), ["sop", "plan"]);
    assert.equal(downloadSuffix(snap.checks?.status), "");
    assert.equal(isPlayableAnalyze(snap.analyze), false);
    assert.equal(snap.checks?.status === "pass" && isPlayableAnalyze(snap.analyze), false);
  });

  it("Hamilton dishonesty trap: overflowing volume stays, fail mentions spill", async () => {
    const session = createSession();
    applyForm(session, {
      goal: `Hamilton STAR: dispense ${OVERFLOW_VOL} µL into a 200 µL well.`,
      doc: SOP,
    });
    assert.equal(nextToolHint(session), "emit_plan");

    const emitted = await tool(session, "emit_plan").execute("1", { plan: OVERFLOW_PLAN });
    assert.equal(payload(emitted).ok, true);
    assert.ok(stepVolumes(session.plan).includes(OVERFLOW_VOL));
    assert.equal(
      JSON.stringify(session.plan).includes(String(OVERFLOW_VOL)),
      true
    );

    session.lastChecks = virtualDeckChecks(session.plan as Record<string, unknown>);
    assert.equal(session.lastChecks.status, "fail");
    assert.match((session.lastChecks.consequences ?? []).join(" "), /spill/i);
    assert.ok(stepVolumes(session.plan).includes(OVERFLOW_VOL));
  });

  it("OT-2 with code service down: plan fallback, unknown capacity is cannot-verify, no watch", async () => {
    const session = createSession();
    applyForm(session, {
      goal: "OT-2: transfer 50 µL A1 to B1 on a plate with unknown well capacity.",
      doc: SOP,
    });
    session.codeService = "down";
    assert.equal(session.robot, "OT-2");
    assert.equal(nextToolHint(session), "emit_plan");

    const emitted = await tool(session, "emit_plan").execute("1", { plan: UNKNOWN_CAP_PLAN });
    assert.equal(payload(emitted).ok, true);
    session.lastChecks = virtualDeckChecks(session.plan as Record<string, unknown>);
    assert.equal(session.lastChecks.status, "unevaluable");

    const snap = snapshot(session);
    assert.equal(downloadSuffix(snap.checks?.status), " (cannot verify)");
    assert.ok(downloadable(snap).includes("plan"));
    assert.equal(isPlayableAnalyze(snap.analyze), false);
    const open = await tool(session, "open_animation").execute("1", {});
    assert.equal(payload(open).allowed, false);
  });

  it("loop guard lives in tools.test.ts one-patch budget (not duplicated)", () => {
    const src = read("tests/tools.test.ts");
    assert.match(src, /describe\("one-patch budget"/);
    assert.match(src, /fail → patch → fail → refuse/);
  });
});
