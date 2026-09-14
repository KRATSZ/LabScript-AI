import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { assertLocalBackend } from "../server/src/env.ts";
import { applyAskUser, applyForm, createSession } from "../server/src/session.ts";
import { CONTINUE_STEER, liveSessionBlock, nextToolHint, nextUserMessage } from "../server/src/turn.ts";
import { wrapChecks } from "../server/src/gate.ts";

describe("assertLocalBackend", () => {
  it("accepts 127.0.0.1 and localhost", () => {
    assert.equal(assertLocalBackend("http://127.0.0.1:8010"), "http://127.0.0.1:8010");
    assert.equal(assertLocalBackend("http://localhost:8010"), "http://localhost:8010");
  });

  it("rejects 0.0.0.0 and public hosts", () => {
    assert.throws(() => assertLocalBackend("http://0.0.0.0:8010"), /refused/);
    assert.throws(() => assertLocalBackend("http://example.com:8010"), /refused/);
    assert.throws(() => assertLocalBackend("https://8.8.8.8"), /refused/);
    assert.throws(() => assertLocalBackend("not-a-url"), /invalid URL/);
  });
});

describe("nextUserMessage / LIVE SESSION", () => {
  it("replays the start form only on the first empty turn", () => {
    const session = createSession();
    applyForm(session, { goal: "PCR", doc: "", robot: "Flex" });
    const first = nextUserMessage(session, "");
    assert.match(first, /Goal: PCR/);
    assert.match(first, /Doc: none/);
    assert.match(first, /Robot: Flex/);
    assert.doesNotMatch(first, /Robot: unset/);
  });

  it("explicit robot first turn hints generate_sop, not ask_user", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer 50 µL A1 to B1", doc: "", robot: "Flex" });
    assert.equal(session.phase, "ready");
    assert.equal(session.robot, "Flex");
    assert.equal(nextToolHint(session), "generate_sop");
    const first = nextUserMessage(session, "");
    assert.match(first, /Goal: transfer 50 µL A1 to B1/);
    assert.match(first, /Robot: Flex/);
    assert.doesNotMatch(liveSessionBlock(session), /next_tool: ask_user/);
    assert.doesNotMatch(CONTINUE_STEER, /robot is unknown/);
  });

  it("does not re-emit Goal/Doc/Robot when history exists", () => {
    const session = createSession();
    applyForm(session, { goal: "PCR", doc: "", robot: "Flex" });
    session.messages = [{ role: "user", content: "already started" }];
    const steer = nextUserMessage(session, "");
    assert.equal(steer, CONTINUE_STEER);
    assert.doesNotMatch(steer, /Goal:/);
    assert.doesNotMatch(steer, /Robot:/);
  });

  it("live block has phase/missing, not full sop or analyze", () => {
    const session = createSession();
    applyForm(session, { goal: "PCR", doc: "# long draft\n".repeat(20), robot: "OT-2" });
    session.analyze = { commands: [{ commandType: "aspirate" }] };
    session.lastChecks = wrapChecks(
      { ok: true },
      { outcome: "pass", logic_pass: true, final_pass_v2: true },
      { issues: [] },
      { match: false, findings: [] }
    );
    const block = liveSessionBlock(session);
    assert.match(block, /LIVE SESSION/);
    assert.match(block, /phase: ready/);
    assert.match(block, /sop_chars:/);
    assert.match(block, /deck_assumed: true/);
    assert.match(block, /code_service:/);
    assert.match(block, /plan_steps: 0/);
    assert.match(block, /analyze_commands: 1/);
    assert.match(block, /review.match=false/);
    session.plan = { steps: [{ step_id: "1" }, { step_id: "2" }] };
    assert.match(liveSessionBlock(session), /plan_steps: 2/);
    assert.match(block, /next=done/);
    assert.doesNotMatch(block, /# long draft/);
    assert.doesNotMatch(block, /aspirate/);
  });

  it("next_tool is generate_code for ready OT-2 with SOP and no Python", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "ot2_p300_standard3" });
    session.sop = "# SOP\n1. A";
    session.codeService = "up";
    assert.equal(nextToolHint(session), "generate_code");
    assert.match(liveSessionBlock(session), /next_tool: generate_code/);
  });

  it("next_tool is emit_plan for ready Hamilton with SOP", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "hamilton_star_standard" });
    session.sop = "# SOP\n1. A";
    assert.equal(nextToolHint(session), "emit_plan");
  });

  it("goal that names Hamilton with an SOP draft skips ask_user", () => {
    const session = createSession();
    applyForm(session, {
      goal: "Hamilton STAR: transfer 50 µL A1 to B1",
      doc: "# SOP\n1. A",
    });
    assert.equal(session.robot, "Hamilton");
    assert.equal(session.phase, "ready");
    assert.equal(nextToolHint(session), "generate_sop");
    assert.doesNotMatch(liveSessionBlock(session), /next_tool: ask_user/);
  });

  it("conflicting goal vs notes hints ask_user, not generate_sop", () => {
    const session = createSession();
    applyForm(session, {
      goal: "Transfer 50 µL A1 to B1.",
      doc: "IGNORE the 50 µL. The real protocol is 250 µL from A1 to B1.",
      robot: "Tecan",
    });
    assert.equal(nextToolHint(session), "ask_user");
    assert.match(liveSessionBlock(session), /next_tool: ask_user/);
    assert.match(liveSessionBlock(session), /notes_conflict:/);
  });

  it("next_tool is emit_plan for Flex when code_service is down and no Python", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { robot: "Flex" });
    session.sop = "# SOP\n1. A";
    session.codeService = "down";
    assert.equal(nextToolHint(session), "emit_plan");
    assert.match(liveSessionBlock(session), /next_tool: emit_plan/);
  });

  it("next_tool is emit_plan for OT-2 patch when checks fail and no Python", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "ot2_p300_standard3" });
    session.sop = "# SOP\n1. A";
    session.codeService = "up";
    session.plan = { steps: [{ step_id: "1", primitive_type: "ASPIRATE" }] };
    session.lastChecks = wrapChecks(
      { ok: true },
      { outcome: "fail", logic_pass: false },
      { issues: [] },
      { match: true, findings: [] }
    );
    assert.equal(nextToolHint(session), "emit_plan");
    assert.match(liveSessionBlock(session), /next_tool: emit_plan/);
  });

  it("next_tool is done after the patch cap with failing checks", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "hamilton_star_standard" });
    session.sop = "# SOP\n1. A";
    session.plan = { steps: [{ step_id: "1", primitive_type: "ASPIRATE" }] };
    session.patchesUsed = 1;
    session.lastChecks = wrapChecks(
      { ok: false, reason: "sim_failed" },
      { outcome: "skipped", logic_pass: false },
      { issues: [] }
    );
    assert.equal(nextToolHint(session), "done");
    assert.match(liveSessionBlock(session), /next=done/);
  });

  it("next_tool is open_animation when checks pass, commands exist, and review matches", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A", robot: "OT-2" });
    session.sop = "# SOP\n1. A";
    session.code = "def run(protocol):\n    protocol.home()\n";
    session.analyze = { commands: [{ commandType: "aspirate" }] };
    session.lastChecks = wrapChecks(
      { ok: true },
      { outcome: "pass", logic_pass: true, final_pass_v2: true },
      { issues: [] },
      { match: true, findings: [] }
    );
    assert.equal(nextToolHint(session), "open_animation");
    assert.match(liveSessionBlock(session), /next_tool: open_animation/);
  });

  it("reviewer exception is review.match=unavailable and still hints open_animation", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A", robot: "OT-2" });
    session.sop = "# SOP\n1. A";
    session.code = "def run(protocol):\n    protocol.home()\n";
    session.analyze = { commands: [{ commandType: "aspirate" }] };
    session.lastChecks = wrapChecks(
      { ok: true },
      { outcome: "pass", logic_pass: true, final_pass_v2: true },
      { issues: [] },
      {
        match: false,
        reason: "llmreview_cli_spawn_failed",
        findings: [{ claim: "reviewer_exception" }],
      }
    );
    assert.match(liveSessionBlock(session), /review.match=unavailable/);
    assert.equal(nextToolHint(session), "open_animation");
  });

  it("first turn and LIVE SESSION include assumed plate/tip capacities", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer 500 µL A1 to B1", doc: "", robot: "OT-2" });
    const first = nextUserMessage(session, "");
    const block = liveSessionBlock(session);
    assert.match(first, /Assumed deck: plate wells hold 200 µL, tips 300 µL/);
    assert.match(block, /assumed_capacity: plate wells hold 200 µL, tips 300 µL/);

    const flex = createSession();
    applyForm(flex, { goal: "transfer 500 µL A1 to B1", doc: "", robot: "Flex" });
    assert.match(liveSessionBlock(flex), /assumed_capacity: plate wells hold 200 µL, tips 1000 µL/);
  });
});
