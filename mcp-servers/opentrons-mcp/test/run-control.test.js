import test from "node:test";
import assert from "node:assert/strict";

import {
  buildRunProtocolResult,
  isTerminalRunStatus,
  shouldAttachRecoveryGuidance,
} from "../lib/run-control.js";

test("isTerminalRunStatus recognizes terminal and intervention-required states", () => {
  assert.equal(isTerminalRunStatus("succeeded"), true);
  assert.equal(isTerminalRunStatus("awaiting-recovery"), true);
  assert.equal(isTerminalRunStatus("blocked-by-open-door"), true);
  assert.equal(isTerminalRunStatus("running"), false);
});

test("shouldAttachRecoveryGuidance only flags failed and awaiting-recovery runs", () => {
  assert.equal(shouldAttachRecoveryGuidance("failed"), true);
  assert.equal(shouldAttachRecoveryGuidance("awaiting-recovery"), true);
  assert.equal(shouldAttachRecoveryGuidance("blocked-by-open-door"), false);
});

test("buildRunProtocolResult marks intervention-required states", () => {
  const result = buildRunProtocolResult({
    protocol: { data: { id: "protocol-1" } },
    created_run: { data: { id: "run-1" } },
    play_action: { data: { id: "action-1" } },
    final_run_history: { run_id: "run-1", status: "blocked-by-open-door" },
  });

  assert.equal(result.final_status, "blocked-by-open-door");
  assert.equal(result.requires_attention, true);
  assert.equal(result.protocol.data.id, "protocol-1");
});
