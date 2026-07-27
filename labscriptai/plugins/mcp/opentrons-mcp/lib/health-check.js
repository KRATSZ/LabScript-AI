import { execFileSync, execSync } from "child_process";
import fs from "fs";

import { requestRobotJson } from "./http.js";
import { PLUGIN_ROOT, SESSION_STATE_DIR, firstExistingPath, resolvePythonCandidates } from "./paths.js";

export const MCP_RUNTIME_CAPABILITIES = {
  runtime_build: "liquid-source-map-v2",
  liquid_not_found_classification: true,
  liquid_source_map: true,
  liquid_source_map_readback: true,
  liquid_expected_absent_mismatch: true,
  manual_only_liquid_recovery: true,
  tip_continuation_protocol: true,
  liquid_source_substitution_recovery_playbook: true,
  safe_drop_attached_tip: true,
  virtual_lab_state_validation: true,
  virtual_lab_state_simulate_gate: true,
  runtime_watch_loop: true,
};

function resolveHealthPython(args = {}) {
  return args.python_executable || firstExistingPath(resolvePythonCandidates()) || process.env.OPENTRONS_PYTHON || "python3";
}

function isPathLikeExecutable(value = "") {
  return String(value).includes("/") || String(value).includes("\\");
}

/**
 * Run a comprehensive health check of the MCP server environment.
 *
 * @param {object} args
 * @param {string} [args.robot_ip] - Optional robot IP to check connectivity.
 * @returns {object} Structured health report.
 */
export function buildHealthCheck(args = {}) {
  const selectedPython = resolveHealthPython(args);
  const report = {
    timestamp: new Date().toISOString(),
    mcp_server: {
      status: "ok",
      capabilities: MCP_RUNTIME_CAPABILITIES,
    },
    venv: { status: "unknown" },
    robot: { status: "not_checked" },
    git: {},
    session: { status: "clean" },
  };

  // --- Venv check ---
  const venvPython = selectedPython;
  report.venv.python_executable = venvPython;
  if (!fs.existsSync(venvPython) && isPathLikeExecutable(venvPython)) {
    report.venv.status = "missing";
    report.venv.hint = args.python_executable || process.env.OPENTRONS_PYTHON
      ? "Provided python_executable does not exist; check the path or OPENTRONS_PYTHON."
      : "Run: uv venv .venv && uv sync --extra protocol";
  } else {
    try {
      const version = execFileSync(venvPython, ["-c", "import sys; print(sys.version.split()[0])"], {
        timeout: 15000,
        encoding: "utf8",
      }).trim();
      report.venv.python = version;
      report.venv.status = "ok";
    } catch {
      report.venv.status = "broken";
      report.venv.error = "venv python failed to run";
    }

    try {
      const otVersion = execFileSync(
        venvPython,
        ["-c", "import opentrons; print(opentrons.__version__)"],
        { timeout: 15000, encoding: "utf8" }
      ).trim();
      report.venv.opentrons = otVersion;
    } catch {
      report.venv.opentrons = "not_installed";
      report.venv.opentrons_hint = "Run: uv sync --extra protocol";
    }
  }

  // --- Git state ---
  try {
    report.git.branch = execSync("git rev-parse --abbrev-ref HEAD", {
      cwd: PLUGIN_ROOT,
      timeout: 3000,
      encoding: "utf8",
    }).trim();

    const porcelain = execSync("git status --porcelain", {
      cwd: PLUGIN_ROOT,
      timeout: 3000,
      encoding: "utf8",
    }).trim();
    report.git.uncommitted_changes = porcelain ? porcelain.split("\n").length : 0;
  } catch {
    report.git.status = "not_a_git_repo";
  }

  // --- Session state ---
  const sessionDir = SESSION_STATE_DIR;
  if (fs.existsSync(sessionDir)) {
    const files = fs.readdirSync(sessionDir).filter((f) => f.endsWith(".json"));
    if (files.length > 0) {
      report.session.status = "has_active_session";
      report.session.files = files;
    }
  }

  // --- Robot connectivity (async, handled by caller) ---
  // If robot_ip is provided, the TOOL_HANDLER will check it via HTTP.

  return report;
}

/**
 * Check robot connectivity via HTTP /health endpoint.
 * Returns a snapshot object (does not throw).
 */
export async function checkRobotHealth(robotIp) {
  if (!robotIp) return { status: "not_checked" };

  try {
    const body = await requestRobotJson("GET", robotIp, "/health");
    return {
      status: "reachable",
      ip: robotIp,
      robot_model: body?.robotModel || body?.name || "unknown",
      robot_serial: body?.serialNumber || "unknown",
      api_version: body?.apiVersion || body?.version || "unknown",
    };
  } catch (err) {
    return {
      status: "unreachable",
      ip: robotIp,
      error: err.code || err.message,
    };
  }
}
