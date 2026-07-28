import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  enrichRecoveryArgsWithProtocolPath,
  extractProtocolNameFromSource,
  resolveLocalProtocolByName,
  resolveProtocolPathForRecovery,
} from "./protocol-path.js";

test("extractProtocolNameFromSource reads metadata.protocolName", () => {
  const name = extractProtocolNameFromSource(
    'metadata = {"protocolName": "Triple transfer chain", "author": "x"}',
  );
  assert.equal(name, "Triple transfer chain");
});

test("resolveProtocolPathForRecovery prefers session protocol_path", () => {
  const withTmp = fs.mkdtempSync(path.join(os.tmpdir(), "protocol-path-"));
  const protocolFile = path.join(withTmp, "demo.py");
  fs.writeFileSync(protocolFile, 'metadata = {"protocolName": "Demo"}\n');

  const resolved = resolveProtocolPathForRecovery(
    { run_id: "run-123" },
    {
      readSessionState: runId => {
        assert.equal(runId, "run-123");
        return { protocol_path: protocolFile };
      },
    },
  );
  assert.equal(resolved, path.resolve(protocolFile));
  fs.rmSync(withTmp, { recursive: true, force: true });
});

test("resolveLocalProtocolByName matches workspace local/*.py", () => {
  const withTmp = fs.mkdtempSync(path.join(os.tmpdir(), "protocol-name-"));
  const localDir = path.join(withTmp, "local");
  fs.mkdirSync(localDir, { recursive: true });
  const protocolFile = path.join(localDir, "02_demo.py");
  fs.writeFileSync(
    protocolFile,
    'metadata = {"protocolName": "Triple transfer chain"}\n# tip_budget: pick_up_tip_count=3\n',
  );

  const previous = process.env.LABSCRIPTAI_WORKSPACE;
  process.env.LABSCRIPTAI_WORKSPACE = withTmp;
  try {
    const matched = resolveLocalProtocolByName("Triple transfer chain", withTmp);
    assert.equal(matched, protocolFile);
    const enriched = enrichRecoveryArgsWithProtocolPath({
      run_id: "run-abc",
      protocol_name: "Triple transfer chain",
    });
    assert.equal(enriched.file_path, protocolFile);
  } finally {
    if (previous === undefined) {
      delete process.env.LABSCRIPTAI_WORKSPACE;
    } else {
      process.env.LABSCRIPTAI_WORKSPACE = previous;
    }
    fs.rmSync(withTmp, { recursive: true, force: true });
  }
});
