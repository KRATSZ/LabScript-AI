import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { tabCount, tabVisible } from "../web/src/stageTabs.ts";
import { activitySteps, activitySummary, eventDetailText, formatDuration } from "../web/src/trajectoryLogic.ts";
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
  });
});
