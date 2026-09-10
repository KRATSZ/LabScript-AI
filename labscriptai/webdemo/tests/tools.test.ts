import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { applyAskUser, applyForm, createSession } from "../server/src/session.ts";
import { buildTools } from "../server/src/tools.ts";
import { wrapChecks } from "../server/src/gate.ts";

describe("tools harness", () => {
  it("exposes the six demo tools", () => {
    const session = createSession();
    const tools = buildTools(session, { write() {}, close() {} });
    assert.deepEqual(
      tools.map((t) => t.name),
      ["ask_user", "generate_sop", "generate_code", "run_checks", "skill", "open_animation"]
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
    assert.deepEqual(parsed.missing, ["generate_code — OT-2/Flex need 8010 Python"]);
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
