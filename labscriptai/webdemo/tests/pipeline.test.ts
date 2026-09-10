import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { pipelineStates, phaseLabel } from "../web/src/pipelineLogic.ts";
import type { SessionSnapshot } from "../web/src/types.ts";
import { checkCodeService, extractPatchedCode } from "../server/src/backend.ts";

function snap(over: Partial<SessionSnapshot> = {}): SessionSnapshot {
  return {
    id: "s",
    phase: "need_robot",
    missing: ["robot"],
    goal: "transfer",
    doc: "none",
    robot: null,
    hardware: { deck: {} },
    hardware_config: "",
    sop: "",
    code: "",
    plan: null,
    analyze: null,
    checks: null,
    fab: { lit: false },
    ...over,
  };
}

describe("pipelineStates", () => {
  it("maps live tools to the five-step rail", () => {
    assert.deepEqual(pipelineStates(snap(), null), ["wait", "wait", "wait", "wait", "wait"]);
    assert.equal(pipelineStates(snap({ phase: "need_robot" }), "ask_user")[0], "run");
    assert.equal(pipelineStates(snap({ phase: "ready", sop: "# x" }), null)[0], "ok");
    assert.equal(pipelineStates(snap({ sop: "# x" }), "generate_sop")[1], "run");
    assert.equal(pipelineStates(snap({ code: "def run():\n  pass\n" }), "generate_code")[2], "run");
    assert.equal(pipelineStates(snap({}), null)[2], "wait");
    assert.equal(pipelineStates(snap({ robot: "OT-2" }), null)[2], "wait");
    assert.equal(pipelineStates(snap({ code: "def run():\n  pass\n" }), null)[2], "ok");
    assert.equal(pipelineStates(snap({ robot: "Hamilton" }), "emit_plan")[2], "run");
    assert.equal(
      pipelineStates(snap({ robot: "Hamilton", plan: { steps: [{ step_id: "1" }] } }), null)[2],
      "ok"
    );
  });

  it("marks unevaluable checks with their own state, not fail or wait", () => {
    const checks = {
      status: "unevaluable" as const,
      sim: { ok: true },
      logicpass: { outcome: "unevaluable" },
      statepass: {},
    };
    const states = pipelineStates(snap({ checks, phase: "ready" }), null);
    assert.equal(states[3], "uneval");
    assert.equal(states[4], "wait");
  });

  it("lights review fail when match is false", () => {
    const checks = {
      status: "pass" as const,
      sim: { ok: true },
      logicpass: { outcome: "pass" },
      statepass: {},
      llmreview: { match: false },
    };
    const states = pipelineStates(snap({ checks, phase: "ready", sop: "s", code: "c" }), null);
    assert.equal(states[3], "ok");
    assert.equal(states[4], "fail");
  });

  it("marks fail status as fail even if sim looks ok", () => {
    const checks = {
      status: "fail" as const,
      sim: { ok: true },
      logicpass: { outcome: "fail" },
      statepass: {},
    };
    assert.equal(pipelineStates(snap({ checks }), null)[3], "fail");
  });
});

describe("phaseLabel", () => {
  it("maps three check states and leaves pre-check phases alone", () => {
    assert.equal(phaseLabel("ready", "pass", true, false), "Ready to watch");
    assert.equal(phaseLabel("ready", "pass", false, false), "Checks passed — no animation available");
    assert.equal(phaseLabel("ready", "pass", false, true), "Checks passed — step table below");
    assert.equal(phaseLabel("ready", "fail", false, false), "Checks failed");
    assert.equal(phaseLabel("ready", "fail", false, true), "Checks failed");
    assert.equal(phaseLabel("ready", "unevaluable", false, false), "Cannot verify");
    assert.equal(phaseLabel("need_hw_slots", null, false, false), "Missing deck details");
    assert.equal(phaseLabel("ready", null, false, false), "In progress");
    assert.equal(phaseLabel("need_robot", null, false, false), "Which robot — OT-2, Flex, Hamilton, or Tecan?");
  });
});

describe("robot switch snapshot", () => {
  it("UI helpers follow only the new snapshot artifacts", () => {
    const pass = {
      status: "pass" as const,
      sim: { ok: true },
      logicpass: { outcome: "pass" },
      statepass: {},
    };
    const ot = snap({
      robot: "OT-2",
      phase: "ready",
      sop: "# OT SOP",
      code: "def run(): pass",
      analyze: { commands: [{ commandType: "home" }] },
      checks: pass,
    });
    const ham = snap({
      robot: "Hamilton",
      phase: "ready",
      sop: "# HAM SOP",
      code: "",
      plan: { steps: [{ step_id: "1" }] },
      analyze: null,
      checks: pass,
    });
    assert.equal(ot.code.includes("def run"), true);
    assert.equal(ham.code, "");
    assert.equal(ham.analyze, null);
    assert.notEqual(ot.sop, ham.sop);
    assert.equal(phaseLabel(ot.phase, ot.checks?.status, true, false), "Ready to watch");
    assert.equal(phaseLabel(ham.phase, ham.checks?.status, false, true), "Checks passed — step table below");
    assert.deepEqual(pipelineStates(ham, null).slice(0, 3), ["ok", "ok", "ok"]);
  });
});

describe("extractPatchedCode", () => {
  it("accepts edit payloads and python fences", () => {
    assert.equal(
      extractPatchedCode({ type: "edit", content: "from opentrons import protocol_api\ndef run(p):\n    p.home()\n" })?.includes("def run"),
      true
    );
    const fenced = extractPatchedCode({
      type: "chat",
      content: "Sure:\n```python\nfrom opentrons import protocol_api\ndef run(protocol):\n    protocol.home()\n```\n",
    });
    assert.match(fenced || "", /def run/);
    assert.equal(extractPatchedCode({ type: "chat", content: "I cannot edit that." }), null);
  });
});

describe("checkCodeService", () => {
  it("resolves to up or down and never throws", async () => {
    const status = await checkCodeService();
    assert.ok(status === "up" || status === "down");
  });
});
