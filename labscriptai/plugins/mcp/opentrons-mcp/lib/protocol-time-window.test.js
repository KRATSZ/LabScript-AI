import assert from "node:assert/strict";
import test from "node:test";

import {
  assessTimeWindow,
  findTimeWindowAnchor,
  isPlayBlockedByTimeWindow,
  parseProtocolTimeWindow,
} from "./protocol-time-window.js";

const windowProtocol = `
protocol.comment(
    "TIME WINDOW: complete Phase 2 within 10 minutes of Phase 1 "
    "or enzyme activity / assay validity is compromised"
)
`;

test("parseProtocolTimeWindow reads within N minutes across comment lines", () => {
  const parsed = parseProtocolTimeWindow(windowProtocol);
  assert.equal(parsed.declared, true);
  assert.equal(parsed.window_minutes, 10);
  assert.match(parsed.source_line, /TIME WINDOW/i);
  assert.equal(parsed.expired, false);
});

test("assessTimeWindow undeclared when protocol has no TIME WINDOW", () => {
  const assessed = assessTimeWindow({
    protocolSource: "protocol.comment('Phase 1 only')",
    commands: [],
  });
  assert.equal(assessed.declared, false);
  assert.equal(assessed.expired, false);
  assert.equal(assessed.window_minutes, null);
});

test("assessTimeWindow not expired when elapsed within window", () => {
  const anchorAt = "2026-07-31T10:00:00.000Z";
  const now = Date.parse(anchorAt) + 5 * 60 * 1000;
  const assessed = assessTimeWindow({
    protocolSource: windowProtocol,
    commands: [
      { id: "pick-1", commandType: "pickUpTip", status: "succeeded", completedAt: "2026-07-31T09:59:00.000Z" },
      { id: "disp-1", commandType: "dispenseInPlace", status: "succeeded", completedAt: anchorAt },
    ],
    now,
  });
  assert.equal(assessed.declared, true);
  assert.equal(assessed.expired, false);
  assert.equal(assessed.anchor_command_id, "disp-1");
  assert.equal(assessed.anchor_completed_at, anchorAt);
  assert.ok(assessed.elapsed_minutes < 10);
});

test("assessTimeWindow expired when elapsed exceeds window", () => {
  const anchorAt = "2026-07-31T10:00:00.000Z";
  const now = Date.parse(anchorAt) + 12 * 60 * 1000;
  const assessed = assessTimeWindow({
    protocolSource: windowProtocol,
    commands: [
      { id: "pick-1", commandType: "pickUpTip", status: "succeeded", completedAt: "2026-07-31T09:59:00.000Z" },
      { id: "disp-1", commandType: "dispenseInPlace", status: "succeeded", completedAt: anchorAt },
      { id: "drop-1", commandType: "dropTip", status: "succeeded", completedAt: "2026-07-31T10:00:30.000Z" },
      { id: "pick-2", commandType: "pickUpTip", status: "succeeded", completedAt: "2026-07-31T10:11:00.000Z" },
    ],
    now,
  });
  assert.equal(assessed.declared, true);
  assert.equal(assessed.expired, true);
  assert.equal(assessed.anchor_command_id, "disp-1");
  assert.ok(assessed.elapsed_minutes > 10);
});

test("findTimeWindowAnchor uses last Phase-1 dispense before second pickup", () => {
  const anchor = findTimeWindowAnchor([
    { id: "pick-1", commandType: "pickUpTip", status: "succeeded" },
    { id: "disp-1", commandType: "dispenseInPlace", status: "succeeded", completedAt: "2026-07-31T10:00:00.000Z" },
    { id: "disp-2", commandType: "dispenseInPlace", status: "succeeded", completedAt: "2026-07-31T10:00:10.000Z" },
    { id: "pick-2", commandType: "pickUpTip", status: "succeeded" },
    { id: "disp-3", commandType: "dispenseInPlace", status: "succeeded", completedAt: "2026-07-31T10:20:00.000Z" },
  ]);
  assert.equal(anchor.anchor_command_id, "disp-2");
});

test("findTimeWindowAnchor accepts plain dispense (fake robot / non-InPlace)", () => {
  const anchor = findTimeWindowAnchor([
    { id: "pick-1", commandType: "pickUpTip", status: "succeeded" },
    { id: "disp-1", commandType: "dispense", status: "succeeded", completedAt: "2026-07-31T10:00:00.000Z" },
    { id: "pick-2", commandType: "pickUpTip", status: "succeeded" },
  ]);
  assert.equal(anchor.anchor_command_id, "disp-1");
  assert.equal(anchor.anchor_completed_at, "2026-07-31T10:00:00.000Z");
});

test("isPlayBlockedByTimeWindow only when declared and expired", () => {
  assert.equal(isPlayBlockedByTimeWindow({ declared: true, expired: true }), true);
  assert.equal(isPlayBlockedByTimeWindow({ declared: true, expired: false }), false);
  assert.equal(isPlayBlockedByTimeWindow({ declared: false, expired: true }), false);
  assert.equal(isPlayBlockedByTimeWindow(null), false);
});

test("unknown time-window evidence always blocks play", () => {
  const unknown = {
    declared: true,
    expired: false,
    time_window_unknown: true,
  };
  assert.equal(isPlayBlockedByTimeWindow(unknown), true);
  assert.equal(isPlayBlockedByTimeWindow(unknown, { allowExpired: true }), true);
  assert.equal(
    isPlayBlockedByTimeWindow({ declared: true, expired: true }, { allowExpired: true }),
    false,
  );
});
