import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { applyAskUser, applyForm, createSession } from "../server/src/session.ts";
import { buildTools } from "../server/src/tools.ts";
import { compactChecks, PATCH_BUDGET_REFUSAL, wrapChecks } from "../server/src/gate.ts";

describe("tools harness", () => {
  it("exposes the seven demo tools", () => {
    const session = createSession();
    const tools = buildTools(session, { write() {}, close() {} });
    assert.deepEqual(
      tools.map((t) => t.name),
      ["ask_user", "generate_sop", "generate_code", "emit_plan", "run_checks", "skill", "open_animation"]
    );
  });

  it("generate_sop blocked without goal returns JSON", async () => {
    const session = createSession();
    const tools = buildTools(session, { write() {}, close() {} });
    const sop = tools.find((t) => t.name === "generate_sop");
    assert.ok(sop);
    const result = await sop.execute("1", {});
    const parsed = JSON.parse(result.content[0].text);
    assert.equal(parsed.blocked, true);
    assert.ok(Array.isArray(parsed.missing));
  });

  it("generate_sop blocked without hardware does not need DeepSeek", async () => {
    const session = createSession();
    applyForm(session, { goal: "把 50 µL 从 A1 转到 B1（96 孔板）", doc: "" });
    assert.equal(session.phase, "need_robot");
    const tools = buildTools(session, { write() {}, close() {} });
    const sop = tools.find((t) => t.name === "generate_sop");
    assert.ok(sop);
    const result = await sop.execute("1", {});
    const parsed = JSON.parse(result.content[0].text);
    assert.equal(parsed.blocked, true);
    assert.ok(parsed.missing.includes("robot"));
  });

  it("generate_code blocked without hardware returns JSON", async () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "" });
    const tools = buildTools(session, { write() {}, close() {} });
    const code = tools.find((t) => t.name === "generate_code");
    assert.ok(code);
    const result = await code.execute("1", {});
    const parsed = JSON.parse(result.content[0].text);
    assert.equal(parsed.blocked, true);
    assert.ok(Array.isArray(parsed.missing));
  });

  it("generate_sop skips when a draft already exists", async () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "ot2_p300_standard3" });
    const tools = buildTools(session, { write() {}, close() {} });
    const sop = tools.find((t) => t.name === "generate_sop");
    assert.ok(sop);
    const result = await sop.execute("1", {});
    const parsed = JSON.parse(result.content[0].text);
    assert.equal(parsed.skipped, true);
    assert.equal(parsed.sop_markdown, "# SOP\n1. A");
  });

  it("generate_code skips a passing script unless instruction is set", async () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "ot2_p300_standard3" });
    session.sop = "# SOP\n1. A";
    session.code = "from opentrons import protocol_api\ndef run(protocol):\n    protocol.home()\n";
    session.lastChecks = wrapChecks(
      { ok: true },
      { outcome: "pass", logic_pass: true, final_pass_v2: true },
      { issues: [] }
    );
    const tools = buildTools(session, { write() {}, close() {} });
    const code = tools.find((t) => t.name === "generate_code");
    assert.ok(code);
    const result = await code.execute("1", {});
    const parsed = JSON.parse(result.content[0].text);
    assert.equal(parsed.skipped, true);
    assert.equal(parsed.next, "done");
    assert.equal(session.code.includes("protocol.home"), true);
  });

  it("run_checks blocked without code returns JSON", async () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "ot2_p300_standard3" });
    const tools = buildTools(session, { write() {}, close() {} });
    const checks = tools.find((t) => t.name === "run_checks");
    assert.ok(checks);
    const result = await checks.execute("1", {});
    const parsed = JSON.parse(result.content[0].text);
    assert.equal(parsed.blocked, true);
    assert.deepEqual(parsed.missing, [
      "generate_code — OT-2/Flex need 8010 Python, or emit_plan if 8010 is down",
    ]);
  });

  it("open_animation blocked without FinalPass returns JSON", async () => {
    const session = createSession();
    const tools = buildTools(session, { write() {}, close() {} });
    const open = tools.find((t) => t.name === "open_animation");
    assert.ok(open);
    const result = await open.execute("1", {});
    const parsed = JSON.parse(result.content[0].text);
    assert.equal(parsed.blocked, true);
    assert.equal(parsed.allowed, false);
  });

  it("ask_user with Flex robot returns assumed_deck true", async () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "" });
    const tools = buildTools(session, { write() {}, close() {} });
    const ask = tools.find((t) => t.name === "ask_user");
    assert.ok(ask);
    const result = await ask.execute("1", { robot: "Flex" });
    const parsed = JSON.parse(result.content[0].text);
    assert.equal(parsed.assumed_deck, true);
    assert.equal(parsed.ready, true);
    assert.equal(parsed.phase, "ready");
  });
});

