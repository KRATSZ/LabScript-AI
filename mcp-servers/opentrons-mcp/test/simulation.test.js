import test from "node:test";
import assert from "node:assert/strict";

import { parseSimulationLog } from "../lib/simulation.js";

test("parseSimulationLog classifies missing trash errors", () => {
  const result = parseSimulationLog({
    stderr: "Traceback ... NoTrashDefinedError: drop_tip() called without a trash bin",
    exit_code: 1,
    protocol_path: "/tmp/protocol.py",
  });

  assert.equal(result.success, false);
  assert.equal(result.issues[0].category, "MISSING_TRASH_OR_SETUP");
  assert.equal(result.issues[0].error_leaf, "MISSING_TRASH_OR_SETUP");
  assert.equal(result.primary_issue.error_domain, "protocol");
  assert.equal(result.issues[0].fixable_by_edit, true);
});

test("parseSimulationLog classifies syntax errors", () => {
  const result = parseSimulationLog({
    stderr:
      '  File "/tmp/protocol.py", line 8\n    pipette.pick_up_tip(\n                        ^\nSyntaxError: \'(\' was never closed',
    exit_code: 1,
    protocol_path: "/tmp/protocol.py",
  });

  assert.equal(result.success, false);
  assert.equal(result.issues[0].category, "SYNTAX_OR_IMPORT");
  assert.equal(result.error_leaf, "SYNTAX_OR_IMPORT");
  assert.equal(result.default_next_step, "edit_protocol_and_retry_simulation");
  assert.equal(result.line_references[0].line, 8);
});

test("parseSimulationLog passes clean output", () => {
  const result = parseSimulationLog({
    stdout: "Protocol simulation completed successfully.",
    stderr: "",
    exit_code: 0,
  });

  assert.equal(result.success, true);
  assert.equal(result.issue_count, 0);
  assert.equal(result.error_leaf, null);
  assert.equal(result.suggested_next_step, "simulation_passed_ready_for_execution");
});

test("parseSimulationLog does not misclassify successful trash drop logs", () => {
  const result = parseSimulationLog({
    stdout: "Dropping tip into Trash Bin on slot A3\n",
    stderr: "",
    exit_code: 0,
  });

  assert.equal(result.success, true);
  assert.equal(result.issue_count, 0);
});

test("parseSimulationLog classifies OutOfTipsError", () => {
  const result = parseSimulationLog({
    stderr: "OutOfTipsError [line 26]: ",
    exit_code: 1,
  });

  assert.equal(result.success, false);
  assert.equal(result.issues[0].category, "OUT_OF_TIPS");
  assert.equal(result.issues[0].fixable_by_edit, true);
});

test("parseSimulationLog classifies TipNotAttachedError", () => {
  const result = parseSimulationLog({
    stderr: 'ProtocolCommandFailedError [line 22]: TipNotAttachedError: Pipette should have a tip attached, but does not.',
    exit_code: 1,
  });

  assert.equal(result.success, false);
  assert.equal(result.issues[0].category, "OUT_OF_TIPS");
  assert.equal(result.issues[0].fixable_by_edit, true);
});
