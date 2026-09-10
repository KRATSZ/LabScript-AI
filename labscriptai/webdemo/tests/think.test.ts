import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { codeThinkingToken } from "../server/src/think.ts";

describe("code thinking heartbeats", () => {
  it("ignores heartbeat-only messages", () => {
    assert.equal(codeThinkingToken({ event_type: "thinking", message: "Model is reasoning..." }), "");
    assert.equal(codeThinkingToken({ event_type: "thinking", message: "model is reasoning..." }), "");
    assert.equal(codeThinkingToken({ message: "MODEL IS REASONING..." }), "");
    assert.equal(codeThinkingToken({ token: "", message: "Model is reasoning..." }), "");
  });

  it("keeps real reasoning tokens", () => {
    assert.equal(
      codeThinkingToken({ token: "I will load labware" }),
      "I will load labware"
    );
    assert.equal(
      codeThinkingToken({ token: "", message: "I will load labware" }),
      "I will load labware"
    );
    assert.equal(
      codeThinkingToken({
        token: "I will load labware",
        message: "Model is reasoning...",
      }),
      "I will load labware"
    );
  });
});
