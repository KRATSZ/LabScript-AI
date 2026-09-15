import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  pipelineStates,
  pipelineSteps,
  phaseLabel,
  statusWord,
  statusTone,
  headerTone,
  unevalDetail,
} from "../web/src/pipelineLogic.ts";
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

const pass = {
  status: "pass" as const,
  sim: { ok: true },
  logicpass: { outcome: "pass" },
  statepass: {},
};

const unevalChecks = {
  status: "unevaluable" as const,
  sim: { ok: true },
  logicpass: { outcome: "unevaluable" },
  statepass: {},
  consequences: ["Cannot verify: the Hamilton/Tecan simulator is not installed, so only partial checks ran."],
};

describe("pipelineSteps", () => {
  it("names the python path Goal→SOP→Code→Checks→Watch", () => {
    assert.deepEqual(pipelineSteps("OT-2"), ["Goal", "SOP", "Code", "Checks", "Watch"]);
    assert.deepEqual(pipelineSteps("Flex"), ["Goal", "SOP", "Code", "Checks", "Watch"]);
  });

  it("names the plan path Goal→SOP→Plan→Checks→Export and never says Code or Watch", () => {
    assert.deepEqual(pipelineSteps("Hamilton"), ["Goal", "SOP", "Plan", "Checks", "Export"]);
    assert.deepEqual(pipelineSteps("Vantage"), ["Goal", "SOP", "Plan", "Checks", "Export"]);
    assert.deepEqual(pipelineSteps("Tecan"), ["Goal", "SOP", "Plan", "Checks", "Export"]);
    for (const robot of ["Hamilton", "Vantage", "Tecan"] as const) {
      const labels = pipelineSteps(robot).join(" ");
      assert.equal(labels.includes("Code"), false);
      assert.equal(labels.includes("Watch"), false);
      assert.equal(labels.includes("Script"), false);
    }
  });
});

describe("pipelineStates", () => {
  it("maps live tools to the five-step rail", () => {
    assert.deepEqual(pipelineStates(snap({ goal: "" }), null), ["wait", "wait", "wait", "wait", "wait"]);
    assert.equal(pipelineStates(snap(), null)[0], "ok");
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
    const states = pipelineStates(snap({ checks: unevalChecks, phase: "ready" }), null);
    assert.equal(states[3], "uneval");
    assert.equal(states[4], "wait");
  });

  it("does not paint Watch from llmreview; Watch needs pass + commands", () => {
    const checks = {
      ...pass,
      llmreview: { match: false },
    };
    const states = pipelineStates(
      snap({ checks, phase: "ready", sop: "s", code: "c", robot: "OT-2" }),
      null
    );
    assert.equal(states[3], "ok");
    assert.equal(states[4], "wait");
  });

  it("lights Watch when OT-2 passed with commands", () => {
    const states = pipelineStates(
      snap({
        robot: "OT-2",
        phase: "ready",
        sop: "s",
        code: "c",
        analyze: { commands: [{ commandType: "home" }] },
        checks: pass,
      }),
      null
    );
    assert.equal(states[4], "ok");
  });

  it("lights Export on Hamilton after checks, uneval when cannot-verify", () => {
    const ham = snap({
      robot: "Hamilton",
      phase: "ready",
      sop: "# s",
      plan: { steps: [{ step_id: "1" }] },
      checks: pass,
    });
    assert.equal(pipelineStates(ham, null)[4], "ok");
    assert.equal(pipelineStates({ ...ham, checks: unevalChecks }, null)[3], "uneval");
    assert.equal(pipelineStates({ ...ham, checks: unevalChecks }, null)[4], "uneval");
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
    assert.equal(phaseLabel("ready", "pass", false, false), "Checks passed");
    assert.equal(phaseLabel("ready", "pass", false, true), "Checks passed");
    assert.equal(
      phaseLabel("ready", "pass", false, true, undefined, undefined, undefined, true),
      "Ready to watch"
    );
    assert.equal(phaseLabel("ready", "fail", false, false), "Checks failed");
    assert.equal(phaseLabel("ready", "fail", false, true), "Checks failed");
    assert.equal(phaseLabel("ready", "unevaluable", false, false), "Cannot verify");
    assert.equal(phaseLabel("need_hw_slots", null, false, false), "Missing deck details");
    assert.equal(phaseLabel("ready", null, false, false), "In progress");
    assert.equal(phaseLabel("ready", null, false, false, null, false, false), "A couple of details first");
    assert.equal(phaseLabel("need_robot", null, false, false), "Which robot — OT-2, Flex, Hamilton STAR, Hamilton Vantage, or Tecan Fluent?");
  });

  it("unevaluable header uses the checks consequence, not a frontend invention", () => {
    assert.equal(
      phaseLabel("ready", "unevaluable", false, true, unevalChecks),
      "Cannot verify: the Hamilton/Tecan simulator is not installed, so only partial checks ran."
    );
    assert.equal(unevalDetail(unevalChecks), unevalChecks.consequences[0]);
    assert.equal(unevalDetail(pass), "");
  });
});

describe("three-state copy", () => {
  it("uses the same yellow word across header helpers, issues, and exports", () => {
    assert.equal(statusWord("pass"), "Passed");
    assert.equal(statusWord("fail"), "Failed");
    assert.equal(statusWord("unevaluable"), "Cannot verify");
    assert.equal(statusTone("pass"), "pass");
    assert.equal(statusTone("fail"), "fail");
    assert.equal(statusTone("unevaluable"), "uneval");
    assert.equal(statusTone(null), null);
    assert.equal(headerTone("unevaluable", false), "uneval");
    assert.equal(headerTone("pass", true), "pass");
    assert.equal(headerTone("fail", false), "fail");
  });
});

describe("robot switch snapshot", () => {
  it("UI helpers follow only the new snapshot artifacts", () => {
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
    assert.equal(phaseLabel(ham.phase, ham.checks?.status, false, true), "Checks passed");
    assert.equal(
      phaseLabel(ham.phase, ham.checks?.status, false, true, undefined, undefined, undefined, true),
      "Ready to watch"
    );
    assert.deepEqual(pipelineStates(ham, null).slice(0, 3), ["ok", "ok", "ok"]);
    assert.deepEqual(pipelineSteps(ot.robot), ["Goal", "SOP", "Code", "Checks", "Watch"]);
    assert.deepEqual(pipelineSteps(ham.robot), ["Goal", "SOP", "Plan", "Checks", "Export"]);
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
