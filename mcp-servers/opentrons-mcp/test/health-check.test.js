import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import os from "os";
import path from "path";
import { buildHealthCheck, checkRobotHealth } from "../lib/health-check.js";

describe("health_check", () => {
  it("returns a structured report without robot_ip", () => {
    const report = buildHealthCheck({});
    assert.ok(report.timestamp);
    assert.equal(report.mcp_server.status, "ok");
    assert.ok(report.venv);
    assert.ok(report.git);
    assert.ok(report.session);
    // In CI or fresh checkout venv may not exist, just check structure
    assert.ok(["ok", "missing", "broken"].includes(report.venv.status));
  });

  it("detects venv and opentrons if present", () => {
    const report = buildHealthCheck({});
    // If venv exists (real dev environment), check for python version
    if (report.venv.status === "ok") {
      assert.ok(report.venv.python);
      assert.ok(
        report.venv.opentrons || report.venv.opentrons === "not_installed"
      );
    }
  });

  it("detects git branch", () => {
    const report = buildHealthCheck({});
    if (report.git.branch) {
      assert.ok(typeof report.git.branch === "string");
      assert.equal(typeof report.git.uncommitted_changes, "number");
    }
  });

  it("accepts robot_ip values with an explicit port", async () => {
    const originalFetch = global.fetch;
    global.fetch = async url =>
      new Response(JSON.stringify({ robotModel: "OT-3 Standard", serialNumber: "FLX-1" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });

    try {
      const report = await checkRobotHealth("10.31.2.149:31950");
      assert.equal(report.status, "reachable");
      assert.equal(report.ip, "10.31.2.149:31950");
    } finally {
      global.fetch = originalFetch;
    }
  });

  it("respects python_executable override for local runtime inspection", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "health-check-python-"));
    const fakePython = path.join(dir, "python");
    fs.writeFileSync(
      fakePython,
      [
        "#!/bin/sh",
        'case "$2" in',
        '  *"import sys; print(sys.version.split()[0])"*) echo "3.12.0" ;;',
        '  *"import opentrons; print(opentrons.__version__)"*) echo "9.9.9" ;;',
        "  *) exit 1 ;;",
        "esac",
        "",
      ].join("\n"),
    );
    fs.chmodSync(fakePython, 0o755);

    const report = buildHealthCheck({ python_executable: fakePython });
    assert.equal(report.venv.python_executable, fakePython);
    assert.equal(report.venv.status, "ok");
    assert.equal(report.venv.opentrons, "9.9.9");
  });
});
