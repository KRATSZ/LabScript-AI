import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { buildHealthCheck } from "../lib/health-check.js";

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
});
