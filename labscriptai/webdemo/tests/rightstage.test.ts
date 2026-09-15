import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { tabCount } from "../web/src/stageTabs.ts";
import { eventDetailText } from "../web/src/trajectoryLogic.ts";
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
    assert.equal(tabCount("trajectory", session, events), 2);
    assert.equal(tabCount("artifacts", null, []), 0);
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
