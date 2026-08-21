import fs from "fs";
import path from "path";
import { spawn } from "child_process";

import { resolvePythonCandidates, SCRIPTS_DIR, ARTIFACTS_DIR } from "./paths.js";
import {
  PRESSURE_CSV_B64_PREFIX,
  PRESSURE_CSV_FIELDNAMES,
} from "./pressure-protocol.js";

const pressureCheckScriptPath = path.join(SCRIPTS_DIR, "pressure_trace_check.py");
const fetchPressureScriptPath = path.join(SCRIPTS_DIR, "fetch_robot_pressure_csv.py");

export const DEFAULT_PRESSURE_ARTIFACT_DIR = path.join(ARTIFACTS_DIR, "pressure-traces");

/** @deprecated Prefer PRESSURE_CSV_FIELDNAMES / canonical schema. Kept for legacy two-column CSVs. */
export const PRESSURE_CSV_COLUMNS = Object.freeze(["t_ms", "pressure_pa"]);

export { PRESSURE_CSV_B64_PREFIX, PRESSURE_CSV_FIELDNAMES };

function unwrapData(payload) {
  if (payload && typeof payload === "object" && "data" in payload) {
    return payload.data;
  }
  return payload;
}

function asArray(value) {
  if (Array.isArray(value)) {
    return value;
  }
  if (value && typeof value === "object") {
    return Object.values(value);
  }
  return [];
}

function readNested(value, candidates, fallback = null) {
  for (const candidate of candidates) {
    let current = value;
    let found = true;
    for (const part of candidate) {
      if (current && typeof current === "object" && part in current) {
        current = current[part];
      } else {
        found = false;
        break;
      }
    }
    if (found && current !== undefined) {
      return current;
    }
  }
  return fallback;
}

function runCommand(command, args, stdinJson = null) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: process.cwd(),
      env: process.env,
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", chunk => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", chunk => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", code => {
      resolve({ code, stdout, stderr, command, args });
    });

    if (stdinJson) {
      child.stdin.write(JSON.stringify(stdinJson));
      child.stdin.end();
    } else {
      child.stdin.end();
    }
  });
}

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch (error) {
    return {
      parse_error: error.message,
      raw_stdout: text,
    };
  }
}

function commentMessages(commandsPayload) {
  return asArray(unwrapData(commandsPayload))
    .filter(command => readNested(command, [["commandType"], ["command_type"]]) === "comment")
    .map(command => readNested(command, [["params", "message"], ["data", "params", "message"]], null))
    .map(message => String(message || ""))
    .filter(Boolean);
}

/**
 * Parse run comments for pressure evidence.
 * Canonical: last PRESSURE_CSV_B64:<base64> wins.
 * Legacy: PRESSURE_TRACE chunked comments reassembled when no B64 present.
 */
