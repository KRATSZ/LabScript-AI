import fs from "fs";
import path from "path";

import { readResultLogEntries } from "./result-log.js";

export function extractProtocolNameFromSource(source = "") {
  const match = String(source).match(/["']protocolName["']\s*:\s*["']([^"']+)["']/);
  return match ? match[1].trim() : null;
}

function resolveExistingPath(candidate) {
  if (!candidate) {
    return null;
  }
  const resolved = path.resolve(String(candidate));
  return fs.existsSync(resolved) ? resolved : null;
}

function listWorkspaceProtocolFiles(workspaceRoot) {
  const localDir = path.join(path.resolve(workspaceRoot), "local");
  if (!fs.existsSync(localDir)) {
    return [];
  }
  return fs
    .readdirSync(localDir)
    .filter(name => name.endsWith(".py"))
    .map(name => path.join(localDir, name))
    .filter(candidate => fs.existsSync(candidate));
}

export function resolveLocalProtocolByName(protocolName, workspaceRoot) {
  const needle = String(protocolName || "").trim();
  if (!needle || !workspaceRoot) {
    return null;
  }
  for (const candidate of listWorkspaceProtocolFiles(workspaceRoot)) {
    const source = fs.readFileSync(candidate, "utf8");
    if (
      source.includes(`"protocolName": "${needle}"`) ||
      source.includes(`"protocolName":"${needle}"`) ||
      source.includes(`'protocolName': '${needle}'`)
    ) {
      return candidate;
    }
  }
  return null;
}

function protocolPathFromResultLogs(runId, limit = 50) {
  if (!runId) {
    return { protocolPath: null, protocolName: null };
  }
  let protocolName = null;
  for (const entry of readResultLogEntries({ run_id: runId, limit })) {
    const candidate =
      entry?.protocol_path || entry?.data?.protocol_path || entry?.data?.file_path || null;
    const resolved = resolveExistingPath(candidate);
    if (resolved) {
      return { protocolPath: resolved, protocolName: entry?.protocol_name || protocolName };
    }
    if (!protocolName && entry?.protocol_name) {
      protocolName = entry.protocol_name;
    }
  }
  return { protocolPath: null, protocolName };
}

/**
 * Resolve a protocol .py path for recovery / tip-budget / time-window parsing.
 * Uses explicit args, session state (run_id then session_id), result logs, env,
 * then workspace heuristics.
 */
export function resolveProtocolPathForRecovery(args = {}, deps = {}) {
  const readSessionState = deps.readSessionState || (() => ({}));

  const direct = resolveExistingPath(args.file_path || args.protocol_path);
  if (direct) {
    return direct;
  }

  const sessionIds = [...new Set([args.run_id, args.session_id].filter(Boolean))];
  for (const sessionId of sessionIds) {
    const session = readSessionState(sessionId) || {};
    const sessionPath = resolveExistingPath(session.protocol_path);
    if (sessionPath) {
      return sessionPath;
    }
  }

  const { protocolPath: loggedPath, protocolName: loggedName } = protocolPathFromResultLogs(args.run_id);
  if (loggedPath) {
    return loggedPath;
  }

  const envProtocol = resolveExistingPath(process.env.LABSCRIPTAI_PROTOCOL_PATH);
  if (envProtocol) {
    return envProtocol;
  }

  const workspace = process.env.LABSCRIPTAI_WORKSPACE;
  if (workspace) {
    const pyFiles = listWorkspaceProtocolFiles(workspace);
    if (pyFiles.length === 1) {
      return pyFiles[0];
    }
    const protocolName = args.protocol_name || loggedName;
    const matched = resolveLocalProtocolByName(protocolName, workspace);
    if (matched) {
      return matched;
    }
  }

  return null;
}

export function enrichRecoveryArgsWithProtocolPath(args = {}, deps = {}) {
  const resolved = resolveProtocolPathForRecovery(args, deps);
  if (!resolved || args.file_path || args.protocol_path) {
    return args;
  }
  return { ...args, file_path: resolved };
}
