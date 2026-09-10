import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { pipelineStates } from "../web/src/pipelineLogic.ts";
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
  });

  it("marks unevaluable checks as fail, not wait", () => {
    const checks = {
      sim: { ok: true },
      logicpass: { outcome: "unevaluable", logic_pass: false },
      statepass: {},
      fab: { lit: false },
    };
    const states = pipelineStates(snap({ checks, phase: "ready" }), null);
    assert.equal(states[3], "fail");
    assert.equal(states[4], "wait");
  });

  it("lights review fail when match is false", () => {
    const checks = {
      sim: { ok: true },
      logicpass: { outcome: "pass", logic_pass: true, final_pass_v2: true },
      statepass: {},
      llmreview: { match: false },
      fab: { lit: true },
    };
    const states = pipelineStates(snap({ checks, phase: "ready", sop: "s", code: "c" }), null);
    assert.equal(states[3], "ok");
    assert.equal(states[4], "fail");
  });

  it("keeps Checks fail when FinalPass_v2 is missing", () => {
    const checks = {
      sim: { ok: true },
      logicpass: { outcome: "pass", logic_pass: true, final_pass_v2: false },
      statepass: {},
      fab: { lit: false },
    };
    assert.equal(pipelineStates(snap({ checks }), null)[3], "fail");
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