export function extractPressureTracesFromCommands(commandsPayload) {
  const messages = commentMessages(commandsPayload);
  const errors = [];
  const b64Payloads = [];
  const chunkGroups = new Map();

  for (const message of messages) {
    if (message.startsWith(PRESSURE_CSV_B64_PREFIX)) {
      b64Payloads.push(message.slice(PRESSURE_CSV_B64_PREFIX.length));
      continue;
    }
    if (message.startsWith("PRESSURE_TRACE_ERROR:")) {
      try {
        const payload = JSON.parse(message.slice("PRESSURE_TRACE_ERROR:".length));
        errors.push({ ...payload, observation_only: true, advisory: true });
      } catch {
        errors.push({
          error: message.slice("PRESSURE_TRACE_ERROR:".length),
          observation_only: true,
          advisory: true,
        });
      }
      continue;
    }

    const match = message.match(/^PRESSURE_TRACE:([^:]+):(\d+)\/(\d+):(.+)$/);
    if (match) {
      const [, well, idx, total, b64] = match;
      const key = String(well).toUpperCase();
      if (!chunkGroups.has(key)) {
        chunkGroups.set(key, { well: key, total: Number(total), parts: new Map() });
      }
      const group = chunkGroups.get(key);
      group.total = Number(total);
      group.parts.set(Number(idx), b64);
      continue;
    }

    const legacy = message.match(/^PRESSURE_TRACE:(\d+)\/(\d+):(.+)$/);
    if (legacy) {
      const [, idx, total, b64] = legacy;
      const key = "_";
      if (!chunkGroups.has(key)) {
        chunkGroups.set(key, { well: null, total: Number(total), parts: new Map() });
      }
      chunkGroups.get(key).parts.set(Number(idx), b64);
      chunkGroups.get(key).total = Number(total);
    }
  }

  const traces = [];

  if (b64Payloads.length > 0) {
    const last = b64Payloads[b64Payloads.length - 1];
    try {
      const csvText = Buffer.from(last, "base64").toString("utf8");
      const samples = parsePressureCsv(csvText);
      traces.push({
        well: samples.find(s => s.well)?.well || null,
        success: samples.length > 0,
        source: "PRESSURE_CSV_B64",
        observation_only: true,
        advisory: true,
        units: { t: "ms", pressure: "Pa", z: "mm" },
        columns: [...PRESSURE_CSV_FIELDNAMES],
        samples,
        csv_text: csvText,
        sample_count: samples.length,
        comment_rewrites: b64Payloads.length,
      });
    } catch (error) {
      traces.push({
        success: false,
        source: "PRESSURE_CSV_B64",
        error: `base64 decode failed: ${error.message}`,
        observation_only: true,
        advisory: true,
        samples: [],
        csv_text: null,
      });
    }
  }

  // Legacy chunk path only if no canonical payload
  if (traces.length === 0) {
    for (const group of chunkGroups.values()) {
      const ordered = [];
      for (let i = 1; i <= group.total; i += 1) {
        if (!group.parts.has(i)) {
          traces.push({
            well: group.well,
            success: false,
            source: "PRESSURE_TRACE_legacy",
            legacy: true,
            error: `missing PRESSURE_TRACE chunk ${i}/${group.total}`,
            observation_only: true,
            advisory: true,
            samples: [],
            csv_text: null,
          });
          ordered.length = 0;
          break;
        }
        ordered.push(group.parts.get(i));
      }
      if (ordered.length === 0) {
        continue;
      }
      try {
        const csvText = Buffer.from(ordered.join(""), "base64").toString("utf8");
        const samples = parsePressureCsv(csvText);
        traces.push({
          well: group.well,
          success: samples.length > 0,
          source: "PRESSURE_TRACE_legacy",
          legacy: true,
          observation_only: true,
          advisory: true,
          samples,
          csv_text: csvText,
          sample_count: samples.length,
        });
      } catch (error) {
        traces.push({
          well: group.well,
          success: false,
          source: "PRESSURE_TRACE_legacy",
          legacy: true,
          error: `base64 decode failed: ${error.message}`,
          observation_only: true,
          advisory: true,
          samples: [],
          csv_text: null,
        });
      }
    }
  }

  return { traces, errors, observation_only: true, advisory: true };
}

/**
 * Parse canonical or legacy pressure CSV into sample objects.
 */
