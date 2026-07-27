import fs from "fs";
import path from "path";
import { randomUUID } from "crypto";

import { DEFAULT_SESSION_ID } from "./state.js";
import { RESULT_LOG_DIR } from "./paths.js";

function resultLogDir() {
  return process.env.OPENTRONS_RESULT_LOG_DIR
    ? path.resolve(process.env.OPENTRONS_RESULT_LOG_DIR)
    : RESULT_LOG_DIR;
}

function sanitizeSessionId(sessionId = DEFAULT_SESSION_ID) {
  return String(sessionId || DEFAULT_SESSION_ID).replace(/[^a-zA-Z0-9._-]/g, "_");
}

function sessionLogPath(sessionId = DEFAULT_SESSION_ID) {
  return path.join(resultLogDir(), `${sanitizeSessionId(sessionId)}.jsonl`);
}

function ensureResultLogDirectory() {
  fs.mkdirSync(resultLogDir(), { recursive: true });
}

function normalizeEntry(entry = {}) {
  const sessionId = sanitizeSessionId(entry.session_id || entry.sessionId || DEFAULT_SESSION_ID);
  const protocolPath = entry.protocol_path ? path.resolve(entry.protocol_path) : null;
  const timestamp = entry.timestamp || new Date().toISOString();
  return {
    entry_id: entry.entry_id || randomUUID(),
    timestamp,
    session_id: sessionId,
    run_id: entry.run_id || null,
    tool_name: entry.tool_name || "unknown_tool",
    event_kind: entry.event_kind || entry.tool_name || "unknown_event",
    status: entry.status || "completed",
    summary: entry.summary || null,
    protocol_path: protocolPath,
    protocol_name: entry.protocol_name || (protocolPath ? path.basename(protocolPath) : null),
    robot_ip: entry.robot_ip || null,
    state_revision: Number(entry.state_revision || 0),
    requires_attention:
      typeof entry.requires_attention === "boolean" ? entry.requires_attention : null,
    data: entry.data || {},
    error: entry.error || null,
  };
}

function parseLogLine(line) {
  const trimmed = String(line || "").trim();
  if (!trimmed) {
    return null;
  }
  try {
    return JSON.parse(trimmed);
  } catch {
    return null;
  }
}

function entryMatchesFilters(entry, filters = {}) {
  if (filters.session_id && entry.session_id !== sanitizeSessionId(filters.session_id)) {
    return false;
  }
  if (filters.run_id && entry.run_id !== filters.run_id) {
    return false;
  }
  if (filters.tool_name && entry.tool_name !== filters.tool_name) {
    return false;
  }
  if (filters.event_kind && entry.event_kind !== filters.event_kind) {
    return false;
  }
  if (filters.status && entry.status !== filters.status) {
    return false;
  }
  return true;
}

export function appendResultLogEntry(entry = {}) {
  ensureResultLogDirectory();
  const normalized = normalizeEntry(entry);
  fs.appendFileSync(sessionLogPath(normalized.session_id), `${JSON.stringify(normalized)}\n`);
  return normalized;
}

export function readResultLogEntries(filters = {}) {
  ensureResultLogDirectory();
  const logFiles = filters.session_id
    ? [sessionLogPath(filters.session_id)]
    : fs
        .readdirSync(resultLogDir(), { withFileTypes: true })
        .filter(entry => entry.isFile() && entry.name.endsWith(".jsonl"))
        .map(entry => path.join(resultLogDir(), entry.name));

  const entries = [];
  for (const filePath of logFiles) {
    if (!fs.existsSync(filePath)) {
      continue;
    }
    const raw = fs.readFileSync(filePath, "utf8");
    for (const line of raw.split("\n")) {
      const entry = parseLogLine(line);
      if (!entry) {
        continue;
      }
      if (entryMatchesFilters(entry, filters)) {
        entries.push(entry);
      }
    }
  }

  entries.sort((left, right) => String(right.timestamp).localeCompare(String(left.timestamp)));
  const limit = Math.max(1, Math.min(Number(filters.limit || 20), 200));
  return entries.slice(0, limit);
}

export function summarizeResultLogEntries(entries = []) {
  return entries.reduce(
    (summary, entry) => {
      summary.total += 1;
      summary.by_tool[entry.tool_name] = (summary.by_tool[entry.tool_name] || 0) + 1;
      summary.by_status[entry.status] = (summary.by_status[entry.status] || 0) + 1;
      summary.by_event_kind[entry.event_kind] = (summary.by_event_kind[entry.event_kind] || 0) + 1;
      return summary;
    },
    {
      total: 0,
      by_tool: {},
      by_status: {},
      by_event_kind: {},
    },
  );
}
