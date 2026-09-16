import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { tabCount, tabVisible } from "../web/src/stageTabs.ts";
import {
  activitySteps,
  activityStatusWord,
  activitySummary,
  eventDetailText,
  formatDuration,
  labThinkNote,
  thoughtNotesFromChat,
  thoughtTurnsFromChat,
} from "../web/src/trajectoryLogic.ts";
import type { AgentEvent, SessionSnapshot } from "../web/src/types.ts";

const event = (partial: Partial<AgentEvent> & Pick<AgentEvent, "kind">): AgentEvent => ({
  seq: 1,
  t: 1,
  ...partial,
});

describe("right stage tabs", () => {
  it("counts artifacts and trajectory events, not Stage", () => {
    const session = {
      sop: "# SOP",
      plan: { steps: [] },
      robot: "Tecan",
      artifacts: { worklistGwl: "A;..." },
    } as unknown as SessionSnapshot;
    const events = [
      event({ seq: 1, kind: "turn/start" }),
      event({ seq: 2, kind: "turn/end", detail: { ok: true } }),
    ];
    assert.equal(tabCount("stage", session, events), null);
    assert.equal(tabCount("artifacts", session, events), 3);
    assert.equal(tabCount("trajectory", session, events), 0);
    assert.equal(tabCount("artifacts", null, []), 0);
    assert.equal(tabVisible("stage", null, []), true);
    assert.equal(tabVisible("artifacts", null, []), false);
    assert.equal(tabVisible("trajectory", null, []), false);
    assert.equal(tabVisible("artifacts", session, events), true);
    assert.equal(tabVisible("trajectory", session, events), true);
    const clarify = { robot: "OT-2", sop: "", code: "" } as unknown as SessionSnapshot;
    assert.equal(tabVisible("artifacts", clarify, events), false);
    assert.equal(tabVisible("trajectory", clarify, events), true);
  });
});

describe("trajectory details", () => {
  it("shows duration and ok/not-ok from tool results", () => {
    assert.equal(eventDetailText(event({ kind: "turn/start" })), "");
    assert.equal(
      eventDetailText(event({ kind: "tool/result", detail: { duration_ms: 12, ok: true } })),
      "12 ms · ok"
    );
    assert.equal(
      eventDetailText(event({ kind: "tool/result", detail: { duration_ms: 8, ok: false } })),
      "8 ms · not ok"
    );
  });
});