export function parsePressureCsv(csvText) {
  const text = String(csvText || "").trim();
  if (!text) {
    return [];
  }
  const lines = text.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
  if (lines.length === 0) {
    return [];
  }

  const header = lines[0].split(",").map(part => part.trim().toLowerCase());
  const hasCanonical = header.includes("pressure_pa") && (header.includes("phase") || header.includes("elapsed_ms"));
  const samples = [];

  if (hasCanonical) {
    const idx = Object.fromEntries(header.map((name, i) => [name, i]));
    for (const line of lines.slice(1)) {
      if (line.startsWith("#")) {
        continue;
      }
      const parts = line.split(",").map(part => part.trim());
      const pressurePa = Number(parts[idx.pressure_pa]);
      if (!Number.isFinite(pressurePa)) {
        continue;
      }
      const elapsed = Number(parts[idx.elapsed_ms]);
      const z = Number(parts[idx.z_offset_from_top_mm]);
      const step = Number(parts[idx.step_index]);
      const cap = Number(parts[idx.capacitance_pf]);
      samples.push({
        site: parts[idx.site] || null,
        well: parts[idx.well] || null,
        phase: parts[idx.phase] || null,
        step_index: Number.isFinite(step) ? step : null,
        z_offset_from_top_mm: Number.isFinite(z) ? z : null,
        pressure_pa: pressurePa,
        capacitance_pf: Number.isFinite(cap) ? cap : null,
        elapsed_ms: Number.isFinite(elapsed) ? elapsed : null,
        // Compat alias for older analyzers
        t_ms: Number.isFinite(elapsed) ? elapsed : null,
      });
    }
    return samples;
  }

  // Legacy t_ms,pressure_pa
  for (const line of lines) {
    if (line.startsWith("#") || /^t_ms\s*,/i.test(line)) {
      continue;
    }
    const [tRaw, pRaw] = line.split(",").map(part => part.trim());
    const tMs = Number(tRaw);
    const pressurePa = Number(pRaw);
    if (!Number.isFinite(tMs) || !Number.isFinite(pressurePa)) {
      continue;
    }
    samples.push({
      phase: "legacy",
      elapsed_ms: tMs,
      t_ms: tMs,
      pressure_pa: pressurePa,
      z_offset_from_top_mm: null,
      well: null,
      site: null,
      capacitance_pf: null,
      step_index: null,
    });
  }
  return samples;
}

export function writePressureTraceCsv(trace, outputPath) {
  const dest = path.resolve(outputPath);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  let csvText = trace?.csv_text || null;
  if (!csvText && Array.isArray(trace?.samples) && trace.samples.length) {
    const hasCanonical = trace.samples.some(s => s.phase != null || s.elapsed_ms != null);
    if (hasCanonical) {
      const lines = [PRESSURE_CSV_FIELDNAMES.join(",")];
      for (const s of trace.samples) {
        lines.push(
          [
            s.site ?? "",
            s.well ?? "",
            s.phase ?? "",
            s.step_index ?? "",
            s.z_offset_from_top_mm ?? "",
            s.pressure_pa ?? "",
            s.capacitance_pf ?? "",
            s.elapsed_ms ?? s.t_ms ?? "",
          ].join(","),
        );
      }
      csvText = lines.join("\n");
    } else {
      csvText = ["t_ms,pressure_pa", ...trace.samples.map(s => `${s.t_ms},${s.pressure_pa}`)].join("\n");
    }
  }
  fs.writeFileSync(dest, `${csvText || ""}\n`, "utf8");
  return dest;
}

export function buildPressureTraceCheckPayload({
  csvPath = null,
  csvText = null,
  samples = null,
  movingAverageWindow = 5,
  resampleMs = null,
} = {}) {
  return {
    csv_path: csvPath,
    csv_text: csvText,
    samples,
    moving_average_window: movingAverageWindow,
    resample_ms: resampleMs,
  };
}

export function normalizePressureTraceProcessResult(result) {
  if (result.code !== 0) {
    const parsed = safeJsonParse(result.stdout.trim());
    if (parsed && typeof parsed === "object" && !parsed.parse_error) {
      return {
        ...parsed,
        observation_only: true,
        advisory: true,
        resume_authority: false,
        python: result.python,
        stderr: result.stderr || null,
        exit_code: result.code,
      };
    }
    return {
      summary: "pressure_trace_check Python process failed.",
      observation_only: true,
      advisory: true,
      resume_authority: false,
      needs_human_review: true,
      advisory_features: {},
      confidence_band: "low",
      error: {
        exit_code: result.code,
        stderr: result.stderr,
        stdout: result.stdout?.slice?.(0, 4000),
      },
      python: result.python,
    };
  }

  const parsed = safeJsonParse(result.stdout.trim());
  if (parsed.parse_error) {
    return {
      summary: "pressure_trace_check returned non-JSON output.",
      observation_only: true,
      advisory: true,
      resume_authority: false,
      needs_human_review: true,
      advisory_features: {},
      confidence_band: "low",
      error: parsed,
      python: result.python,
    };
  }

  return {
    ...parsed,
    observation_only: true,
    advisory: true,
    resume_authority: false,
    python: result.python,
    stderr: result.stderr || null,
  };
}

