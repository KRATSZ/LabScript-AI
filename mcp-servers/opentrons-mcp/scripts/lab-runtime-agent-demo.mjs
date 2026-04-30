#!/usr/bin/env node

import fs from "fs";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";

import { TOOL_HANDLERS } from "../index.js";
import {
  buildObservedDeckState,
  getSlotOccupationSummary,
  suggestNextTipWell,
} from "../lib/decision.js";
import { ensureTiprackState } from "../lib/state.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const MCP_ROOT = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(MCP_ROOT, "../..");
const DEFAULT_ARTIFACT_ROOT = path.join(REPO_ROOT, "artifacts", "lab-runtime-demo");
const DEFAULT_ROBOT_IP = "192.168.66.103";
const VALID_SCENARIOS = new Set(["missing-tip", "occupied-destination", "liquid-sensing", "self-evolution"]);
const VALID_MODES = new Set(["mock", "live"]);

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function timestampId(now = new Date()) {
  return now.toISOString().replace(/[:.]/g, "-");
}

function readJsonIfExists(filePath, fallback) {
  if (!fs.existsSync(filePath)) {
    return clone(fallback);
  }
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return clone(fallback);
  }
}

function writeJson(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

function appendJsonl(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.appendFileSync(filePath, `${JSON.stringify(value)}\n`);
}

function defaultExperienceStore() {
  return {
    version: 1,
    updated_at: null,
    cases: [],
    policies: {
      missing_tip: {},
      liquid_sensing: {},
      occupied_destination: {},
    },
  };
}

export function loadExperienceStore(artifactRoot = DEFAULT_ARTIFACT_ROOT) {
  return readJsonIfExists(path.join(artifactRoot, "experience_store.json"), defaultExperienceStore());
}

function saveExperienceStore(artifactRoot, store) {
  const nextStore = {
    ...defaultExperienceStore(),
    ...store,
    policies: {
      ...defaultExperienceStore().policies,
      ...(store.policies || {}),
    },
    updated_at: new Date().toISOString(),
  };
  writeJson(path.join(artifactRoot, "experience_store.json"), nextStore);
  return nextStore;
}

function recordMissingTipExperience({ artifactRoot, store, tiprackSlot, failedWell, nextWell, scenario }) {
  const caseId = `${scenario || "missing-tip"}-${Date.now()}`;
  const existingPolicy = store.policies?.missing_tip?.[tiprackSlot] || {
    avoid_wells: [],
    fallback_strategy: "next_available_tip",
  };
  const avoidWells = [...new Set([...(existingPolicy.avoid_wells || []), failedWell])];

  const nextStore = {
    ...store,
    cases: [
      ...(store.cases || []),
      {
        case_id: caseId,
        scenario: scenario || "missing-tip",
        failure_type: "tip_pickup_failed",
        context: {
          tiprack_slot: tiprackSlot,
          failed_well: failedWell,
        },
        recovery: {
          action: "mark_tip_unavailable_and_try_next",
          next_well: nextWell,
          success: Boolean(nextWell),
        },
        learned_policy: {
          avoid_tip_wells: avoidWells,
          fallback_strategy: "next_available_tip",
        },
        created_at: new Date().toISOString(),
      },
    ],
    policies: {
      ...(store.policies || {}),
      missing_tip: {
        ...(store.policies?.missing_tip || {}),
        [tiprackSlot]: {
          avoid_wells: avoidWells,
          fallback_strategy: "next_available_tip",
          updated_at: new Date().toISOString(),
        },
      },
    },
  };

  return saveExperienceStore(artifactRoot, nextStore);
}

function buildSessionState({ sessionId, tiprackSlot = "C2", tiprackLoadName = "opentrons_flex_96_tiprack_1000ul" } = {}) {
  const sessionState = {
    session_id: sessionId || "lab-runtime-demo",
    state_revision: 0,
    needs_reconciliation: false,
    deck: { slots: {} },
    pipettes: {},
    tip_tracking: { tipracks: {} },
    cleanup: { pending_actions: [], auto_home_allowed: null },
  };
  ensureTiprackState(sessionState, { slotName: tiprackSlot, loadName: tiprackLoadName });
  return sessionState;
}

function applyAvoidedTipWells(sessionState, tiprackSlot, avoidWells = []) {
  const tiprack = ensureTiprackState(sessionState, { slotName: tiprackSlot });
  tiprack.missing_wells = [...new Set([...(tiprack.missing_wells || []), ...avoidWells])];
  return tiprack;
}

function buildRuntimeState({ scenario, mode, robotIp, experienceStore }) {
  return {
    scenario,
    mode,
    robot_ip: robotIp || null,
    planner_adapter: {
      name: "deterministic_policy_v1",
      model_agnostic: true,
      future_adapters: ["claude_code", "codex", "claude_agent_sdk", "sail_planner"],
    },
    compile_time: {
      execution_package: {
        protocol_py: "provided_or_generated_by_compile_time_agent",
        deck_plan_json: "desired_state.deck",
        reagent_plan_json: "desired_state.reagents",
        tip_plan_json: "desired_state.tips",
        risk_checklist_json: "risk_state",
        runbook_md: "summary.md",
      },
      simulation_gate: {
        status: "pass",
        mode,
        note: "Demo uses deterministic mock compile-time pass unless live tool execution is explicitly requested.",
      },
    },
    desired_state: {},
    committed_state: {},
    observed_state: {
      robot_api: {},
      vision: {
        status: "not_used_in_v1_demo",
        role: "evidence_only",
      },
      liquid_sensor: {},
      operator_confirmation: null,
    },
    risk_state: {
      auto_recovery_allowed: mode === "mock",
      requires_human_confirmation: mode === "live",
      hard_stop: false,
      reason: null,
    },
    experience: {
      case_count: experienceStore?.cases?.length || 0,
      policies_available: Object.keys(experienceStore?.policies || {}),
    },
    action: null,
    outcome: "not_started",
  };
}

function createArtifacts({ artifactRoot, scenario, now = new Date() }) {
  const runId = `${timestampId(now)}-${scenario}`;
  const runDir = path.join(artifactRoot, runId);
  fs.mkdirSync(runDir, { recursive: true });
  return {
    run_id: runId,
    run_dir: runDir,
    event_log_path: path.join(runDir, "event_log.jsonl"),
    state_trace_path: path.join(runDir, "state_trace.json"),
    summary_path: path.join(runDir, "summary.md"),
    experience_store_path: path.join(artifactRoot, "experience_store.json"),
  };
}

function createContext(options = {}) {
  const artifactRoot = path.resolve(options.artifactRoot || DEFAULT_ARTIFACT_ROOT);
  const experienceStore = loadExperienceStore(artifactRoot);
  const artifacts = createArtifacts({
    artifactRoot,
    scenario: options.scenario,
    now: options.now || new Date(),
  });
  const runtimeState = buildRuntimeState({
    scenario: options.scenario,
    mode: options.mode,
    robotIp: options.robotIp,
    experienceStore,
  });
  const events = [];

  function emit(phase, data = {}) {
    const event = {
      index: events.length + 1,
      timestamp: new Date().toISOString(),
      phase,
      ...data,
    };
    events.push(event);
    appendJsonl(artifacts.event_log_path, event);
    return event;
  }

  return {
    ...options,
    artifactRoot,
    artifacts,
    experienceStore,
    runtimeState,
    events,
    emit,
    toolHandlers: options.toolHandlers || TOOL_HANDLERS,
  };
}

function assertValidOptions(options) {
  if (!VALID_SCENARIOS.has(options.scenario)) {
    throw new Error(`Unsupported scenario: ${options.scenario}`);
  }
  if (!VALID_MODES.has(options.mode)) {
    throw new Error(`Unsupported mode: ${options.mode}`);
  }
  if (options.mode === "live" && !options.robotIp) {
    throw new Error("--robot-ip is required in live mode.");
  }
}

function buildSummaryMarkdown({ context, result }) {
  const state = context.runtimeState;
  const action = state.action || {};
  const lines = [
    `# LabscriptAI Runtime Agent Demo: ${state.scenario}`,
    "",
    `- Run ID: \`${context.artifacts.run_id}\``,
    `- Mode: \`${state.mode}\``,
    `- Outcome: \`${state.outcome}\``,
    `- Planner adapter: \`${state.planner_adapter.name}\``,
    `- Selected action: \`${action.name || "none"}\``,
    `- Auto executable: \`${action.auto_executable === true}\``,
    `- Requires confirmation: \`${action.requires_confirmation === true}\``,
    "",
    "## Runtime State",
    "",
    "```json",
    JSON.stringify(state, null, 2),
    "```",
    "",
    "## Event Phases",
    "",
    ...context.events.map(event => `- ${event.index}. \`${event.phase}\` - ${event.summary || event.status || "recorded"}`),
    "",
    "## Artifact Paths",
    "",
    `- Event log: \`${context.artifacts.event_log_path}\``,
    `- State trace: \`${context.artifacts.state_trace_path}\``,
    `- Experience store: \`${context.artifacts.experience_store_path}\``,
  ];

  if (result?.video_cue) {
    lines.push("", "## Video Cue", "", result.video_cue);
  }

  return `${lines.join("\n")}\n`;
}

function finishScenario(context, result = {}) {
  context.runtimeState.outcome = result.outcome || context.runtimeState.outcome || "completed";
  context.emit("recover_or_finish", {
    status: context.runtimeState.outcome,
    summary: result.summary || "Scenario finished.",
  });
  writeJson(context.artifacts.state_trace_path, {
    runtime_state: context.runtimeState,
    events: context.events,
    result,
  });
  fs.writeFileSync(context.artifacts.summary_path, buildSummaryMarkdown({ context, result }));
  return {
    ...result,
    artifacts: context.artifacts,
    runtime_state: context.runtimeState,
    events: context.events,
  };
}

async function runMissingTip(context, { writeExperience = true, scenarioName = "missing-tip" } = {}) {
  const tiprackSlot = context.tiprackSlot || "C2";
  const failedWell = context.failedWell || "A1";
  const sessionState = buildSessionState({
    sessionId: context.sessionId || "lab-runtime-demo-missing-tip",
    tiprackSlot,
    tiprackLoadName: context.tiprackLoadName || "opentrons_flex_96_tiprack_1000ul",
  });

  context.runtimeState.desired_state = {
    deck: {
      [tiprackSlot]: context.tiprackLoadName || "opentrons_flex_96_tiprack_1000ul",
    },
    tips: {
      first_choice: `${tiprackSlot}.${failedWell}`,
      fallback_strategy: "next_available_tip",
    },
    action: "pick_up_tip",
  };
  context.emit("observe", {
    summary: `Ordinary script attempts ${tiprackSlot}.${failedWell}; mock observes missing physical tip.`,
    observed_error: "tip_pickup_failed",
  });

  const nextTip = suggestNextTipWell({
    sessionState,
    tiprackSlots: [tiprackSlot],
    tiprackSlot,
    failedWell,
    failureStatus: "missing",
  });
  context.runtimeState.committed_state.tip_tracking = clone(sessionState.tip_tracking);
  context.runtimeState.observed_state.robot_api = {
    run_status: context.mode === "mock" ? "awaiting-recovery" : "unknown_until_run_id_provided",
    failed_well: `${tiprackSlot}.${failedWell}`,
  };
  context.emit("update_state", {
    summary: `${tiprackSlot}.${failedWell} marked unavailable; next candidate selected.`,
    next_candidate: nextTip.next_candidate,
  });

  const selectedAction = {
    name: "retry_pick_up_tip_with_next_candidate",
    auto_executable: true,
    requires_confirmation: context.mode === "live",
    params: {
      tiprack_slot: nextTip.next_candidate?.tiprack_slot || null,
      well: nextTip.next_candidate?.well_name || null,
      intent: "fixit",
    },
  };
  context.runtimeState.action = selectedAction;
  context.emit("choose_action", {
    summary: `Runtime selects ${selectedAction.params.tiprack_slot}.${selectedAction.params.well}.`,
    action: selectedAction,
  });

  const canExecuteLive = context.mode === "live" && context.confirmLive && context.runId;
  const gate = {
    status: context.mode === "mock" || canExecuteLive ? "pass" : "blocked",
    reason: context.mode === "live" && !canExecuteLive
      ? "live_tip_recovery_requires_confirm_live_and_run_id"
      : null,
  };
  context.runtimeState.risk_state = {
    ...context.runtimeState.risk_state,
    auto_recovery_allowed: gate.status === "pass",
    requires_human_confirmation: context.mode === "live" && !context.confirmLive,
    hard_stop: false,
    reason: gate.reason,
  };
  context.emit("verify_gate", {
    status: gate.status,
    summary: gate.reason || "Recovery action is allowed by deterministic safety policy.",
  });

  let executionResult = {
    executed: false,
    mode: context.mode,
    detail: "mocked_tip_recovery",
  };

  if (context.mode === "mock") {
    executionResult = {
      executed: true,
      mode: "mock",
      tool: "pickUpTip",
      selected_tip: selectedAction.params,
    };
  } else if (canExecuteLive) {
    executionResult = await context.toolHandlers.execute_protocol_recovery({
      robot_ip: context.robotIp,
      run_id: context.runId,
      session_id: context.sessionId || "lab-runtime-demo-missing-tip",
      tiprack_slots: [tiprackSlot],
      timeout_ms: context.timeoutMs || 30000,
      poll_interval_ms: context.pollIntervalMs || 500,
    });
  }

  context.emit("execute_tool", {
    status: executionResult.executed === false ? "skipped" : "completed",
    summary: executionResult.executed === false ? "Live execution skipped by gate." : "Tip recovery executed.",
    execution_result: executionResult,
  });

  let savedStore = context.experienceStore;
  if (writeExperience && nextTip.next_candidate?.well_name) {
    savedStore = recordMissingTipExperience({
      artifactRoot: context.artifactRoot,
      store: context.experienceStore,
      tiprackSlot,
      failedWell,
      nextWell: nextTip.next_candidate.well_name,
      scenario: scenarioName,
    });
    context.experienceStore = savedStore;
  }
  context.emit("record_trace", {
    summary: writeExperience ? "Failure and recovery saved to experience store." : "Trace recorded without writing policy.",
    experience_case_count: savedStore.cases?.length || 0,
  });

  return finishScenario(context, {
    outcome: executionResult.executed === false ? "blocked" : "recovered",
    summary: executionResult.executed === false
      ? "Missing-tip recovery was blocked before live execution."
      : "Missing-tip recovery selected a replacement tip.",
    next_tip: nextTip.next_candidate,
    execution_result: executionResult,
    experience_store: savedStore,
    video_cue:
      "Start with an ordinary script failing on C2.A1, then show the runtime marking A1 unavailable and retrying the next candidate tip.",
  });
}

async function runOccupiedDestination(context) {
  const sourceSlot = context.sourceSlot || "B3";
  const targetSlot = context.targetSlot || "C3";
  const alternativeSlot = context.destinationSlot || "B3";
  const labwareId = context.labwareId || "plate-1";
  const contextId = context.contextId || null;
  const observedDeckState = buildObservedDeckState({
    deckConfiguration: {
      data: {
        cutoutFixtures: [
          { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutB3" },
          { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutC3" },
        ],
      },
    },
    run: {
      data: {
        labware: [
          {
            id: "occupant-c3",
            loadName: "nest_96_wellplate_200ul_flat",
            location: { slotName: targetSlot },
          },
        ],
      },
    },
  });
  const sessionState = {
    session_id: context.sessionId || "lab-runtime-demo-occupied-destination",
    deck: { slots: {} },
    tip_tracking: { tipracks: {} },
    cleanup: { pending_actions: [] },
  };
  const slotOccupation = getSlotOccupationSummary({
    slotName: targetSlot,
    observedDeckState,
    sessionState,
  });

  context.runtimeState.desired_state = {
    deck: {
      [sourceSlot]: "source_labware",
      [targetSlot]: "desired_destination",
    },
    action: "move_labware",
    requested_move: {
      labware_id: labwareId,
      from_slot: sourceSlot,
      to_slot: targetSlot,
    },
  };
  context.runtimeState.observed_state.robot_api = {
    deck: observedDeckState,
    target_slot: slotOccupation,
  };
  context.emit("observe", {
    summary: `${targetSlot} is occupied before gripper move.`,
    slot_occupation: slotOccupation,
  });
  context.emit("update_state", {
    summary: "Observed occupied destination reconciled into runtime state.",
    observed_slot: targetSlot,
  });

  const selectedAction = {
    name: "move_labware_to_alternative_slot",
    auto_executable: context.mode === "mock" || Boolean(context.confirmLive && contextId),
    requires_confirmation: true,
    params: {
      labware_id: labwareId,
      occupied_slot: targetSlot,
      alternative_slot: alternativeSlot,
      strategy: "usingGripper",
    },
  };
  context.runtimeState.action = selectedAction;
  context.emit("choose_action", {
    summary: `Runtime selects gripper relocation to ${alternativeSlot}, gated by confirmation.`,
    action: selectedAction,
  });

  const gatePass = context.mode === "mock" || Boolean(context.confirmLive && contextId);
  context.runtimeState.risk_state = {
    auto_recovery_allowed: gatePass,
    requires_human_confirmation: !gatePass,
    hard_stop: false,
    reason: gatePass ? null : "gripper_move_requires_confirm_live_and_context_id",
  };
  context.emit("verify_gate", {
    status: gatePass ? "pass" : "blocked",
    summary: gatePass
      ? "Gripper relocation is allowed for this demo path."
      : "Live gripper move blocked until --confirm-live and --context-id are supplied.",
  });

  let executionResult = {
    executed: false,
    mode: context.mode,
    detail: "blocked_before_gripper_motion",
  };
  if (context.mode === "mock") {
    executionResult = {
      executed: true,
      mode: "mock",
      tool: "move_labware",
      from_slot: targetSlot,
      to_slot: alternativeSlot,
    };
  } else if (gatePass) {
    executionResult = await context.toolHandlers.move_labware({
      robot_ip: context.robotIp,
      context_type: context.contextType || "maintenance",
      context_id: contextId,
      labware_id: labwareId,
      new_slot_name: alternativeSlot,
      strategy: "usingGripper",
      intent: "fixit",
      session_id: context.sessionId || "lab-runtime-demo-occupied-destination",
      timeout_ms: context.timeoutMs || 30000,
      poll_interval_ms: context.pollIntervalMs || 500,
    });
  }
  context.emit("execute_tool", {
    status: executionResult.executed === false ? "skipped" : "completed",
    summary: executionResult.executed === false ? "Gripper motion was not executed." : "Gripper relocation branch executed.",
    execution_result: executionResult,
  });
  context.emit("record_trace", {
    summary: "Occupied-destination recovery trace recorded.",
  });

  return finishScenario(context, {
    outcome: executionResult.executed === false ? "blocked" : "recovered",
    summary: executionResult.executed === false
      ? "Occupied destination was blocked pending confirmation/context."
      : "Occupied destination was handled with a gripper relocation branch.",
    slot_occupation: slotOccupation,
    execution_result: executionResult,
    video_cue:
      "Show the target slot occupied, then show the runtime refusing blind motion and using a confirmed gripper relocation path.",
  });
}

async function runLiquidSensing(context) {
  const labwareSlot = context.labwareSlot || "B3";
  const tiprackSlot = context.tiprackSlot || "C2";
  const well = context.well || "A1";
  const mockHeight = Number(context.mockLiquidHeightMm ?? 6.2);
  context.runtimeState.desired_state = {
    deck: {
      [labwareSlot]: context.labwareLoadName || "nest_96_wellplate_200ul_flat",
      [tiprackSlot]: context.tiprackLoadName || "opentrons_flex_96_tiprack_200ul",
    },
    reagents: {
      [`${labwareSlot}.${well}`]: {
        expected: "water",
        minimum_height_mm: 1,
      },
    },
    action: "measure_liquid_height_before_aspiration",
  };
  context.emit("observe", {
    summary: `Liquid state at ${labwareSlot}.${well} is unknown before aspiration.`,
  });
  context.runtimeState.observed_state.liquid_sensor[`${labwareSlot}.${well}`] = {
    status: "unknown",
  };
  context.emit("update_state", {
    summary: "Runtime marks liquid state unknown and selects pressure-based probe.",
  });

  const selectedAction = {
    name: "probe_wells_measure_height",
    auto_executable: context.mode === "mock" || Boolean(context.confirmLive && process.env.OPENTRONS_ENABLE_PROBE_WELLS === "1"),
    requires_confirmation: context.mode === "live",
    params: {
      labware_slot: labwareSlot,
      tiprack_slot: tiprackSlot,
      well,
      mode: "measure_height",
    },
  };
  context.runtimeState.action = selectedAction;
  context.emit("choose_action", {
    summary: `Runtime selects liquid height probe for ${labwareSlot}.${well}.`,
    action: selectedAction,
  });

  const gatePass = context.mode === "mock" || selectedAction.auto_executable;
  context.runtimeState.risk_state = {
    auto_recovery_allowed: gatePass,
    requires_human_confirmation: context.mode === "live" && !context.confirmLive,
    hard_stop: false,
    reason: gatePass ? null : "live_probe_requires_confirm_live_and_OPENTRONS_ENABLE_PROBE_WELLS",
  };
  context.emit("verify_gate", {
    status: gatePass ? "pass" : "blocked",
    summary: gatePass
      ? "Liquid probe is allowed."
      : "Live probe is blocked until confirmation and OPENTRONS_ENABLE_PROBE_WELLS=1.",
  });

  let probeResult = {
    executed: false,
    mode: context.mode,
    probe_results: [],
  };
  if (context.mode === "mock") {
    probeResult = {
      executed: true,
      mode: "mock",
      probe_results: [
        {
          well,
          mode: "measure_height",
          success: true,
          value: mockHeight,
        },
      ],
    };
  } else if (gatePass) {
    probeResult = await context.toolHandlers.probe_wells({
      robot_ip: context.robotIp,
      pipette_name: context.pipetteName || "flex_1channel_1000",
      mount: context.mount || "left",
      tiprack_load_name: context.tiprackLoadName || "opentrons_flex_96_tiprack_200ul",
      tiprack_slot: tiprackSlot,
      labware_load_name: context.labwareLoadName || "nest_96_wellplate_200ul_flat",
      labware_slot: labwareSlot,
      wells: [well],
      mode: "measure_height",
      execute_on_robot: true,
      session_id: context.sessionId || "lab-runtime-demo-liquid-sensing",
    });
  }

  const measured = probeResult.probe_results?.[0] || probeResult.data?.probe_results?.[0] || null;
  if (measured) {
    const height = Number(measured.value);
    context.runtimeState.observed_state.liquid_sensor[`${labwareSlot}.${well}`] = {
      status: measured.success ? "present" : "failed",
      height_mm: Number.isFinite(height) ? height : null,
      source: "pressure_sensor",
    };
    context.runtimeState.committed_state.reagent_plan_adjustment = {
      well: `${labwareSlot}.${well}`,
      aspirate_depth_mm: Number.isFinite(height) ? Math.max(1, Number((height - 1).toFixed(2))) : null,
      policy: "measure_height_before_aspiration",
    };
  }
  context.emit("execute_tool", {
    status: probeResult.executed === false ? "skipped" : "completed",
    summary: measured ? `Measured liquid height ${measured.value} mm.` : "Liquid probe did not run.",
    probe_result: probeResult,
  });
  context.emit("record_trace", {
    summary: "Liquid sensing trace recorded.",
    liquid_state: context.runtimeState.observed_state.liquid_sensor[`${labwareSlot}.${well}`],
  });

  return finishScenario(context, {
    outcome: measured ? "replanned" : "blocked",
    summary: measured
      ? "Liquid height was measured and the aspiration plan was adjusted."
      : "Liquid probe was blocked before live execution.",
    probe_result: probeResult,
    adjusted_plan: context.runtimeState.committed_state.reagent_plan_adjustment || null,
    video_cue:
      "Show the runtime probing liquid before aspiration, then show the measured height changing the aspiration plan.",
  });
}

async function runSelfEvolution(context) {
  const tiprackSlot = context.tiprackSlot || "C2";
  const failedWell = context.failedWell || "A1";

  context.runtimeState.desired_state = {
    deck: {
      [tiprackSlot]: context.tiprackLoadName || "opentrons_flex_96_tiprack_1000ul",
    },
    action: "reuse_experience_before_tip_pickup",
  };
  context.emit("observe", {
    summary: "First episode begins without prior task-local recovery policy.",
  });

  const firstSession = buildSessionState({
    sessionId: `${context.sessionId || "lab-runtime-demo-self-evolution"}-first`,
    tiprackSlot,
  });
  const firstTip = suggestNextTipWell({
    sessionState: firstSession,
    tiprackSlots: [tiprackSlot],
    tiprackSlot,
    failedWell,
    failureStatus: "missing",
  });
  const savedStore = recordMissingTipExperience({
    artifactRoot: context.artifactRoot,
    store: context.experienceStore,
    tiprackSlot,
    failedWell,
    nextWell: firstTip.next_candidate?.well_name || null,
    scenario: "self-evolution",
  });
  context.experienceStore = savedStore;
  context.emit("update_state", {
    summary: "First episode records failure trace and writes missing-tip policy.",
    first_next_tip: firstTip.next_candidate,
  });

  const secondSession = buildSessionState({
    sessionId: `${context.sessionId || "lab-runtime-demo-self-evolution"}-second`,
    tiprackSlot,
  });
  const learnedPolicy = savedStore.policies?.missing_tip?.[tiprackSlot] || { avoid_wells: [] };
  applyAvoidedTipWells(secondSession, tiprackSlot, learnedPolicy.avoid_wells || []);
  const secondTip = suggestNextTipWell({
    sessionState: secondSession,
    tiprackSlots: [tiprackSlot],
  });
  context.runtimeState.committed_state.tip_tracking = clone(secondSession.tip_tracking);
  context.runtimeState.observed_state.robot_api = {
    first_episode: {
      failed_well: `${tiprackSlot}.${failedWell}`,
      recovered_with: firstTip.next_candidate,
    },
    second_episode: {
      avoided_wells_from_experience: learnedPolicy.avoid_wells || [],
      first_attempt_tip: secondTip.next_candidate,
    },
  };

  const selectedAction = {
    name: "retrieve_experience_and_preblock_tip",
    auto_executable: true,
    requires_confirmation: false,
    params: {
      avoid_wells: learnedPolicy.avoid_wells || [],
      selected_tip: secondTip.next_candidate,
    },
  };
  context.runtimeState.action = selectedAction;
  context.emit("choose_action", {
    summary: `Second episode starts at ${secondTip.next_candidate?.tiprack_slot}.${secondTip.next_candidate?.well_name} using learned policy.`,
    action: selectedAction,
  });
  context.emit("verify_gate", {
    status: "pass",
    summary: "Case-based policy only changes tip plan; no unsafe motion is introduced.",
  });
  context.emit("execute_tool", {
    status: "completed",
    summary: "Self-evolution demo executed in deterministic mock mode.",
  });
  context.emit("record_trace", {
    summary: "Self-evolution trace recorded.",
    experience_case_count: savedStore.cases?.length || 0,
  });

  return finishScenario(context, {
    outcome: "improved",
    summary: "Experience store changed the second episode tip plan before failure recurred.",
    first_episode: {
      failed_well: `${tiprackSlot}.${failedWell}`,
      recovered_with: firstTip.next_candidate,
    },
    second_episode: {
      avoided_wells: learnedPolicy.avoid_wells || [],
      selected_tip: secondTip.next_candidate,
    },
    experience_store: savedStore,
    video_cue:
      "Show episode 1 failing and recovering, then episode 2 starting with the learned tip plan and avoiding the failed tip well.",
  });
}

export async function runRuntimeAgentDemo(options = {}) {
  const normalized = {
    scenario: options.scenario || "missing-tip",
    mode: options.mode || "mock",
    robotIp: options.robotIp || (options.mode === "live" ? DEFAULT_ROBOT_IP : null),
    confirmLive: Boolean(options.confirmLive),
    ...options,
  };
  assertValidOptions(normalized);
  const context = createContext(normalized);
  context.emit("start", {
    summary: `Starting ${normalized.scenario} in ${normalized.mode} mode.`,
    confirm_live: normalized.confirmLive,
  });
  context.emit("compile_time", {
    summary: "Execution package loaded; simulation/preflight gate represented as deterministic pass for demo packaging.",
    execution_package: context.runtimeState.compile_time.execution_package,
    simulation_gate: context.runtimeState.compile_time.simulation_gate,
  });

  switch (normalized.scenario) {
    case "missing-tip":
      return runMissingTip(context);
    case "occupied-destination":
      return runOccupiedDestination(context);
    case "liquid-sensing":
      return runLiquidSensing(context);
    case "self-evolution":
      return runSelfEvolution(context);
    default:
      throw new Error(`Unsupported scenario: ${normalized.scenario}`);
  }
}

export function parseArgs(argv = process.argv.slice(2)) {
  const parsed = {
    scenario: "missing-tip",
    mode: "mock",
    robotIp: null,
    confirmLive: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const readValue = () => {
      index += 1;
      if (index >= argv.length) {
        throw new Error(`Missing value for ${arg}`);
      }
      return argv[index];
    };

    switch (arg) {
      case "--scenario":
        parsed.scenario = readValue();
        break;
      case "--mode":
        parsed.mode = readValue();
        break;
      case "--robot-ip":
        parsed.robotIp = readValue();
        break;
      case "--confirm-live":
        parsed.confirmLive = true;
        break;
      case "--artifact-root":
        parsed.artifactRoot = readValue();
        break;
      case "--session-id":
        parsed.sessionId = readValue();
        break;
      case "--run-id":
        parsed.runId = readValue();
        break;
      case "--context-id":
        parsed.contextId = readValue();
        break;
      case "--context-type":
        parsed.contextType = readValue();
        break;
      case "--labware-id":
        parsed.labwareId = readValue();
        break;
      case "--destination-slot":
        parsed.destinationSlot = readValue();
        break;
      case "--tiprack-slot":
        parsed.tiprackSlot = readValue();
        break;
      case "--tiprack-load-name":
        parsed.tiprackLoadName = readValue();
        break;
      case "--labware-slot":
        parsed.labwareSlot = readValue();
        break;
      case "--labware-load-name":
        parsed.labwareLoadName = readValue();
        break;
      case "--well":
        parsed.well = readValue();
        break;
      case "--mock-liquid-height-mm":
        parsed.mockLiquidHeightMm = Number(readValue());
        break;
      case "--help":
        parsed.help = true;
        break;
      default:
        throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (parsed.mode === "live" && !parsed.robotIp) {
    parsed.robotIp = DEFAULT_ROBOT_IP;
  }
  return parsed;
}

function usage() {
  return [
    "Usage:",
    "  node scripts/lab-runtime-agent-demo.mjs --scenario missing-tip --mode mock",
    "  node scripts/lab-runtime-agent-demo.mjs --scenario occupied-destination --mode mock",
    "  node scripts/lab-runtime-agent-demo.mjs --scenario liquid-sensing --mode mock",
    "  node scripts/lab-runtime-agent-demo.mjs --scenario self-evolution --mode mock",
    "",
    "Live mode requires explicit confirmation and enough context for the chosen action:",
    "  node scripts/lab-runtime-agent-demo.mjs --scenario liquid-sensing --mode live --robot-ip 192.168.66.103 --confirm-live",
    "",
    `Scenarios: ${[...VALID_SCENARIOS].join(", ")}`,
    "Modes: mock, live",
  ].join("\n");
}

async function main() {
  const args = parseArgs();
  if (args.help) {
    console.log(usage());
    return;
  }
  const result = await runRuntimeAgentDemo(args);
  console.log(JSON.stringify({
    scenario: result.runtime_state.scenario,
    mode: result.runtime_state.mode,
    outcome: result.runtime_state.outcome,
    action: result.runtime_state.action,
    artifacts: result.artifacts,
  }, null, 2));
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  main().catch(error => {
    console.error(error?.stack || error);
    process.exit(1);
  });
}