const failChecks = () =>
  wrapChecks(
    { ok: false, reason: "sim_failed" },
    { outcome: "skipped", logic_pass: false, final_pass_v2: false },
    { issues: [] }
  );

const passChecks = () =>
  wrapChecks(
    { ok: true },
    { outcome: "pass", logic_pass: true, final_pass_v2: true },
    { issues: [] }
  );

const DEMO_PLAN = {
  schema: "bpl.plan_ir.lh.v0",
  plan_id: "demo-transfer",
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

function tool(session: ReturnType<typeof createSession>, name: string) {
  const found = buildTools(session, { write() {}, close() {} }).find((t) => t.name === name);
  assert.ok(found);
  return found;
}

function assertRefused(result: { content: Array<{ type: string; text: string }>; terminate?: boolean; details?: unknown }) {
  assert.equal(result.terminate, true);
  assert.match(result.content[0].text, /Patch budget used/);
  assert.match(result.content[0].text, /Stop calling tools/);
  assert.match(result.content[0].text, /Tell the user what fails/);
  assert.equal(result.content[0].text, PATCH_BUDGET_REFUSAL);
  assert.equal((result.details as { refused?: boolean }).refused, true);
}

describe("one-patch budget", () => {
  it("emit_plan: fail → patch → fail → refuse, and a new turn allows one more", async () => {
    const session = createSession();
    applyForm(session, { goal: "transfer 50uL A1 to B1", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "hamilton_star_standard" });
    session.sop = "# SOP\n1. A";
    const emit = tool(session, "emit_plan");

    const first = await emit.execute("1", { plan: DEMO_PLAN });
    assert.equal(JSON.parse(first.content[0].text).ok, true);
    assert.equal(session.patchesUsed ?? 0, 0);

    session.lastChecks = failChecks();
    assert.equal(compactChecks(session.lastChecks, session.patchesUsed ?? 0).next, "patch");

    const patch = await emit.execute("2", { plan: { ...DEMO_PLAN, plan_id: "demo-transfer-v2" } });
    assert.equal(JSON.parse(patch.content[0].text).ok, true);
    assert.equal(session.patchesUsed, 1);

    session.lastChecks = failChecks();
    assert.equal(compactChecks(session.lastChecks, session.patchesUsed ?? 0).next, "done");
    const planAfterPatch = session.plan;

    const refused = await emit.execute("3", { plan: { ...DEMO_PLAN, plan_id: "start-over" } });
    assertRefused(refused);
    assert.equal(session.patchesUsed, 1);
    assert.equal(session.plan, planAfterPatch);

    session.patchesUsed = 0;
    const retry = await emit.execute("4", { plan: { ...DEMO_PLAN, plan_id: "after-user" } });
    assert.equal(JSON.parse(retry.content[0].text).ok, true);
    assert.equal(session.patchesUsed, 1);
    assert.equal(retry.terminate, undefined);
  });

  it("generate_code: fail → patch used → fail → refuse, reset allows one more", async () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "ot2_p300_standard3" });
    session.sop = "# SOP\n1. A";
    session.code = "from opentrons import protocol_api\ndef run(protocol):\n    protocol.home()\n";
    const code = tool(session, "generate_code");

    session.lastChecks = failChecks();
    assert.equal(compactChecks(session.lastChecks, 0).next, "patch");
    session.patchesUsed = 1;
    session.lastChecks = failChecks();
    assert.equal(compactChecks(session.lastChecks, session.patchesUsed ?? 0).next, "done");
    const kept = session.code;

    const refused = await code.execute("1", { instruction: "start over from scratch" });
    assertRefused(refused);
    assert.equal(session.code, kept);
    assert.equal(session.patchesUsed, 1);

    session.patchesUsed = 0;
    assert.equal(compactChecks(session.lastChecks, 0).next, "patch");
  });

  it("happy path fail → patch → pass does not refuse", async () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "ot2_p300_standard3" });
    session.sop = "# SOP\n1. A";
    session.code = "from opentrons import protocol_api\ndef run(protocol):\n    protocol.home()\n";
    session.patchesUsed = 1;
    session.lastChecks = passChecks();
    const code = tool(session, "generate_code");
    const result = await code.execute("1", {});
    const parsed = JSON.parse(result.content[0].text);
    assert.equal(parsed.skipped, true);
    assert.equal(parsed.next, "done");
    assert.equal(result.terminate, undefined);
  });
});