async function runPressureTracePython(payload, preferredPython) {
  const candidates = resolvePythonCandidates(preferredPython);
  let lastError = null;
  for (const candidate of candidates) {
    try {
      const result = await runCommand(candidate, [pressureCheckScriptPath], payload);
      return { ...result, python: candidate };
    } catch (error) {
      if (error.code === "ENOENT") {
        lastError = error;
        continue;
      }
      throw error;
    }
  }
  throw lastError || new Error("No usable Python interpreter found for pressure_trace_check.");
}

export async function runPressureTraceCheck({
  csvPath = null,
  csvText = null,
  samples = null,
  movingAverageWindow = 5,
  resampleMs = null,
  pythonExecutable = null,
} = {}) {
  if (!csvPath && !csvText && !samples) {
    throw new Error("analyze_pressure_trace requires csv_path, csv_text, or samples.");
  }
  if (csvPath) {
    const resolved = path.resolve(csvPath);
    if (!fs.existsSync(resolved)) {
      throw new Error(`analyze_pressure_trace: csv not found: ${resolved}`);
    }
  }

  const payload = buildPressureTraceCheckPayload({
    csvPath: csvPath ? path.resolve(csvPath) : null,
    csvText,
    samples,
    movingAverageWindow,
    resampleMs,
  });
  const result = await runPressureTracePython(payload, pythonExecutable);
  return normalizePressureTraceProcessResult(result);
}

export async function runFetchPressureCsv({
  robotIp,
  outDir = null,
  runId = null,
  limit = 12,
  nameHint = "pressure",
  prefer = "both",
  pythonExecutable = null,
} = {}) {
  if (!robotIp) {
    throw new Error("fetch_pressure_trace requires robot_ip.");
  }
  const out = outDir
    ? path.resolve(outDir)
    : path.join(DEFAULT_PRESSURE_ARTIFACT_DIR, `fetch-${Date.now()}`);
  fs.mkdirSync(out, { recursive: true });

  const args = [
    fetchPressureScriptPath,
    "--robot",
    String(robotIp),
    "--out",
    out,
    "--limit",
    String(limit),
    "--name-hint",
    String(nameHint || "pressure"),
    "--prefer",
    String(prefer || "both"),
  ];
  if (runId) {
    args.push("--run-id", String(runId));
  }

  const candidates = resolvePythonCandidates(pythonExecutable);
  let lastError = null;
  for (const candidate of candidates) {
    try {
      const result = await runCommand(candidate, args);
      const manifestPath = path.join(out, "manifest.json");
      let manifest = null;
      if (fs.existsSync(manifestPath)) {
        try {
          manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
        } catch {
          manifest = null;
        }
      }
      let primaryCsv = null;
      if (manifest?.run_traces?.length) {
        primaryCsv = manifest.run_traces.find(t => t.saved_to)?.saved_to || null;
      }
      if (!primaryCsv && manifest?.files?.length) {
        primaryCsv = manifest.files.find(f => f.saved_to)?.saved_to || null;
      }
      return {
        observation_only: true,
        advisory: true,
        resume_authority: false,
        exit_code: result.code,
        stdout: result.stdout,
        stderr: result.stderr || null,
        out_dir: out,
        csv_path: primaryCsv,
        manifest_path: fs.existsSync(manifestPath) ? manifestPath : null,
        manifest,
        python: candidate,
      };
    } catch (error) {
      if (error.code === "ENOENT") {
        lastError = error;
        continue;
      }
      throw error;
    }
  }
  throw lastError || new Error("No usable Python interpreter found for fetch_robot_pressure_csv.");
}
