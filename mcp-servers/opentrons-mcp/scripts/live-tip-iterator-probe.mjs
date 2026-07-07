#!/usr/bin/env node
/**
 * Live tip-iterator probe on Flex.
 * Usage: node scripts/live-tip-iterator-probe.mjs --robot-ip 192.168.66.102 --protocol auto|explicit
 */

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { TOOL_HANDLERS } from "../index.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "../../..");
const EXAMPLES = path.resolve(__dirname, "../examples");
const ROBOT_HTTP = path.join(REPO_ROOT, "skills/opentrons-robot-lan/scripts/opentrons_robot_api.py");

function parseArgs(argv) {
  const args = { robotIp: null, protocol: "auto", tiprackSlots: ["A2"], outDir: null };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--robot-ip") args.robotIp = argv[++i];
    else if (token === "--protocol") args.protocol = argv[++i];
    else if (token === "--tiprack-slot") args.tiprackSlots = [argv[++i]];
    else if (token === "--out-dir") args.outDir = argv[++i];
  }
  if (!args.robotIp) throw new Error("--robot-ip is required");
  return args;
}

function protocolFile(kind) {
  if (kind === "explicit") return path.join(EXAMPLES, "tip_iterator_probe_explicit.py");
  return path.join(EXAMPLES, "tip_iterator_probe_auto.py");
}

function runRobotHttp(args) {
  const result = spawnSync("python3", [ROBOT_HTTP, "--host", args.robotIp, ...args.rest], {
    encoding: "utf-8",
    maxBuffer: 20 * 1024 * 1024,
  });
  if (result.status !== 0) {
    throw new Error(`robot http failed (${args.label}): ${result.stderr || result.stdout}`);
  }
  const lines = result.stdout.trim().split("\n").filter(Boolean);
  const last = JSON.parse(lines[lines.length - 1]);
  return { stdout: result.stdout, last, all: lines.map(line => JSON.parse(line)) };
}

async function deployAndWatch(robotIp, filePath) {
  const deploy = runRobotHttp({
    robotIp,
    label: "deploy-and-run",
    rest: ["deploy-and-run", filePath],
  });
  const runId = deploy.all.find(entry => entry.run_id)?.run_id;
  if (!runId) {
    throw new Error(`deploy-and-run did not return run_id: ${deploy.stdout}`);
  }
  const watch = runRobotHttp({
    robotIp,
    label: "watch-run",
    rest: ["watch-run", runId, "--interval", "2", "--timeout", "300"],
  });
  return { runId, deploy, watch };
}

function summarizePickUpTips(commands) {
  return (commands || [])
    .filter(cmd => String(cmd?.commandType || "").toLowerCase() === "pickuptip")
    .map(cmd => ({
      id: cmd.id,
      status: cmd.status,
      intent: cmd.intent || null,
      wellName: cmd.params?.wellName || cmd.params?.well_name || null,
      errorType: cmd.error?.errorType || cmd.error?.error_type || null,
      createdAt: cmd.createdAt || cmd.created_at || null,
    }));
}

async function fetchAllCommands(robotIp, runId) {
  const pageLength = 50;
  let cursor = null;
  const all = [];
  for (let page = 0; page < 20; page += 1) {
    const result = await TOOL_HANDLERS.run_history({
      robot_ip: robotIp,
      run_id: runId,
      page_length: pageLength,
      cursor,
    });
    const commands = result?.data?.commands || [];
    all.push(...commands);
    cursor = result?.data?.cursor || null;
    if (!cursor || commands.length < pageLength) break;
  }
  return all;
}

