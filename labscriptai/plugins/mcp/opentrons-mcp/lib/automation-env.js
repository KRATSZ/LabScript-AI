import fs from "fs";
import path from "path";

import { PLUGIN_ROOT } from "./paths.js";

/**
 * Resolve which .env file to read for automation secrets (ARK_API_KEY, etc.).
 *
 * Priority when envFilePath is omitted:
 * 1. <repo-root>/.env          — Opentrons-Lab-Agent root (preferred in core)
 * 2. <PLUGIN_ROOT>/../.env     — same when PLUGIN_ROOT is core/mcp
 * 3. <PLUGIN_ROOT>/automation/.env — legacy labscriptai-ot plugin layout
 */
export function resolveAutomationEnvPath(envFilePath = null) {
  if (envFilePath) {
    return path.resolve(envFilePath);
  }

  const candidates = [];
  // Vendored layout: PLUGIN_ROOT = <repo>/core/mcp
  candidates.push(path.resolve(PLUGIN_ROOT, "../../.env")); // repo root (preferred)
  candidates.push(path.resolve(PLUGIN_ROOT, "../.env")); // core/.env
  candidates.push(path.join(PLUGIN_ROOT, ".env"));
  // Legacy plugin layout.
  candidates.push(path.join(PLUGIN_ROOT, "automation", ".env"));

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  // Prefer repo-root path even if missing (caller handles null read).
  return candidates[0];
}

function normalizeEnvKey(rawKey) {
  return rawKey.trim().replace(/\s+/g, "_").toUpperCase();
}

export function parseAutomationEnvLine(line) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith("#")) {
    return null;
  }

  const eqMatch = trimmed.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
  if (eqMatch) {
    return {
      key: eqMatch[1],
      value: eqMatch[2].replace(/^['"]|['"]$/g, "").trim(),
    };
  }

  const colonIndex = trimmed.indexOf(":");
  if (colonIndex > 0) {
    return {
      key: normalizeEnvKey(trimmed.slice(0, colonIndex)),
      value: trimmed.slice(colonIndex + 1).replace(/^['"]|['"]$/g, "").trim(),
    };
  }

  return null;
}

export function loadAutomationEnvValue(envVarName, { envFilePath = null } = {}) {
  if (process.env[envVarName]) {
    return process.env[envVarName];
  }

  const filePath = resolveAutomationEnvPath(envFilePath);
  if (!fs.existsSync(filePath)) {
    return null;
  }

  try {
    const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
    const target = normalizeEnvKey(envVarName);
    for (const line of lines) {
      const parsed = parseAutomationEnvLine(line);
      if (parsed && normalizeEnvKey(parsed.key) === target) {
        return parsed.value;
      }
    }
  } catch {
    return null;
  }

  return null;
}
