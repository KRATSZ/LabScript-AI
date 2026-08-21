/**
 * MCP handlers for advisory pressure traces.
 *
 * Unique product path: labscriptai chat → robot(op=act, action_type=…).
 * Generate → simulate → default NOT execute. Live sampling requires
 * OPENTRONS_ENABLE_PRESSURE_TRACE=1. Never authorizes resume/play.
 */

import fs from "fs";
import path from "path";

import { ARTIFACTS_DIR } from "./paths.js";
import { buildPressureTraceProtocol, PRESSURE_PRESETS } from "./pressure-protocol.js";
import { runFetchPressureCsv, runPressureTraceCheck } from "./pressure-trace.js";
import { parseSimulationLog, runSimulationTool } from "./simulation.js";

export const PRESSURE_TRACE_ENV_FLAG = "OPENTRONS_ENABLE_PRESSURE_TRACE";
export const DEFAULT_PRESSURE_PROTOCOL_DIR = path.join(ARTIFACTS_DIR, "pressure-protocols");

function advisoryFlags() {
  return {
    observation_only: true,
    advisory: true,
    resume_authority: false,
  };
}

function withAdvisory(payload = {}) {
  const flags = advisoryFlags();
  const hasNested = payload.data && typeof payload.data === "object";
  const data = hasNested ? payload.data : payload;
  const rest = hasNested ? payload : {};
  return {
    ...rest,
    ...flags,
    data: {
      ...data,
      ...flags,
    },
  };
}

function sanitizeFilenamePart(value, fallback = "trace") {
  const normalized = String(value || fallback)
    .trim()
    .replace(/[^a-zA-Z0-9._-]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return normalized || fallback;
}

function resolvePressureProtocolOutputPath(args = {}) {
  if (args.output_path) {
    return path.resolve(String(args.output_path));
  }
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const baseName = [
    "pressure-trace",
    sanitizeFilenamePart(args.preset || "hover"),
    sanitizeFilenamePart(args.well || "A1"),
    timestamp,
  ].join("_");
  return path.join(DEFAULT_PRESSURE_PROTOCOL_DIR, `${baseName}.py`);
}

function pressureTraceLiveEnabled() {
  return process.env[PRESSURE_TRACE_ENV_FLAG] === "1";
}

function parseBool(value, fallback = false) {
  if (value === undefined || value === null) {
    return fallback;
  }
  if (typeof value === "boolean") {
    return value;
  }
  const normalized = String(value).trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) {
    return true;
  }
  if (["0", "false", "no", "off"].includes(normalized)) {
    return false;
  }
  return fallback;
}

async function simulateGeneratedProtocol(outputPath, args = {}, simulate = runSimulationTool) {
  const simulation = await simulate({
    protocol_path: outputPath,
    workspace_root: args.workspace_root,
    api_root: args.api_root,
    shared_data_root: args.shared_data_root,
    python_executable: args.python_executable,
    extra_args: args.extra_args,
    max_log_chars: args.max_log_chars ?? 12000,
  });
  const parsedSimulationOutput = parseSimulationLog({
    stdout: simulation?.stdout,
    stderr: simulation?.stderr,
    exit_code: simulation?.exit_code ?? simulation?.helper?.helper_exit_code,
    file_path: outputPath,
    protocol_path: outputPath,
  });
  return { simulation, parsedSimulationOutput };
}