async function runProbe({ robotIp, protocol, tiprackSlots, outDir }) {
  const filePath = protocolFile(protocol);
  const sessionId = `tip-probe-${protocol}-${Date.now()}`;
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const artifactDir = outDir || path.resolve(REPO_ROOT, `runs/tip-iterator-probe/${stamp}-${protocol}`);
  fs.mkdirSync(artifactDir, { recursive: true });

  const report = {
    robot_ip: robotIp,
    protocol_kind: protocol,
    protocol_file: filePath,
    tiprack_slots: tiprackSlots,
    session_id: sessionId,
    steps: [],
  };

  console.log(`[probe] protocol=${protocol} robot=${robotIp} tiprack=${tiprackSlots.join(",")}`);

  const { runId, deploy, watch } = await deployAndWatch(robotIp, filePath);
  report.run_id = runId;
  report.deploy = deploy.all;
  report.watch = watch.last;
  report.initial_final_status = watch.last?.final_status || watch.last?.status;
  report.steps.push({ step: "deploy_and_watch", final_status: report.initial_final_status });

  let commandsAfterRun = await fetchAllCommands(robotIp, runId);
  report.pickup_commands_after_initial_run = summarizePickUpTips(commandsAfterRun);

  if (String(report.initial_final_status).toLowerCase() !== "awaiting-recovery") {
    report.note = `Run ended with ${report.initial_final_status}; recovery path skipped.`;
    fs.writeFileSync(path.join(artifactDir, "report.json"), JSON.stringify(report, null, 2));
    console.log(JSON.stringify({ artifactDir, note: report.note, pickups: report.pickup_commands_after_initial_run }, null, 2));
    return { artifactDir, report };
  }

  const suggest = await TOOL_HANDLERS.suggest_recovery_action({
    robot_ip: robotIp,
    run_id: runId,
    session_id: sessionId,
    tiprack_slots: tiprackSlots,
  });
  report.suggest_recovery_action = suggest?.data || suggest;
  report.steps.push({ step: "suggest_recovery_action", action: suggest?.data?.recovery?.action || suggest?.data?.action });

  const recoveryAction = suggest?.data?.recovery?.action || suggest?.data?.action;
  if (recoveryAction !== "retry_pick_up_tip_with_next_candidate") {
    report.note = `Unexpected recovery action: ${recoveryAction}`;
    fs.writeFileSync(path.join(artifactDir, "report.json"), JSON.stringify(report, null, 2));
    return { artifactDir, report };
  }

  const execute = await TOOL_HANDLERS.execute_protocol_recovery({
    robot_ip: robotIp,
    run_id: runId,
    session_id: sessionId,
    tiprack_slots: tiprackSlots,
    idempotency_key: `probe-${protocol}-${Date.now()}`,
    timeout_ms: 180000,
    poll_interval_ms: 1000,
  });
  report.execute_protocol_recovery = {
    executed_action: execute?.data?.executed_action,
    executed_params: execute?.data?.executed_params,
    final_run_history_status: execute?.data?.final_run_history?.status,
    parsed_error_after: execute?.data?.parsed_error || null,
    recovery_after: execute?.data?.recovery || null,
  };
  report.steps.push({
    step: "execute_protocol_recovery",
    final_status: execute?.data?.final_run_history?.status,
    fixit_well: execute?.data?.executed_params?.well,
  });

  commandsAfterRun = await fetchAllCommands(robotIp, runId);
  report.pickup_commands_final = summarizePickUpTips(commandsAfterRun);
  report.all_commands_final = commandsAfterRun;

  const pickups = report.pickup_commands_final;
  const fixitIdx = pickups.findIndex(p => p.intent === "fixit");
  const nextAfterFixit = fixitIdx >= 0 ? pickups[fixitIdx + 1] : null;
  report.verdict = {
    fixit_well: fixitIdx >= 0 ? pickups[fixitIdx].wellName : null,
    next_pickup_well: nextAfterFixit?.wellName || null,
    next_pickup_status: nextAfterFixit?.status || null,
    double_occupancy_risk:
      fixitIdx >= 0 &&
      nextAfterFixit &&
      pickups[fixitIdx].wellName === nextAfterFixit.wellName,
  };

  fs.writeFileSync(path.join(artifactDir, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ artifactDir, verdict: report.verdict, final_status: report.execute_protocol_recovery.final_run_history_status }, null, 2));
  return { artifactDir, report };
}

const args = parseArgs(process.argv);
runProbe(args).catch(err => {
  console.error(err);
  process.exit(1);
});