describe("activity steps", () => {
  it("folds tool call+result into lab language and skips developer kinds", () => {
    const events = [
      event({ seq: 1, kind: "turn/start" }),
      event({ seq: 2, kind: "tool/call", name: "ask_user" }),
      event({ seq: 3, kind: "step/start", name: "ask" }),
      event({ seq: 4, kind: "tool/result", name: "ask_user", detail: { duration_ms: 40, ok: true } }),
      event({ seq: 5, kind: "tool/call", name: "run_checks" }),
      event({ seq: 6, kind: "tool/result", name: "run_checks", detail: { duration_ms: 1200, ok: true } }),
      event({ seq: 7, kind: "turn/end", detail: { ok: true } }),
    ];
    const steps = activitySteps(events, null);
    assert.equal(steps.length, 2);
    assert.equal(steps[0].label, "Asked you to confirm");
    assert.equal(steps[0].status, "ok");
    assert.equal(steps[1].label, "Checked bench constraints");
    assert.equal(formatDuration(1200), "1.2 s");
    assert.equal(activitySummary(steps), "2 steps · all passed");
    const running = activitySteps(events.slice(0, 5), "run_checks");
    assert.equal(running[1].status, "run");
    assert.equal(running[1].label, "Checking bench constraints…");
    const thinking = activitySteps(events.slice(0, 4), null, {
      thinking: true,
      thoughtTurns: [1],
      thinkingNote: "Confirm volumes and wells on the standard deck.",
    });
    assert.equal(thinking[0].name, "_think");
    assert.equal(thinking[0].label, "Thinking it through…");
    assert.equal(thinking[0].status, "run");
    assert.match(thinking[0].note || "", /volumes and wells/);
    assert.equal(thinking[1].label, "Asked you to confirm");
    const thought = activitySteps(events, null, {
      thoughtTurns: [1],
      thoughtNotes: { 1: "Confirm volumes and wells on the standard deck. Call ask_user and stop." },
    });
    assert.equal(thought[0].label, "Thought it through");
    assert.equal(thought[0].status, "ok");
    assert.equal(thought[0].note, undefined);
    assert.equal(activitySummary(thinking), "2 steps · 1 still going");
    const asked = activitySteps(
      [
        event({ seq: 1, kind: "tool/call", name: "ask_user" }),
        event({ seq: 2, kind: "tool/result", name: "ask_user", detail: { duration_ms: 1, ok: false } }),
      ],
      null
    );
    assert.equal(asked[0].status, "ok");
    assert.equal(asked[0].label, "Asked you to confirm");
    assert.equal(formatDuration(1), "");
    const withDeck = activitySteps(
      [
        event({ seq: 1, kind: "tool/call", name: "run_checks" }),
        event({ seq: 2, kind: "tool/result", name: "run_checks", detail: { duration_ms: 900, ok: true } }),
        event({ seq: 3, kind: "tool/call", name: "open_animation" }),
        event({ seq: 4, kind: "tool/result", name: "open_animation", detail: { duration_ms: 200, ok: true } }),
      ],
      null
    );
    assert.equal(withDeck.length, 1);
    assert.equal(withDeck[0].label, "Checked the bench — deck is up");
    assert.equal(
      withDeck.some((step) => /opened the preview/i.test(step.label)),
      false
    );
    assert.equal(activityStatusWord("run"), "Still going");
    assert.equal(labThinkNote("{ok:true}"), "");
    assert.match(labThinkNote("Confirm 20 µL on the standard deck."), /20 µL/);
    assert.equal(labThinkNote("Confirm 20 µL on the standard deck. Call ask_user and stop."), "");
    assert.equal(
      labThinkNote("User confirms the deck. Need compact SOP 400-800 chars. Output only specified."),
      ""
    );
    assert.equal(
      labThinkNote(
        "First turn: confirm volumes, wells, sample counts, mix, standard deck. Name the three slots in one sentence."
      ),
      ""
    );
    assert.equal(
      labThinkNote(
        "Need to give the one-sentence ask naming the three slots and stop. The user said \"Confirm the standard deck.\""
      ),
      ""
    );
    assert.equal(
      labThinkNote(
        "The user confirmed. Slot 3 is a 12-well reservoir. Standard deck confirmed. Bullets robot/pipettes, deck, reagents, numbered steps. Need from Goal volumes and wells."
      ),
      ""
    );
    assert.equal(
      labThinkNote(
        "User confirmed. mix only if needed new tip vs reuse - Assume: one line if you guessed Stop when technician can run. No summary, no repeated deck. Need include the volumes."
      ),
      ""
    );
    assert.equal(labThinkNote("Name the three slots in one sentence. No essay."), "");
    assert.equal(
      labThinkNote(
        "The tool returned a wait. The user confirmed the standard deck. Do not ask. Then stop."
      ),
      ""
    );
    assert.equal(
      labThinkNote(
        "First turn: confirm volumes, wells, mix, standard deck. But the instruction says \"At most one question\". Hardware: OT-2, API 2.15, left p300_single_gen2, gripper false."
      ),
      ""
    );
    assert.equal(
      labThinkNote(
        "Confirmed. Goal transfer 20 µL from plate A1 to B1. Reservoir slot3 not used? Reagents: sample in plate slot 2 well A1, volume? Could list sample, slot 2 A1,"
      ),
      ""
    );
    assert.equal(
      labThinkNote("one short confirm on volumes, wells, sample counts, mix, standard deck"),
      ""
    );
    const labOnly = labThinkNote(
      "User confirmed. 20 µL from plate A1 to B1. Reservoir slot 3 not used."
    );
    assert.match(labOnly, /User confirmed/i);
    assert.match(labOnly, /20 µL/);
    assert.match(labOnly, /slot 3/i);
    assert.doesNotMatch(labOnly, /Reagents:|Could list|volume\?/i);
    assert.match(
      labThinkNote("confirm volumes, wells, sample counts, mix, standard deck"),
      /confirm volumes/
    );
    assert.equal(
      thoughtNotesFromChat([
        { role: "user", text: "go" },
        { role: "assistant", text: "ok", thinking: "plan the wells" },
      ])[1],
      "plan the wells"
    );
    assert.equal(thoughtTurnsFromChat([
      { role: "user", text: "go" },
      { role: "assistant", text: "", thinking: "plan the wells" },
      { role: "user", text: "20 µL" },
      { role: "assistant", text: "ok", thinking: "write it" },
    ]).join(","), "1,2");
  });
});