export async function handleRunPressureTrace(args = {}, deps = {}) {
  const simulate = deps.simulate || runSimulationTool;
  const executeProtocol = deps.executeProtocol;
  const fetchTrace = deps.fetchTrace || handleFetchPressureTrace;
  const analyzeTrace = deps.analyzeTrace || handleAnalyzePressureTrace;

  const preset = String(args.preset || "hover").toLowerCase();
  if (!PRESSURE_PRESETS.includes(preset)) {
    throw new Error(`Unsupported pressure preset: ${args.preset}. Use one of: ${PRESSURE_PRESETS.join(", ")}`);
  }

  const outputPath = resolvePressureProtocolOutputPath(args);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  const protocolOpts = {
    preset,
    pipetteName: args.pipette_name || "flex_1channel_1000",
    mount: args.mount || "left",
    tiprackLoadName: args.tiprack_load_name || "opentrons_flex_96_tiprack_200ul",
    tiprackSlot: args.tiprack_slot || "C2",
    labwareLoadName: args.labware_load_name || "nest_96_wellplate_200ul_flat",
    labwareSlot: args.labware_slot || "B3",
    trashSlot: args.trash_slot || "A3",
    well: args.well || "A1",
    apiLevel: args.api_level || "2.24",
    robotType: args.robot_type || "Flex",
  };
  if (args.starting_tip) protocolOpts.startingTip = args.starting_tip;
  if (args.z_hover_mm != null) protocolOpts.zHoverMm = args.z_hover_mm;
  if (args.z_step_mm != null) protocolOpts.zStepMm = args.z_step_mm;
  if (args.z_max_mm != null) protocolOpts.zMaxMm = args.z_max_mm;
  if (args.move_speed != null) protocolOpts.moveSpeed = args.move_speed;
  if (args.z_speed != null) protocolOpts.zSpeed = args.z_speed;
  if (args.hover_samples != null) protocolOpts.hoverSamples = args.hover_samples;
  if (args.hover_interval_s != null) protocolOpts.hoverIntervalS = args.hover_interval_s;
  if (args.robot_csv_path) protocolOpts.robotCsvPath = args.robot_csv_path;
  const protocolText = buildPressureTraceProtocol(protocolOpts);
  fs.writeFileSync(outputPath, `${protocolText}\n`);

  const executeOnRobot = parseBool(args.execute_on_robot, false);
  if (executeOnRobot && !pressureTraceLiveEnabled()) {
    const error = new Error(
      `Live run_pressure_trace is disabled. Set ${PRESSURE_TRACE_ENV_FLAG}=1 after operator sign-off. Pressure traces remain observation-only and never authorize resume/play.`,
    );
    error.toolContext = {
      data: withAdvisory({
        data: {
          preset,
          well: String(args.well || "A1").toUpperCase(),
          generated_protocol_path: outputPath,
          execute_on_robot: false,
          rejected: true,
          live_enabled: false,
        },
      }).data,
    };
    throw error;
  }

  let simulation = null;
  let parsedSimulationOutput = null;
  try {
    ({ simulation, parsedSimulationOutput } = await simulateGeneratedProtocol(outputPath, args, simulate));
  } catch (error) {
    simulation = {
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    };
    parsedSimulationOutput = {
      success: false,
      error: simulation.error,
    };
  }

  const baseData = {
    ...advisoryFlags(),
    preset,
    well: String(args.well || "A1").toUpperCase(),
    generated_protocol_path: outputPath,
    execute_on_robot: executeOnRobot,
    simulation,
    parsed_simulation_output: parsedSimulationOutput,
    live_enabled: pressureTraceLiveEnabled(),
  };

  if (!executeOnRobot) {
    return withAdvisory({ data: baseData });
  }
  if (!parsedSimulationOutput?.success) {
    throw new Error("run_pressure_trace will not execute on the robot because local simulation did not pass.");
  }
  if (!args.robot_ip) {
    throw new Error("run_pressure_trace requires robot_ip when execute_on_robot is true.");
  }
  if (typeof executeProtocol !== "function") {
    throw new Error("run_pressure_trace live execution is not wired.");
  }

  const runResult = await executeProtocol({
    robot_ip: args.robot_ip,
    file_path: outputPath,
    timeout_ms: args.timeout_ms,
    poll_interval_ms: args.poll_interval_ms,
    page_length: args.page_length,
    session_id: args.session_id,
    workspace_root: args.workspace_root,
    api_root: args.api_root,
    shared_data_root: args.shared_data_root,
    python_executable: args.python_executable,
    extra_args: args.extra_args,
  });

  let fetchResult = null;
  let analyzeResult = null;
  const runId = runResult?.runId || runResult?.run_id || null;
  if (parseBool(args.auto_fetch, false) && args.robot_ip) {
    fetchResult = await fetchTrace({
      robot_ip: args.robot_ip,
      run_id: runId || args.run_id,
      python_executable: args.python_executable,
      out_dir: args.out_dir,
    });
  }
  if (parseBool(args.auto_analyze, false)) {
    const csvPath = fetchResult?.data?.csv_path || args.csv_path;
    if (csvPath) {
      analyzeResult = await analyzeTrace({
        csv_path: csvPath,
        python_executable: args.python_executable,
        moving_average_window: args.moving_average_window,
      });
    }
  }

  return withAdvisory({
    hardwareSnapshot: runResult?.hardwareSnapshot,
    stateRevision: runResult?.stateRevision,
    sessionId: runResult?.sessionId,
    runId,
    data: {
      ...baseData,
      run_protocol: runResult?.data || runResult || null,
      fetch_pressure_trace: fetchResult?.data || null,
      analyze_pressure_trace: analyzeResult?.data || null,
    },
  });
}

export async function handleFetchPressureTrace(args = {}) {
  const result = await runFetchPressureCsv({
    robotIp: args.robot_ip,
    outDir: args.out_dir || args.output_dir || null,
    runId: args.run_id || null,
    limit: args.limit,
    nameHint: args.name_hint,
    prefer: args.prefer,
    pythonExecutable: args.python_executable,
  });
  return withAdvisory({ data: result });
}

export async function handleAnalyzePressureTrace(args = {}) {
  const result = await runPressureTraceCheck({
    csvPath: args.csv_path || null,
    csvText: args.csv_text || null,
    samples: args.samples || null,
    movingAverageWindow: args.moving_average_window,
    resampleMs: args.resample_ms,
    pythonExecutable: args.python_executable,
  });
  return withAdvisory({ data: result });
}
