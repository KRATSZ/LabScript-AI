import assert from "node:assert/strict";
import test from "node:test";

import { TOOL_HANDLERS } from "./index.js";

test("control_run blocks play when time-window evidence is unavailable", async () => {
  const result = await TOOL_HANDLERS.control_run({
    robot_ip: "http://127.0.0.1:9",
    run_id: "run-without-protocol-source",
    action: "play",
    protocol_path: "/definitely/missing/protocol.py",
    allow_expired_time_window: true,
  });

  assert.equal(result.data.blocked, true);
  assert.equal(result.data.blocked_reason, "time_window_evidence_unavailable");
  assert.equal(result.data.time_window.time_window_unknown, true);
});
