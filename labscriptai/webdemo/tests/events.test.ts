import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { appendEvent, emitAgentEvent, TOOL_STEP } from "../server/src/events.ts";

describe("agent event log", () => {
  it("appends turn/step/tool facts in order", () => {
    const sink = { events: [] as ReturnType<typeof appendEvent>[] };
    appendEvent(sink, { kind: "turn/start", t: 1 });
    appendEvent(sink, { kind: "tool/call", name: "generate_sop", t: 2 });
    appendEvent(sink, { kind: "step/start", name: TOOL_STEP.generate_sop, t: 2 });
    appendEvent(sink, { kind: "tool/result", name: "generate_sop", t: 3, detail: { duration_ms: 10 } });
    appendEvent(sink, { kind: "step/end", name: "sop", t: 3 });
    appendEvent(sink, { kind: "turn/end", t: 4, detail: { ok: true } });
    assert.deepEqual(
      sink.events.map((event) => event.kind),
      ["turn/start", "tool/call", "step/start", "tool/result", "step/end", "turn/end"]
    );
    assert.equal(sink.events[0].seq, 1);
    assert.equal(sink.events[5].seq, 6);
    assert.equal(sink.events[1].name, "generate_sop");
  });

  it("mirrors each append onto SSE as agent_event", () => {
    const frames: Array<{ event: string; data: unknown }> = [];
    const sink = { events: [] as ReturnType<typeof appendEvent>[] };
    emitAgentEvent(
      sink,
      {
        write(event, data) {
          frames.push({ event, data });
        },
        close() {},
      },
      { kind: "tool/call", name: "run_checks", t: 9 }
    );
    assert.equal(frames.length, 1);
    assert.equal(frames[0].event, "agent_event");
    const payload = frames[0].data as { kind: string; name: string; seq: number };
    assert.equal(payload.kind, "tool/call");
    assert.equal(payload.name, "run_checks");
    assert.equal(payload.seq, 1);
    assert.equal(sink.events.length, 1);
  });
});
