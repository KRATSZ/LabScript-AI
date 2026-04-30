import { execSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, "../../../");

/**
 * Run a comprehensive health check of the MCP server environment.
 *
 * @param {object} args
 * @param {string} [args.robot_ip] - Optional robot IP to check connectivity.
 * @returns {object} Structured health report.
 */
export function buildHealthCheck(args = {}) {
  const report = {
    timestamp: new Date().toISOString(),
    mcp_server: { status: "ok" },
    venv: { status: "unknown" },
    robot: { status: "not_checked" },
    git: {},
    session: { status: "clean" },
  };

  // --- Venv check ---
  const venvPython = path.join(PROJECT_ROOT, ".venv/bin/python");
  if (fs.existsSync(venvPython)) {
    try {
      const version = execSync(`${venvPython} -c "import sys; print(sys.version.split()[0])"`, {
        timeout: 5000,
        encoding: "utf8",
      }).trim();
      report.venv.python = version;
      report.venv.status = "ok";
    } catch {
      report.venv.status = "broken";
      report.venv.error = "venv python failed to run";
    }

    try {
      const otVersion = execSync(
        `${venvPython} -c "import opentrons; print(opentrons.__version__)"`,
        { timeout: 8000, encoding: "utf8" }
      ).trim();
      report.venv.opentrons = otVersion;
    } catch {
      report.venv.opentrons = "not_installed";
      report.venv.opentrons_hint = "Run: uv sync --extra protocol";
    }
  } else {
    report.venv.status = "missing";
    report.venv.hint = "Run: uv venv .venv && uv sync --extra protocol";
  }

  // --- Git state ---
  try {
    report.git.branch = execSync("git rev-parse --abbrev-ref HEAD", {
      cwd: PROJECT_ROOT,
      timeout: 3000,
      encoding: "utf8",
    }).trim();

    const porcelain = execSync("git status --porcelain", {
      cwd: PROJECT_ROOT,
      timeout: 3000,
      encoding: "utf8",
    }).trim();
    report.git.uncommitted_changes = porcelain ? porcelain.split("\n").length : 0;
  } catch {
    report.git.status = "not_a_git_repo";
  }

  // --- Session state ---
  const sessionDir = path.join(__dirname, "..", "data", "session-state");
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

  const url = robotIp.includes("://")
    ? `${robotIp}/health`
    : `http://${robotIp}:31950/health`;

  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 5000);
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);

    if (!res.ok) {
      return { status: "error", http_status: res.status, ip: robotIp };
    }
    const body = await res.json();
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
