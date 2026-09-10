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
    assert.doesNotMatch(block, /plan_steps/);
    assert.match(block, /analyze_commands: 1/);
    assert.match(block, /review.match=false/);
    assert.match(block, /next=patch/);
    assert.doesNotMatch(block, /# long draft/);
    assert.doesNotMatch(block, /aspirate/);
  });

  it("next_tool is generate_code for ready OT-2 with SOP and no Python", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "ot2_p300_standard3" });
    session.sop = "# SOP\n1. A";
    assert.equal(nextToolHint(session), "generate_code");
    assert.match(liveSessionBlock(session), /next_tool: generate_code/);
  });

});
