#!/usr/bin/env node

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

import { errorResponse, successResponse } from "./lib/envelope.js";
import { requestRobotBytes, requestRobotJson } from "./lib/http.js";
import {
  applyObservedDeckToSessionState,
  buildActionSummary,
  buildHomeSafetyResult,
  buildObservedDeckState,
  parseRuntimeError,
  buildReconciliationResult,
  buildRecoverySuggestion,
  classifyRecoveryError,
  getSlotOccupationSummary,
  listTipCandidates,
  listAvailableSlots,
  suggestAlternativeSlots,
  suggestNextTipWell,
} from "./lib/decision.js";
import {
  buildModuleStatusSnapshot,
  buildRobotStatusSnapshot,
  buildRunHistorySnapshot,
} from "./lib/live-state.js";
import {
  buildRunProtocolResult,
  isTerminalRunStatus,
  shouldAttachRecoveryGuidance,
} from "./lib/run-control.js";
import {
  buildCaptureImageCommand,
  buildCommandPayload,
  buildCreateRunContextRequest,
  buildContextPaths,
  buildDropTipCommand,
  buildDropTipInPlaceCommand,
  buildHeaterShakerCommand,
  buildHomeCommand,
  buildLoadLabwareCommand,
  buildLoadModuleCommand,
  buildLoadPipetteCommand,
  buildMoveLabwareCommand,
  buildMoveToAddressableAreaForDropTipCommand,
  buildMoveToMaintenancePositionCommand,
  buildOpenGripperJawCommand,
  buildTemperatureModuleCommand,
  buildThermocyclerCommand,
  deriveCleanupPendingActions,
  isHeaterShakerLatchClosed,
  isTerminalCommandStatus,
  normalizeContextType,
  shouldPreflightCloseHeaterShakerLatch,
  shouldRetryHeaterShakerAfterLatchError,
} from "./lib/execution.js";
import {
  buildProtocolRunCreateBody,
  resolveRunLabwareOffsets,
} from "./lib/labware-offsets.js";
import { parseSimulationLog, runDoctorTool, runSimulationTool } from "./lib/simulation.js";
import { buildProbeWellsProtocol, extractProbeResultsFromCommands } from "./lib/probe.js";
import * as probeLib from "./lib/probe.js";
import { applyLiquidProbeResults } from "./lib/liquid-probe-results.js";
import {
  DEFAULT_SESSION_ID,
  validateVirtualLabStateSteps,
  canOverwriteTrust,
  ensureTiprackState,
  liquidContainerKey,
  markTipWellStatus,
  mutateSessionState,
  readSessionState,
  setCleanupState,
  setLiquidContainerState,
  setLiquidSourceState,
  setPipetteState,
  uniqueSessionStrings,
} from "./lib/state.js";
import { classifyTipBindingModeDetail } from "./lib/protocol-tips.js";
import {
  appendResultLogEntry,
  readResultLogEntries,
  summarizeResultLogEntries,
} from "./lib/result-log.js";
import { buildRestartReview, buildSafeNextAction } from "./lib/restart-review.js";
import { buildPreflightRunSetupResult } from "./lib/preflight-run-setup.js";
import {
  estimateTipBudget,
  inspectLabwareDefinition,
  validateLabwareLoadName,
} from "./lib/authoring-tools.js";
import {
  buildCaptureImageParams,
  buildCameraControlBody,
  buildCameraImageSettings,
  buildCameraImageSettingsBody,
  buildCameraStatusSnapshot,
  buildPreviewArtifactName,
  contentTypeToExtension,
} from "./lib/vision.js";
import { MCP_RUNTIME_CAPABILITIES, buildHealthCheck, checkRobotHealth } from "./lib/health-check.js";
import { generateTipContinuationProtocol } from "./lib/continuation.js";
import {
  LIQUID_SOURCE_SUBSTITUTION_PLAYBOOK_ID,
  buildLiquidSourceSubstitutionPlan,
  generateLiquidSourceSubstitutionValidationProtocol,
  setSuffixSufficiencyOnPlan,
  validateLiquidSourceSubstitutionInvariants,
} from "./lib/liquid-source-substitution.js";
import { evaluateSuffixSufficiency } from "./lib/suffix-monitor.js";
import { listRecoveryPlaybooks } from "./lib/recovery-playbooks.js";
import { runVisionCheck } from "./lib/vision-check.js";
import { buildErrorTaxonomy, buildTaxonomyIssue } from "./lib/error-taxonomy.js";
import { buildLiveReadinessReport } from "./lib/live-readiness.js";
import { runRuntimeRecoveryMonitor } from "./lib/runtime-monitor.js";
import { runtimeWatchPoll } from "./lib/runtime-watch/sentry-step.js";
import { runtimeWatchLoop } from "./lib/runtime-watch/watch-loop.js";
import { ackAlert, readAlerts, readLatest } from "./lib/runtime-watch/alert-store.js";
import {
  ackRuntimeOutboxEvent,
  deliverRuntimeOutbox,
  publishMonitorNotifications,
  readRuntimeOutbox,
  runtimeOutboxPaths,
} from "./lib/runtime-outbox.js";
import {
  buildDeckPhotoAnalysisPrompt,
  buildImageDataUrl,
  buildSiliconFlowChatBody,
  callSiliconFlowChatCompletion,
  extractAssistantText,
  parseAssistantJson,
  resolveSiliconFlowApiKey,
} from "./lib/siliconflow.js";
import { analyzeImageWithArk } from "./lib/vlm-ark.js";
import { enrichRecoverySuggestion } from "./lib/recovery-routing.js";
import { listCriticalProbeTargets } from "./lib/critical-probe-targets.js";
import {
  buildDeckVisionPreflightResult,
  isPreflightVisionEnabled,
  resolveVlmProvider,
  runVlmSecondOpinion,
  shouldEscalateToVlm,
} from "./lib/deck-vision-preflight.js";
import { ARTIFACTS_DIR, DATA_DIR, PLUGIN_ROOT } from "./lib/paths.js";

const __filename = fileURLToPath(import.meta.url);
const DEFAULT_CAMERA_ARTIFACT_DIR = path.join(ARTIFACTS_DIR, "camera-captures");
const DEFAULT_VISION_ANNOTATED_DIR = path.resolve(DEFAULT_CAMERA_ARTIFACT_DIR, "vision-annotated");
const DEFAULT_PROBE_PROTOCOL_DIR = path.join(ARTIFACTS_DIR, "probe-protocols");
const PROBE_STATE_WRITEBACK_MODES = new Set(["measure_height", "require_presence", "detect_presence"]);

function resolvePendingProbeRunsDir() {
  const configured = process.env.PLUGIN_DATA || process.env.OPENTRONS_PLUGIN_DATA;
  const dataDir = configured ? path.resolve(configured) : DATA_DIR;
  return path.join(dataDir, "pending-probe-runs");
}

function sanitizePendingSessionId(sessionId = DEFAULT_SESSION_ID) {
  return String(sessionId || DEFAULT_SESSION_ID).replace(/[^a-zA-Z0-9._-]/g, "_");
}

function pendingProbeRunsPath(sessionId) {
  return path.join(resolvePendingProbeRunsDir(), `${sanitizePendingSessionId(sessionId)}.json`);
}

function readPendingProbeRuns(sessionId) {
  const filePath = pendingProbeRunsPath(sessionId);
  if (!fs.existsSync(filePath)) {
    return { runs: [] };
  }
  try {
    const parsed = JSON.parse(fs.readFileSync(filePath, "utf8"));
    return parsed && typeof parsed === "object" ? { runs: asArray(parsed.runs), ...parsed } : { runs: [] };
  } catch {
    return { runs: [] };
  }
}

function writePendingProbeRuns(sessionId, data) {
  const pendingDir = resolvePendingProbeRunsDir();
  fs.mkdirSync(pendingDir, { recursive: true });
  const filePath = pendingProbeRunsPath(sessionId);
  const tempPath = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  fs.writeFileSync(tempPath, `${JSON.stringify(data, null, 2)}\n`);
  fs.renameSync(tempPath, filePath);
}

function recordPendingProbeRun(
  sessionId,
  { runId = null, labwareSlot = null, labwareLoadName = null, mode = null, probeResults = [] } = {},
) {
  const slotName = labwareSlot ? String(labwareSlot).trim().toUpperCase() : null;
  const pending = readPendingProbeRuns(sessionId);
  const wells = asArray(probeResults)
    .map(result => ({
      slot_name: slotName,
      well_name: String(result?.well || "").trim().toUpperCase(),
      probe_result: result,
      applied: false,
    }))
    .filter(entry => entry.slot_name && entry.well_name);
  if (wells.length === 0) {
    return;
  }
  pending.runs.push({
    run_id: runId,
    recorded_at: new Date().toISOString(),
    labware_slot: slotName,
    labware_load_name: labwareLoadName || null,
    mode: mode || null,
    wells,
  });
  writePendingProbeRuns(sessionId, pending);
}

function getPendingProbeWritebackWells(sessionId) {
  const pending = readPendingProbeRuns(sessionId);
  const entries = [];
  for (const run of pending.runs || []) {
    for (const well of run.wells || []) {
      if (!well.applied) {
        entries.push({
          slot_name: well.slot_name,
          well_name: well.well_name,
          run_id: run.run_id || null,
          mode: run.mode || null,
        });
      }
    }
  }
  return entries;
}

function clearPendingProbeWell(sessionId, slotName, wellName, runId = null) {
  const normalizedSlot = String(slotName || "").trim().toUpperCase();
  const normalizedWell = String(wellName || "").trim().toUpperCase();
  const pending = readPendingProbeRuns(sessionId);
  let changed = false;
  for (const run of pending.runs || []) {
    if (runId && run.run_id !== runId) {
      continue;
    }
    for (const well of run.wells || []) {
      if (well.slot_name === normalizedSlot && well.well_name === normalizedWell && !well.applied) {
        well.applied = true;
        well.applied_at = new Date().toISOString();
        changed = true;
      }
    }
  }
  pending.runs = asArray(pending.runs).filter(run => asArray(run.wells).some(well => !well.applied));
  if (changed) {
    writePendingProbeRuns(sessionId, pending);
  }
}

function callHeightMmToVolumeUl(args = {}) {
  const fn = probeLib.heightMmToVolumeUl;
  if (typeof fn !== "function") {
    return null;
  }
  return fn(args);
}

async function writeObservedProbeResults({ sessionId, context, sources }) {
  const appliedSources = [];
  const blockedSources = [];
  let stateRevision = readSessionState(sessionId).state_revision;

  for (const source of sources) {
    const slotName = String(source.slot_name || "").trim().toUpperCase();
    const wellName = String(source.well_name || "").trim().toUpperCase();
    const containerKey = liquidContainerKey({ slotName, wellName });
    const sessionStateBefore = readSessionState(sessionId);
    const existing =
      sessionStateBefore.liquid_tracking?.containers?.[containerKey] ||
      sessionStateBefore.liquid_tracking?.sources?.[containerKey] ||
      {};
    const currentTrust = existing.trust_level || "declared";

    if (!canOverwriteTrust(currentTrust, "observed")) {
      blockedSources.push({
        container_key: containerKey,
        blocked_by: "trust_downgrade_blocked",
        trust_level: currentTrust,
      });
      continue;
    }

    let volumeUl = null;
    if (source.observed_height_mm !== null && source.observed_height_mm !== undefined) {
      const conversion = callHeightMmToVolumeUl({
        height_mm: source.observed_height_mm,
        labware_load_name: source.labware_load_name || existing.labware_load_name || context.labwareLoadName || null,
        well_name: wellName,
      });
      if (conversion) {
        volumeUl = conversion.volume_ul ?? null;
      }
    }

    const { state } = mutateSessionState(sessionId, sessionState => {
      setLiquidContainerState(sessionState, {
        slot_name: slotName,
        well_name: wellName,
        labware_load_name: source.labware_load_name || existing.labware_load_name || context.labwareLoadName || null,
        volume_ul: volumeUl,
        observed_presence: source.observed_presence ?? null,
        observed_height_mm: source.observed_height_mm ?? null,
        observed_probe_mode: source.observed_probe_mode || context.mode || null,
        trust_level: "observed",
        observed_source: source.observed_source || "live_probe",
        observed_at: source.observed_at || new Date().toISOString(),
        observed_run_id: source.observed_run_id || context.runId || null,
        notes: source.notes || null,
        role: existing.role || "source",
        why: "apply_liquid_probe_results",
      });
      return sessionState;
    });
    stateRevision = state.state_revision;
    appliedSources.push(source);
    clearPendingProbeWell(sessionId, slotName, wellName, source.observed_run_id || context.runId || null);
  }

  return {
    applied_count: appliedSources.length,
    applied_sources: appliedSources,
    blocked_sources: blockedSources,
    state_revision: stateRevision,
  };
}

function substitutionPatchForSuffixMonitor(patch = null) {
  if (!patch || typeof patch !== "object") {
    return null;
  }
  const fromKey = patch.failed_source_key || patch.from_key || patch.fromKey || null;
  const toKey = patch.replacement_source_key || patch.to_key || patch.toKey || null;
  if (!fromKey || !toKey) {
    return patch;
  }
  return {
    ...patch,
    type: patch.type || "replace_source",
    from_key: fromKey,
    to_key: toKey,
  };
}

function evaluateLiveLiquidGateSuffix({
  sessionState,
  recoverySteps = null,
  errorStepIndex = null,
  substitutionPlan = null,
} = {}) {
  const basePlan = substitutionPlan ? { ...substitutionPlan } : {
    auto_resume_eligible: false,
    suffix_sufficient: false,
    final_auto_resume_eligible: false,
    patch: null,
  };
  if (!Array.isArray(recoverySteps) || recoverySteps.length === 0) {
    const plan = setSuffixSufficiencyOnPlan(basePlan, {
      ok: false,
      suffix_sufficient: false,
      violations: [],
    });
    return {
      suffix_sufficient: false,
      blocked_reason: "suffix_steps_unavailable",
      plan,
      suffix_result: null,
      violations: [],
    };
  }
  const suffixResult = evaluateSuffixSufficiency({
    sessionState,
    steps: recoverySteps,
    errorStepIndex,
    patch: substitutionPatchForSuffixMonitor(substitutionPlan?.patch),
  });
  const plan = setSuffixSufficiencyOnPlan(basePlan, suffixResult);
  return {
    suffix_sufficient: plan.suffix_sufficient === true,
    final_auto_resume_eligible: plan.final_auto_resume_eligible === true,
    blocked_reason: plan.suffix_sufficient === true ? null : "suffix_plan_not_sufficient",
    plan,
    suffix_result: suffixResult,
    violations: suffixResult.violations || [],
  };
}

function enrichProbeResultsForWriteback({ probeResults = [], labwareSlot = null, labwareLoadName = null, mode = null } = {}) {
  const slotName = labwareSlot ? String(labwareSlot).trim().toUpperCase() : null;
  return asArray(probeResults).map(result => ({
    ...result,
    slot_name: slotName,
    labware_load_name: labwareLoadName || null,
    height_mm: mode === "measure_height" ? result?.value ?? null : null,
    observed_presence: mode === "measure_height" ? null : result?.value ?? null,
    raw_value: result?.value ?? null,
  }));
}
const DEFAULT_CONTINUATION_PROTOCOL_DIR = path.join(ARTIFACTS_DIR, "continuation-protocols");
const DEFAULT_LIQUID_SUBSTITUTION_PROTOCOL_DIR = path.join(ARTIFACTS_DIR, "liquid-substitution-protocols");
const REQUIRED_RUNTIME_TOOLS = [
  "health_check",
  "runtime_recovery_self_test",
  "runtime_recovery_monitor",
  "runtime_get_outbox",
  "runtime_ack_outbox",
  "runtime_deliver_outbox",
  "runtime_watch_loop",
  "safe_next_action",
  "restart_review",
  "validate_virtual_lab_state_steps",
  "list_recovery_playbooks",
  "live_liquid_recovery_gate",
  "robot_status",
  "module_status",
  "is_home_safe",
  "experiment_history",
  "record_liquid_source_map",
  "get_liquid_source_map",
  "summarize_liquid_source_map",
  "plan_liquid_source_substitution",
  "generate_liquid_source_substitution_protocol",
  "prepare_liquid_source_substitution_recovery",
];

function buildToolAvailabilitySummary() {
  const handlerNames = Object.keys(TOOL_HANDLERS || {});
  const present = REQUIRED_RUNTIME_TOOLS.filter(name => typeof TOOL_HANDLERS?.[name] === "function");
  const missing = REQUIRED_RUNTIME_TOOLS.filter(name => typeof TOOL_HANDLERS?.[name] !== "function");
  return {
    required: REQUIRED_RUNTIME_TOOLS,
    present,
    missing,
    all_present: missing.length === 0,
    tool_count: handlerNames.length,
  };
}

const TOOL_DEFINITIONS = [
  {
    name: "validate_labware_name",
    description: "Validate a labware load name against the local Opentrons definition index and return close matches.",
    inputSchema: {
      type: "object",
      properties: {
        load_name: { type: "string", description: "Labware load name to validate" },
        limit: { type: "integer", default: 5 },
      },
      required: ["load_name"],
    },
  },
  {
    name: "estimate_tip_budget",
    description: "Heuristically estimate tip usage and flag low-volume transfers below the recommended 10% threshold.",
    inputSchema: {
      type: "object",
      properties: {
        protocol_source: { type: "string", description: "Protocol source text to lint" },
        file_path: { type: "string", description: "Protocol file to read if protocol_source is omitted" },
        tip_rack_count: { type: "integer", description: "Override the inferred number of tip racks" },
        tip_rack_capacity: { type: "integer", default: 96 },
      },
    },
  },
  {
    name: "inspect_labware_definition",
    description: "Inspect a labware load name and return geometry, capacity, and dead-volume guidance from the local definition index.",
    inputSchema: {
      type: "object",
      properties: {
        load_name: { type: "string", description: "Labware load name to inspect" },
        limit: { type: "integer", default: 5 },
      },
      required: ["load_name"],
    },
  },
  {
    name: "robot_health",
    description: "Check robot connectivity and health via /health.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
      },
    },
  },
  {
    name: "robot_status",
    description:
      "Fetch the live hardware snapshot needed before physical actions: health, instruments, door, estop, and deck configuration.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
      },
    },
  },
  {
    name: "module_status",
    description: "Fetch attached module state and summarize which modules are ready for execution.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
      },
    },
  },
  {
    name: "get_slot_occupation",
    description: "Return whether a slot is occupied, unknown, or mismatched against committed session deck state.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        slot_name: { type: "string", description: "Target deck slot such as C2" },
        session_id: { type: "string" },
        run_id: { type: "string" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
      },
      required: ["slot_name"],
    },
  },
  {
    name: "list_available_slots",
    description: "List all available slots matching specific criteria (empty, addressable, suitable for labware/modules). Returns slots grouped by availability type.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        session_id: { type: "string" },
        run_id: { type: "string" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        filter: {
          type: "string",
          enum: ["empty", "addressable", "all"],
          description: "Filter slots by availability: 'empty' for unoccupied, 'addressable' for usable slots, 'all' for complete deck state",
        },
      },
      required: [],
    },
  },
  {
    name: "list_tip_candidates",
    description: "List remaining candidate tip wells in default search order using session bookkeeping plus current run context.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        session_id: { type: "string" },
        run_id: { type: "string" },
        tiprack_slots: {
          type: "array",
          items: { type: "string" },
        },
      },
    },
  },
  {
    name: "suggest_next_tip_well",
    description: "Suggest the next viable tip well after skipping previously failed or depleted wells.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        session_id: { type: "string" },
        run_id: { type: "string" },
        tiprack_slots: {
          type: "array",
          items: { type: "string" },
        },
        tiprack_slot: { type: "string" },
        failed_well: { type: "string" },
        failure_status: {
          type: "string",
          enum: ["missing", "depleted", "unknown-blocked"],
        },
      },
    },
  },
  {
    name: "record_liquid_source_map",
    description:
      "Record operator-confirmed liquid/sample identity and optional live probe observations for source wells in session state. This is bookkeeping only and does not move the robot.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        sources: {
          type: "array",
          items: {
            type: "object",
            properties: {
              slot_name: { type: "string", description: "Deck slot such as C3 or D3" },
              well_name: { type: "string", description: "Well name such as A1" },
              labware_load_name: { type: "string" },
              liquid_name: { type: "string" },
              sample_id: { type: "string" },
              volume_ul: { type: "number" },
              capacity_ul: { type: "number" },
              dead_volume_ul: { type: "number" },
              liquid_class: { type: "string" },
              trust_level: {
                type: "string",
                enum: ["declared", "simulated", "observed", "reconciled"],
              },
              expected_presence: { type: "boolean" },
              observed_presence: { type: "boolean" },
              observed_at: { type: "string" },
              observed_run_id: { type: "string" },
              observed_source: { type: "string" },
              expected_min_height_mm: { type: "number" },
              notes: { type: "string" },
            },
            required: ["slot_name", "well_name"],
          },
        },
      },
      required: ["sources"],
    },
  },
  {
    name: "apply_liquid_probe_results",
    description:
      "Write live probe observations into session liquid container state with trust_level=observed. Supports single-well writeback or batch apply from probe_wells artifacts. Bookkeeping only; does not move the robot. Call after probe_wells when pending_state_writeback is true.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        slot_name: { type: "string", description: "Deck slot such as D3" },
        well_name: { type: "string", description: "Well name such as A1 (single-well mode)" },
        labware_load_name: { type: "string" },
        labware_slot: { type: "string", description: "Alias for slot_name in batch mode" },
        actual_volume_ul: { type: "number", description: "Explicit observed volume in microliters" },
        height_mm: { type: "number", description: "Measured liquid height; converted via heightMmToVolumeUl when volume omitted" },
        run_id: { type: "string", description: "Probe run id for audit linkage" },
        observed_presence: { type: "boolean", description: "Presence-only observation when volume is unknown" },
        force: {
          type: "boolean",
          default: false,
          description: "Allow overwriting higher trust levels when true",
        },
        probe_results: {
          type: "array",
          description: "Batch mode: probe_wells results to apply",
          items: {
            type: "object",
            properties: {
              well: { type: "string" },
              mode: { type: "string" },
              success: { type: "boolean" },
              value: {},
            },
            required: ["well"],
          },
        },
        probe_artifact_path: {
          type: "string",
          description: "Optional JSON artifact from probe_wells live execution.",
        },
        generated_protocol_path: { type: "string" },
        mode: {
          type: "string",
          enum: ["detect_presence", "require_presence", "measure_height"],
        },
      },
    },
  },
  {
    name: "get_liquid_source_map",
    description:
      "Read operator-confirmed liquid/source identity from session state. This is bookkeeping only and does not inspect or move the robot.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        slot_name: { type: "string", description: "Optional deck slot filter such as D3" },
        well_name: { type: "string", description: "Optional well filter such as A1; requires slot_name to match a single source" },
      },
    },
  },
  {
    name: "summarize_liquid_source_map",
    description:
      "Summarize liquid source-map completeness for semantic recovery. This is read-only and does not inspect or move the robot.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        slot_name: { type: "string", description: "Optional deck slot filter such as D3" },
      },
    },
  },
  {
    name: "list_critical_probe_targets",
    description:
      "List critical source wells for preflight LPD probing (wash buffer, enzyme, etc.). Reads session liquid source map critical flags/roles; does not move the robot.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        critical_sources: {
          type: "array",
          description: "Optional explicit critical source list from intent review.",
          items: {
            type: "object",
            properties: {
              slot: { type: "string" },
              slot_name: { type: "string" },
              well: { type: "string" },
              well_name: { type: "string" },
              role: { type: "string" },
              labware_load_name: { type: "string" },
              mode: { type: "string", enum: ["detect_presence", "require_presence", "measure_height"] },
            },
          },
        },
        include_all_expected_present_fallback: {
          type: "boolean",
          default: false,
          description: "When no critical flags exist, optionally fall back to all expected_presence=true sources.",
        },
      },
    },
  },
  {
    name: "validate_virtual_lab_state_steps",
    description:
      "Run deterministic Virtual Lab State checks against proposed protocol steps before local simulation. Pure software only; it does not write session state or move the robot.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        initial_state: {
          type: "object",
          description: "Optional complete session-state object. When omitted, the saved session state is used.",
        },
        steps: {
          type: "array",
          items: {
            type: "object",
            properties: {
              id: { type: "string" },
              type: {
                type: "string",
                enum: ["declare_container", "set_container", "pick_up_tip", "drop_tip", "aspirate", "dispense", "transfer"],
              },
              container_key: { type: "string" },
              source_key: { type: "string" },
              target_key: { type: "string" },
              slot_name: { type: "string" },
              well_name: { type: "string" },
              volume_ul: { type: "number" },
              capacity_ul: { type: "number" },
              dead_volume_ul: { type: "number" },
              liquid_class: { type: "string" },
              trust_level: {
                type: "string",
                enum: ["declared", "simulated", "observed", "reconciled"],
              },
              pipette_id: { type: "string" },
              tiprack_slot: { type: "string" },
              requires_tip: { type: "boolean" },
            },
          },
        },
      },
      required: ["steps"],
    },
  },
  {
    name: "list_recovery_playbooks",
    description:
      "List registered fixed recovery playbooks, their gates, allowed watch-mode use, and semantic invariants. This is read-only.",
    inputSchema: {
      type: "object",
      properties: {
        include_motion: {
          type: "boolean",
          default: true,
          description: "When false, return only no-motion playbooks.",
        },
      },
    },
  },
  {
    name: "plan_liquid_source_substitution",
    description:
      "Plan a same-liquid source substitution from the recorded source map. This is read-only/no-motion and does not execute or resume a run.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        failed_source_key: { type: "string", description: "Source key such as D3.A1" },
        failed_slot_name: { type: "string", description: "Deck slot such as D3; used with failed_well_name" },
        failed_well_name: { type: "string", description: "Well such as A1; used with failed_slot_name" },
        preferred_source_key: { type: "string", description: "Optional replacement source key such as C3.A1" },
      },
    },
  },
  {
    name: "generate_liquid_source_substitution_protocol",
    description:
      "Generate a fixed no-aspirate validation protocol for a planned same-liquid source substitution. This writes a local protocol file only; it does not upload, run, or resume the robot.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        failed_source_key: { type: "string", description: "Source key such as D3.A1" },
        failed_slot_name: { type: "string" },
        failed_well_name: { type: "string" },
        preferred_source_key: { type: "string", description: "Optional replacement source key such as C3.A1" },
        pipette_name: { type: "string", description: "Protocol pipette name such as flex_1channel_1000" },
        mount: { type: "string", enum: ["left", "right"] },
        tiprack_load_name: { type: "string" },
        tiprack_slot: { type: "string" },
        output_path: { type: "string" },
        api_level: { type: "string", default: "2.24" },
        robot_type: { type: "string", default: "Flex" },
        tiprack_namespace: { type: "string", default: "opentrons" },
        tiprack_version: { type: "integer", default: 1 },
        labware_namespace: { type: "string", default: "opentrons" },
        labware_version: { type: "integer", default: 1 },
        trash_slot: { type: "string" },
      },
      required: ["failed_source_key", "pipette_name", "mount", "tiprack_load_name", "tiprack_slot"],
    },
  },
  {
    name: "prepare_liquid_source_substitution_recovery",
    description:
      "Prepare the registered same-liquid source-substitution recovery playbook: plan replacement, generate the fixed validation protocol, run local simulation, write an auditable bundle, and stop before any robot motion.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        failed_source_key: { type: "string", description: "Source key such as D3.A1" },
        failed_slot_name: { type: "string" },
        failed_well_name: { type: "string" },
        preferred_source_key: { type: "string", description: "Optional replacement source key such as C3.A1" },
        pipette_name: { type: "string", description: "Protocol pipette name such as flex_1channel_1000" },
        mount: { type: "string", enum: ["left", "right"] },
        tiprack_load_name: { type: "string" },
        tiprack_slot: { type: "string" },
        output_path: { type: "string", description: "Optional JSON recovery bundle path" },
        output_protocol_path: { type: "string", description: "Optional generated validation protocol path" },
        python_executable: { type: "string" },
        api_level: { type: "string", default: "2.24" },
        robot_type: { type: "string", default: "Flex" },
        tiprack_namespace: { type: "string", default: "opentrons" },
        tiprack_version: { type: "integer", default: 1 },
        labware_namespace: { type: "string", default: "opentrons" },
        labware_version: { type: "integer", default: 1 },
        trash_slot: { type: "string" },
      },
      required: ["failed_source_key", "pipette_name", "mount", "tiprack_load_name", "tiprack_slot"],
    },
  },
  {
    name: "is_home_safe",
    description: "Return whether auto-home is currently safe and which cleanup actions are still required first.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        session_id: { type: "string" },
      },
    },
  },
  {
    name: "reconcile_state",
    description: "Compare committed session deck state with live hardware and current run context, then persist a proposed reconciliation snapshot.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        session_id: { type: "string" },
        run_id: { type: "string" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        observed_liquid_containers: {
          type: "array",
          description:
            "Optional observed/reconciled liquid container snapshot to compare with session state. Pure bookkeeping; does not probe or move.",
          items: {
            type: "object",
            properties: {
              container_key: { type: "string" },
              slot_name: { type: "string" },
              well_name: { type: "string" },
              volume_ul: { type: "number" },
              capacity_ul: { type: "number" },
              dead_volume_ul: { type: "number" },
              liquid_class: { type: "string" },
              trust_level: {
                type: "string",
                enum: ["declared", "simulated", "observed", "reconciled"],
              },
            },
          },
        },
        observed_liquid_tracking: {
          type: "object",
          description: "Optional liquid_tracking-like snapshot with containers keyed by container_key.",
        },
      },
    },
  },
  {
    name: "suggest_recovery_action",
    description: "Recommend the next recovery branch from live run errors, robot/module state, and session bookkeeping.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        session_id: { type: "string" },
        run_id: { type: "string" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        error_category: { type: "string" },
        target_slot: { type: "string" },
        failed_well: { type: "string" },
        tiprack_slot: { type: "string" },
        tip_binding_mode: {
          type: "string",
          enum: ["auto", "explicit", "starting_tip"],
          description: "Optional operator-supplied tip binding mode when protocol source is unavailable.",
        },
        protocol_source: {
          type: "string",
          description: "Optional protocol source used to classify auto vs explicit tip binding.",
        },
        file_path: {
          type: "string",
          description: "Optional local protocol file path used to classify auto vs explicit tip binding.",
        },
        protocol_path: {
          type: "string",
          description: "Alias for file_path.",
        },
        tiprack_slots: {
          type: "array",
          items: { type: "string" },
        },
      },
    },
  },
  {
    name: "create_run_context",
    description:
      "Create either a protocol run context or a maintenance-run context before enqueueing commands. Automatically attaches stored labware offsets unless labware_offsets is provided.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        protocol_id: { type: "string" },
        run_time_parameters: { type: "object" },
        labware_offsets: {
          type: "array",
          items: { type: "object" },
        },
        session_id: { type: "string" },
      },
    },
  },
  {
    name: "load_pipette",
    description: "Enqueue loadPipette into a run or maintenance context and poll to terminal status.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        pipette_name: { type: "string" },
        mount: { type: "string" },
        pipette_id: { type: "string" },
        tip_overlap_not_after_version: { type: "string" },
        liquid_presence_detection: { type: "boolean" },
        intent: { type: "string" },
        key: { type: "string" },
        session_id: { type: "string" },
        timeout_ms: { type: "integer", default: 20000 },
        poll_interval_ms: { type: "integer", default: 500 },
      },
      required: ["context_id", "pipette_name", "mount"],
    },
  },
  {
    name: "load_labware",
    description: "Enqueue loadLabware into a run or maintenance context and poll to terminal status.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        slot_name: { type: "string" },
        load_name: { type: "string" },
        namespace: { type: "string" },
        version: { type: "integer" },
        labware_id: { type: "string" },
        display_name: { type: "string" },
        intent: { type: "string" },
        key: { type: "string" },
        session_id: { type: "string" },
        timeout_ms: { type: "integer", default: 20000 },
        poll_interval_ms: { type: "integer", default: 500 },
      },
      required: ["context_id", "slot_name", "load_name", "namespace", "version"],
    },
  },
  {
    name: "load_module",
    description: "Enqueue loadModule into a run or maintenance context and poll to terminal status.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        module_model: { type: "string" },
        slot_name: { type: "string" },
        module_id: { type: "string" },
        intent: { type: "string" },
        key: { type: "string" },
        session_id: { type: "string" },
        timeout_ms: { type: "integer", default: 20000 },
        poll_interval_ms: { type: "integer", default: 500 },
      },
      required: ["context_id", "module_model", "slot_name"],
    },
  },
  {
    name: "control_temperature_module",
    description: "Control a Temperature Module in an active run or maintenance context.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        module_id: { type: "string" },
        action: {
          type: "string",
          enum: ["set_target_temperature", "wait_for_temperature", "deactivate"],
        },
        celsius: { type: "number" },
        intent: { type: "string" },
        key: { type: "string" },
        session_id: { type: "string" },
        timeout_ms: { type: "integer", default: 120000 },
        poll_interval_ms: { type: "integer", default: 500 },
      },
      required: ["context_id", "module_id", "action"],
    },
  },
  {
    name: "control_heater_shaker",
    description: "Control Heater-Shaker temperature, shaker speed, or latch in an active context.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        module_id: { type: "string" },
        action: {
          type: "string",
          enum: [
            "set_target_temperature",
            "wait_for_temperature",
            "deactivate_heater",
            "set_shake_speed",
            "set_and_wait_for_shake_speed",
            "deactivate_shaker",
            "open_labware_latch",
            "close_labware_latch",
          ],
        },
        celsius: { type: "number" },
        rpm: { type: "number" },
        ensure_latch_closed: {
          type: "boolean",
          default: true,
          description:
            "When action is deactivate_shaker, explicitly satisfy the latch-closed precondition before or after a latch-related failure.",
        },
        intent: { type: "string" },
        key: { type: "string" },
        session_id: { type: "string" },
        timeout_ms: { type: "integer", default: 120000 },
        poll_interval_ms: { type: "integer", default: 500 },
      },
      required: ["context_id", "module_id", "action"],
    },
  },
  {
    name: "control_thermocycler",
    description: "Control Thermocycler block/lid temperature or lid state in an active context.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        module_id: { type: "string" },
        action: {
          type: "string",
          enum: [
            "set_block_temperature",
            "wait_for_block_temperature",
            "set_lid_temperature",
            "wait_for_lid_temperature",
            "deactivate_block",
            "deactivate_lid",
            "open_lid",
            "close_lid",
            "run_profile",
          ],
        },
        celsius: { type: "number" },
        hold_time_seconds: { type: "number" },
        block_max_volume_ul: { type: "number" },
        ramp_rate: { type: "number" },
        profile: { type: "array", items: { type: "object" } },
        intent: { type: "string" },
        key: { type: "string" },
        session_id: { type: "string" },
        timeout_ms: { type: "integer", default: 120000 },
        poll_interval_ms: { type: "integer", default: 500 },
      },
      required: ["context_id", "module_id", "action"],
    },
  },
  {
    name: "move_labware",
    description: "Enqueue moveLabware with gripper strategy and poll to terminal status.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        labware_id: { type: "string" },
        new_slot_name: { type: "string" },
        strategy: { type: "string" },
        pick_up_offset: { type: "object" },
        drop_offset: { type: "object" },
        intent: { type: "string" },
        key: { type: "string" },
        session_id: { type: "string" },
        timeout_ms: { type: "integer", default: 30000 },
        poll_interval_ms: { type: "integer", default: 500 },
      },
      required: ["context_id", "labware_id", "new_slot_name"],
    },
  },
  {
    name: "cleanup_motion",
    description: "Execute openGripperJaw, moveToMaintenancePosition, and conditional home in a maintenance context.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        context_id: { type: "string" },
        mount: { type: "string", default: "extension" },
        maintenance_position: { type: "string" },
        allow_home: { type: "boolean", default: true },
        home_axes: {
          type: "array",
          items: { type: "string" },
        },
        session_id: { type: "string" },
        timeout_ms: { type: "integer", default: 30000 },
        poll_interval_ms: { type: "integer", default: 500 },
      },
      required: ["context_id"],
    },
  },
  {
    name: "drop_attached_tip",
    description:
      "Safely drop an already attached pipette tip in a maintenance context after a stopped or recovery run. Refuses when robot_status does not confirm a tip on the requested mount. Defaults to trash-centered drop (alternate_drop_location=false) to avoid offsetting outside the chute.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        context_id: { type: "string" },
        mount: { type: "string", enum: ["left", "right"], default: "left" },
        pipette_name: { type: "string" },
        pipette_id: { type: "string" },
        labware_id: { type: "string" },
        well_name: { type: "string" },
        alternate_drop_location: {
          type: "boolean",
          default: false,
          description:
            "When true, offset XY from trash center (higher collision risk). Default false = trash-centered drop.",
        },
        session_id: { type: "string" },
        timeout_ms: { type: "integer", default: 30000 },
        poll_interval_ms: { type: "integer", default: 500 },
      },
      required: ["context_id"],
    },
  },
  {
    name: "camera_status",
    description: "Read built-in camera enablement and livestream state from the robot.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
      },
    },
  },
  {
    name: "configure_camera",
    description:
      "Enable or tune the built-in camera. Supports /camera booleans and optional /camera/cameraSettings image parameters.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        camera_enabled: { type: "boolean" },
        live_stream_enabled: { type: "boolean" },
        error_recovery_camera_enabled: { type: "boolean" },
        camera_id: { type: "string" },
        resolution_width: { type: "integer" },
        resolution_height: { type: "integer" },
        zoom: { type: "number" },
        contrast: { type: "number" },
        brightness: { type: "number" },
        saturation: { type: "number" },
        pan_x: { type: "number" },
        pan_y: { type: "number" },
      },
    },
  },
  {
    name: "capture_preview_image",
    description:
      "Capture a robot preview image, save it locally, and return the artifact path for later human or model analysis.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        output_path: { type: "string", description: "Optional explicit file path for the saved image" },
        camera_id: { type: "string" },
        resolution_width: { type: "integer" },
        resolution_height: { type: "integer" },
        zoom: { type: "number" },
        contrast: { type: "number" },
        brightness: { type: "number" },
        saturation: { type: "number" },
        pan_x: { type: "number" },
        pan_y: { type: "number" },
      },
    },
  },
  {
    name: "capture_run_image",
    description:
      "Capture an image through the robot command queue, download the resulting data file, and save it locally.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        output_path: { type: "string" },
        file_name: { type: "string" },
        resolution_width: { type: "integer" },
        resolution_height: { type: "integer" },
        zoom: { type: "number" },
        contrast: { type: "number" },
        brightness: { type: "number" },
        saturation: { type: "number" },
        pan_x: { type: "number" },
        pan_y: { type: "number" },
        intent: { type: "string" },
        key: { type: "string" },
        timeout_ms: { type: "integer", default: 30000 },
        poll_interval_ms: { type: "integer", default: 500 },
      },
      required: ["context_id"],
    },
  },
  {
    name: "list_data_files",
    description: "List generated or uploaded data files available on the robot, including historical camera images.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
      },
    },
  },
  {
    name: "download_data_file",
    description: "Download a robot data file by id and save it locally.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        data_file_id: { type: "string" },
        output_path: { type: "string" },
      },
      required: ["data_file_id"],
    },
  },
  {
    name: "analyze_image_with_kimi",
    description:
      "Analyze a local robot image with SiliconFlow Kimi-K2.5 or another multimodal model using OpenAI-compatible chat completions.",
    inputSchema: {
      type: "object",
      properties: {
        image_path: { type: "string" },
        api_key: { type: "string" },
        base_url: { type: "string" },
        model: { type: "string" },
        prompt: { type: "string" },
        system_prompt: { type: "string" },
        detail: {
          type: "string",
          enum: ["auto", "low", "high"],
        },
        temperature: { type: "number" },
        max_tokens: { type: "integer" },
        expected_layout: { type: "object" },
      },
      required: ["image_path"],
    },
  },
  {
    name: "analyze_image_with_ark",
    description:
      "Analyze a local robot deck image with Volcengine Ark (Doubao VLM) using the Responses API. Observation-only; does not mutate session state. Default model endpoint from ARK_MODEL_ENDPOINT or ep-20260716144817-n6rgn; API key from ARK_API_KEY or automation/.env.",
    inputSchema: {
      type: "object",
      properties: {
        image_path: { type: "string" },
        api_key: { type: "string" },
        base_url: { type: "string" },
        model_endpoint: { type: "string" },
        prompt: { type: "string" },
        expected_layout: { type: "object" },
        max_output_tokens: { type: "integer" },
      },
      required: ["image_path"],
    },
  },
  {
    name: "vision_check",
    description:
      "Local YOLOE/YOLO vision observation for CHECKDECK or CHECKTIPS (observation-only; does not mutate session state). Uses ultralytics in the project Python env. CHECKDECK maps detections to Flex 12 slots using optional deck homography (deck_corners_norm or labels sidecar optional_deck_corners_norm) or a uniform image-grid fallback; empty slots are geometric (no detection in cell). Default YOLOE prompts are Flex-tuned (colored tip racks, modules, trash). Override with class_prompts + canonical_labels. CHECKTIPS is stubbed pending rack-local analysis.",
    inputSchema: {
      type: "object",
      properties: {
        mode: {
          type: "string",
          enum: ["deck", "tiprack"],
          description: "deck = slot-level observation; tiprack = reserved / conservative stub",
        },
        image_path: {
          type: "string",
          description: "Absolute or workspace path to a saved camera image",
        },
        expected_layout: {
          type: "object",
          description:
            'Optional map of slot -> expected label (canonical: tiprack, plate, reservoir, module, trash_bin) or "empty". Example: {"C2":"tiprack","A1":"empty"}',
        },
        reference_image_path: {
          type: "string",
          description: "Optional reference image for future visual-prompt tiprack flows (not used in MVP deck mode).",
        },
        conf_threshold: {
          type: "number",
          description: "Minimum detection confidence (default 0.25)",
          default: 0.25,
        },
        use_text_prompts: {
          type: "boolean",
          description:
            "If true, use YOLOE text prompts (requires CLIP). If false, use a plain YOLO checkpoint without set_classes. Default: auto from weights (yoloe = true).",
        },
        weights: {
          type: "string",
          description:
            "Ultralytics checkpoint path or name. Omit to auto-pick: OPENTRONS_DECK_YOLO_WEIGHTS, then vision/models/weights deck_v2/deck_pilot, then local vision/runs, then OPENTRONS_YOLOE_WEIGHTS / yoloe-26s-seg.pt",
        },
        annotated_output_dir: {
          type: "string",
          description: "Directory to save annotated debug image (default under artifacts/camera-captures/vision-annotated)",
        },
        python_executable: {
          type: "string",
          description: "Override Python for ultralytics (else OPENTRONS_PYTHON / .venv)",
        },
        deck_corners_norm: {
          type: "array",
          description:
            "Optional 4-corner deck homography in normalized image coordinates [[x,y], ...] to map detections to slots.",
          items: {
            type: "array",
            items: { type: "number" },
          },
        },
        load_labels_sidecar: {
          type: "boolean",
          description:
            "If true, also try labels/<stem>.labels.json for optional_deck_corners_norm, class_prompts, and canonical_labels.",
        },
        class_prompts: {
          type: "array",
          description: "Optional YOLOE text prompts to bias detection classes.",
          items: { type: "string" },
        },
        canonical_labels: {
          type: "array",
          description: "Optional canonical label set used to normalize detections.",
          items: { type: "string" },
        },
      },
      required: ["image_path"],
    },
  },
  {
    name: "deck_vision_check",
    description:
      "Preflight deck vision orchestration: capture_preview_image → vision_check (YOLO first) → optional Ark VLM second opinion when uncertain or mismatched. Observation-only; compare with reconcile_state before treating as deck truth. Set OPENTRONS_PREFLIGHT_VISION=off to skip.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        session_id: { type: "string" },
        expected_layout: { type: "object" },
        output_path: { type: "string" },
        force_vlm: { type: "boolean", default: false },
        vlm_provider: { type: "string", enum: ["ark", "kimi", "off"] },
        conf_threshold: { type: "number" },
        weights: { type: "string" },
      },
      required: ["robot_ip"],
    },
  },
  {
    name: "get_protocols",
    description: "List protocols stored on the robot.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
      },
    },
  },
  {
    name: "upload_protocol",
    description: "Upload a local protocol file to the robot.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        file_path: { type: "string", description: "Path to protocol file" },
        protocol_kind: {
          type: "string",
          enum: ["standard", "quick-transfer"],
        },
        key: { type: "string" },
        run_time_parameters: { type: "object" },
      },
      required: ["file_path"],
    },
  },
  {
    name: "run_protocol",
    description:
      "Upload a protocol, create a run (auto-attaching stored labware offsets), optionally play it, then poll until the run reaches a terminal or intervention-required state.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        file_path: { type: "string", description: "Path to protocol file" },
        protocol_kind: {
          type: "string",
          enum: ["standard", "quick-transfer"],
        },
        key: { type: "string" },
        run_time_parameters: { type: "object" },
        labware_offsets: {
          type: "array",
          items: { type: "object" },
          description:
            "Optional explicit offsets. When omitted, fetches and dedupes stored robot offsets.",
        },
        auto_play: { type: "boolean", default: true },
        timeout_ms: { type: "integer", default: 1800000 },
        poll_interval_ms: { type: "integer", default: 1000 },
        page_length: { type: "integer", default: 20 },
        session_id: { type: "string" },
        skip_preflight: {
          type: "boolean",
          description: "If true, skip the post-run preflight gate and proceed directly to play.",
        },
        skip_preflight_deck_diff: {
          type: "boolean",
          description: "If true, keep reconciliation and readiness checks but skip the declared-load deck diff.",
        },
        strict_preflight_labware_slots: {
          type: "boolean",
          description: "If true, treat empty observed labware slots as errors during preflight.",
        },
        tiprack_slots: {
          type: "array",
          items: { type: "string" },
        },
      },
      required: ["file_path"],
    },
  },
  {
    name: "probe_wells",
    description:
      "Experimental liquid probing helper that generates a temporary protocol, simulates it locally, and can be explicitly enabled for live robot execution later.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL. Required only for live execution." },
        pipette_name: { type: "string", description: "Flex pipette load name such as flex_1channel_1000" },
        mount: { type: "string", enum: ["left", "right"] },
        tiprack_load_name: { type: "string" },
        tiprack_slot: { type: "string" },
        starting_tip: { type: "string", description: "Optional first tip well, such as A2, to avoid reusing tips across probe runs." },
        labware_load_name: { type: "string" },
        labware_slot: { type: "string" },
        trash_slot: { type: "string" },
        wells: {
          type: "array",
          items: { type: "string" },
        },
        mode: {
          type: "string",
          enum: ["detect_presence", "require_presence", "measure_height"],
          default: "detect_presence",
        },
        api_level: { type: "string", default: "2.24" },
        liquid_presence_detection: { type: "boolean", default: true },
        auto_apply_to_session: {
          type: "boolean",
          default: false,
          description:
            "When execute_on_robot is true, write probe_results into session liquid_tracking via apply_liquid_probe_results.",
        },
        execute_on_robot: { type: "boolean", default: false },
        output_path: { type: "string" },
        timeout_ms: { type: "integer", default: 1800000 },
        poll_interval_ms: { type: "integer", default: 1000 },
        page_length: { type: "integer", default: 50 },
        session_id: { type: "string" },
        workspace_root: { type: "string" },
        api_root: { type: "string" },
        shared_data_root: { type: "string" },
        python_executable: { type: "string" },
        extra_args: {
          type: "array",
          items: { type: "string" },
        },
      },
      required: [
        "pipette_name",
        "mount",
        "tiprack_load_name",
        "tiprack_slot",
        "labware_load_name",
        "labware_slot",
        "wells",
      ],
    },
  },
  {
    name: "create_run",
    description:
      "Create a run for a protocol already on the robot. Automatically attaches stored labware offsets from the robot unless labware_offsets is provided.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        protocol_id: { type: "string", description: "Uploaded protocol ID" },
        run_time_parameters: { type: "object" },
        labware_offsets: {
          type: "array",
          items: { type: "object" },
          description:
            "Optional explicit offsets. When omitted, fetches and dedupes stored robot offsets.",
        },
        page_length: { type: "integer", default: 10 },
      },
      required: ["protocol_id"],
    },
  },
  {
    name: "control_run",
    description: "Play, pause, stop, or resume-from-recovery for a run.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        run_id: { type: "string" },
        action: {
          type: "string",
          enum: ["play", "pause", "stop", "resume-from-recovery"],
        },
        page_length: { type: "integer", default: 10 },
        session_id: { type: "string" },
        tiprack_slots: {
          type: "array",
          items: { type: "string" },
        },
      },
      required: ["run_id", "action"],
    },
  },
  {
    name: "generate_continuation_protocol",
    description:
      "Generate a new tip-only continuation protocol from an awaiting-recovery run. This writes a local protocol file but does not stop, play, or move the robot.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        run_id: { type: "string", description: "Source run id in awaiting-recovery or failed state" },
        session_id: { type: "string" },
        output_path: { type: "string", description: "Optional explicit output .py path" },
        page_length: { type: "integer", default: 200 },
        protocol_name: { type: "string" },
        use_session_state: {
          type: "boolean",
          default: false,
          description:
            "When true, merge persisted session tip bookkeeping into the preview. Default false trusts live run command history only.",
        },
      },
      required: ["robot_ip", "run_id"],
    },
  },
  {
    name: "execute_protocol_recovery",
    description:
      "Execute a supported protocol recovery branch from live recovery guidance, then resume the run when appropriate.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        run_id: { type: "string" },
        session_id: { type: "string" },
        expected_action: { type: "string" },
        tiprack_slots: {
          type: "array",
          items: { type: "string" },
        },
        recovery_well: { type: "string" },
        tiprack_slot: { type: "string" },
        tip_binding_mode: {
          type: "string",
          enum: ["auto", "explicit", "starting_tip"],
        },
        protocol_source: { type: "string" },
        file_path: { type: "string" },
        protocol_path: { type: "string" },
        destination_slot: { type: "string" },
        allow_low_confidence_destination: { type: "boolean", default: false },
        module_wait_timeout_ms: { type: "integer", default: 120000 },
        module_poll_interval_ms: { type: "integer", default: 1000 },
        timeout_ms: { type: "integer", default: 120000 },
        poll_interval_ms: { type: "integer", default: 500 },
        page_length: { type: "integer", default: 20 },
      },
      required: ["run_id"],
    },
  },
  {
    name: "runtime_watch_poll",
    description:
      "Bounded runtime watch poll for a live protocol run. Polls run status, executes only narrow L0 self-fix branches, and returns only running/completed/needs_user/hard_stop/unreachable.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        run_id: { type: "string" },
        session_id: { type: "string" },
        max_block_ms: { type: "integer", default: 50000 },
        poll_interval_ms: { type: "integer", default: 3000 },
        timeout_ms: { type: "integer" },
        page_length: { type: "integer", default: 20 },
        tiprack_slots: {
          type: "array",
          items: { type: "string" },
        },
        tip_binding_mode: {
          type: "string",
          enum: ["auto", "explicit", "starting_tip"],
        },
        protocol_source: { type: "string" },
        file_path: { type: "string" },
        protocol_path: { type: "string" },
        module_wait_timeout_ms: { type: "integer" },
        module_poll_interval_ms: { type: "integer", default: 1000 },
        max_attempts_per_failed_command: { type: "integer", default: 3 },
        unreachable_threshold: { type: "integer", default: 2 },
      },
      required: ["run_id"],
    },
  },
  {
    name: "runtime_watch_loop",
    description:
      "Auto-wake runtime watch loop: reuses runtime_watch_poll on a budgeted schedule (max_turns / max_runtime_ms / interval_ms) and emits one outbox sentinel per tick for host-adapter wake (claudecode/cursor/codex/cli/webhook). Persists a goal-state.json per run (resume=true continues an active goal). Goal status is COMPLETE/BLOCKED/BUDGET_LIMITED; COMPLETE requires either a completed tick or a verify callback. Safety model is inherited from runtime_watch_poll: only L0 whitelist fixes auto-execute; needs_user/hard_stop stop the loop and emit a BLOCKED sentinel. Default self_fix_mode=observe (no robot motion).",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        run_id: { type: "string" },
        session_id: { type: "string" },
        goal_id: { type: "string", description: "Optional explicit goal id; reused with resume=true." },
        goal_prompt: { type: "string", description: "Operator goal text recorded in goal-state for handoff/audit." },
        max_turns: { type: "integer", default: 20 },
        max_runtime_ms: { type: "integer", default: 600000 },
        interval_ms: { type: "integer", default: 5000 },
        max_block_ms: { type: "integer", default: 30000 },
        poll_interval_ms: { type: "integer", default: 3000 },
        page_length: { type: "integer", default: 20 },
        tiprack_slots: { type: "array", items: { type: "string" } },
        tip_binding_mode: { type: "string", enum: ["auto", "explicit", "starting_tip"] },
        protocol_source: { type: "string" },
        file_path: { type: "string" },
        protocol_path: { type: "string" },
        module_wait_timeout_ms: { type: "integer" },
        module_poll_interval_ms: { type: "integer", default: 1000 },
        max_attempts_per_failed_command: { type: "integer", default: 3 },
        unreachable_threshold: { type: "integer", default: 2 },
        resume: { type: "boolean", default: false },
        self_fix_mode: { type: "string", enum: ["observe", "l0"], default: "observe" },
        allow_l4_execution: { type: "boolean", default: false },
        operator_opt_in: { type: "boolean", default: false },
        watch_dir: { type: "string" },
        outbox_dir: { type: "string" },
        notify_adapters: {
          type: "array",
          items: {
            type: "string",
            enum: ["claudecode", "claude", "codex", "cursor", "piagent", "opencode", "cli", "webhook"],
          },
          description: "Adapters to deliver pending outbox sentinels to after the loop ends.",
        },
        notify_limit: { type: "integer", default: 20 },
        host_adapter_dir: { type: "string" },
        webhook_url: { type: "string" },
        zero_llm_when_no_error: {
          type: "boolean",
          default: false,
          description:
            "When true, suppress LLM guidance on ticks with no actionable error. Defaults from OPENTRONS_ZERO_LLM_WHEN_NO_ERROR when omitted.",
        },
      },
      required: ["run_id"],
    },
  },
  {
    name: "runtime_get_alerts",
    description:
      "Read runtime watch and monitor alerts plus latest watch state. Intended for hook/insurance paths and current-dialog notification checks.",
    inputSchema: {
      type: "object",
      properties: {
        run_id: { type: "string" },
        session_id: { type: "string" },
        limit: { type: "integer", default: 20 },
        include_acked: { type: "boolean", default: false },
        watch_dir: { type: "string" },
      },
    },
  },
  {
    name: "runtime_ack_alert",
    description: "Mark a runtime watch alert handled after the operator has supplied the requested decision.",
    inputSchema: {
      type: "object",
      properties: {
        run_id: { type: "string" },
        alert_id: { type: "string" },
        note: { type: "string" },
        selection: { type: ["string", "object", "null"] },
        watch_dir: { type: "string" },
      },
      required: ["run_id", "alert_id"],
    },
  },
  {
    name: "runtime_get_outbox",
    description:
      "Read pending runtime notification outbox events created from watcher/monitor alerts for host adapters.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        run_id: { type: "string" },
        limit: { type: "integer", default: 20 },
        include_acked: { type: "boolean", default: false },
        include_delivered: { type: "boolean", default: true },
        outbox_dir: { type: "string" },
        host_adapter_dir: { type: "string" },
      },
    },
  },
  {
    name: "runtime_ack_outbox",
    description:
      "Mark a runtime notification outbox event handled after the operator or host adapter has acted on it.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        outbox_id: { type: "string" },
        note: { type: "string" },
        selection: { type: ["string", "object", "null"] },
        outbox_dir: { type: "string" },
      },
      required: ["outbox_id"],
    },
  },
  {
    name: "runtime_deliver_outbox",
    description:
      "Deliver pending runtime outbox events to configured host adapters: claudecode, codex, cursor, piagent, opencode, cli, or webhook.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        run_id: { type: "string" },
        adapters: {
          type: "array",
          items: {
            type: "string",
            enum: ["claudecode", "codex", "cursor", "piagent", "opencode", "cli", "webhook"],
          },
        },
        limit: { type: "integer", default: 20 },
        include_delivered: { type: "boolean", default: false },
        outbox_dir: { type: "string" },
        host_adapter_dir: { type: "string" },
        webhook_url: { type: "string" },
      },
    },
  },
  {
    name: "recover_tip_pickup",
    description:
      "In protocol recovery state, enqueue a fixit pickUpTip on the next viable well and resume the run.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        run_id: { type: "string" },
        session_id: { type: "string" },
        tiprack_slots: {
          type: "array",
          items: { type: "string" },
        },
        recovery_well: { type: "string" },
        tiprack_slot: { type: "string" },
        timeout_ms: { type: "integer", default: 120000 },
        poll_interval_ms: { type: "integer", default: 500 },
        page_length: { type: "integer", default: 20 },
      },
      required: ["run_id"],
    },
  },
  {
    name: "get_runs",
    description: "List runs on the robot.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
      },
    },
  },
  {
    name: "run_history",
    description: "Get run state plus recent command history in an agent-friendly format.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        run_id: { type: "string" },
        page_length: { type: "integer", default: 10 },
      },
      required: ["run_id"],
    },
  },
  {
    name: "experiment_history",
    description: "Query persisted run, recovery, and reconciliation result logs for recent experiment history.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        run_id: { type: "string" },
        tool_name: { type: "string" },
        event_kind: { type: "string" },
        status: { type: "string" },
        limit: { type: "integer", default: 20 },
      },
    },
  },
  {
    name: "restart_review",
    description:
      "After MCP or host restart: summarize persisted session state plus recent result logs with structured guidance. suggested_tool_order includes run_history and parse_error when session last_run_id is set. Logs are historical only; pass robot_ip optionally to include a live is_home_safe preview (narrative warns if auto-home is blocked).",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        limit: { type: "integer", default: 20 },
        robot_ip: {
          type: "string",
          description: "Optional; when set, fetches robot_status to preview home safety alongside session state",
        },
      },
    },
  },
  {
    name: "safe_next_action",
    description:
      "Single-entry operator summary after MCP/host restart: same payload as restart_review plus safe_next_action (recommended_next_tool, operator_steps, tool_sequence). Prefer this when the user wants one call instead of reading the full guidance object. Atomic tools are unchanged.",
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string" },
        limit: { type: "integer", default: 20 },
        robot_ip: {
          type: "string",
          description: "Optional; when set, fetches robot_status for home-safety preview (same as restart_review)",
        },
      },
    },
  },
  {
    name: "runtime_recovery_monitor",
    description:
      "Active L1-L4 runtime recovery monitor tick. L1 checks runtime/robot/module health, L2 watches a run, L3 coordinates recovery gates and safe-next guidance, and L4 only delegates whitelisted L0 self-fixes when explicitly enabled.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        session_id: { type: "string" },
        run_id: { type: "string" },
        levels: {
          type: "array",
          items: {
            type: "string",
            enum: ["L1", "L2", "L3", "L4"],
          },
          description: "Optional subset of monitor levels. Default runs L1-L4.",
        },
        self_fix_mode: {
          type: "string",
          enum: ["observe", "l0"],
          default: "observe",
          description:
            "observe is read-only for run watching. l0 delegates only whitelisted L0 fixes to runtime_watch_poll.",
        },
        allow_l4_execution: {
          type: "boolean",
          default: false,
          description:
            "Required, together with operator_opt_in and self_fix_mode=l0, before L4 treats L0 self-fix execution as allowed.",
        },
        operator_opt_in: {
          type: "boolean",
          default: false,
          description: "Explicit operator opt-in for the guarded execution layer.",
        },
        source_plan: {
          type: "string",
          enum: ["c3_d3_liquid_recovery"],
          description:
            "Optional liquid gate source plan. c3_d3_liquid_recovery expands to C3.A1 present, D3.A1-H1 present, and D3.A12 absent.",
        },
        required_sources: {
          type: "array",
          items: {
            type: "object",
            properties: {
              slot_name: { type: "string" },
              well_name: { type: "string" },
              expected_presence: { type: "boolean" },
            },
            required: ["slot_name", "well_name"],
          },
        },
        enable_liquid_gate: {
          type: "boolean",
          default: false,
          description:
            "When true, run live_liquid_recovery_gate even without source_plan or required_sources.",
        },
        allow_observed_mismatch_reprobe: { type: "boolean", default: false },
        max_block_ms: { type: "integer", default: 0 },
        poll_interval_ms: { type: "integer", default: 250 },
        timeout_ms: { type: "integer" },
        page_length: { type: "integer", default: 20 },
        tiprack_slots: {
          type: "array",
          items: { type: "string" },
        },
        tip_binding_mode: {
          type: "string",
          enum: ["auto", "explicit", "starting_tip"],
        },
        protocol_source: { type: "string" },
        file_path: { type: "string" },
        protocol_path: { type: "string" },
        watch_dir: { type: "string" },
        record_result_log: { type: "boolean", default: true },
        publish_notifications: {
          type: "boolean",
          default: true,
          description:
            "When true, publish requires-attention monitor notifications into runtime alerts and the durable outbox.",
        },
        include_info_notifications: {
          type: "boolean",
          default: false,
          description:
            "When true, also publish info monitor notifications; default keeps the outbox low-noise.",
        },
        notify_adapters: {
          type: "array",
          items: {
            type: "string",
            enum: ["claudecode", "codex", "cursor", "piagent", "opencode", "cli", "webhook"],
          },
          description:
            "Optional host adapters to deliver newly pending outbox events after the monitor tick.",
        },
        notify_limit: { type: "integer", default: 20 },
        outbox_dir: { type: "string" },
        host_adapter_dir: { type: "string" },
        webhook_url: { type: "string" },
      },
    },
  },
  {
    name: "parse_error",
    description: "Parse run or maintenance command failures into structured runtime error categories.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        run_id: { type: "string" },
        context_type: {
          type: "string",
          enum: ["protocol", "maintenance"],
        },
        context_id: { type: "string" },
        session_id: { type: "string" },
        page_length: { type: "integer", default: 20 },
      },
    },
  },
  {
    name: "doctor_local_runtime",
    description: "Probe whether the local Python environment can import opentrons.simulate.",
    inputSchema: {
      type: "object",
      properties: {
        workspace_root: { type: "string" },
        api_root: { type: "string" },
        shared_data_root: { type: "string" },
        python_executable: { type: "string" },
      },
    },
  },
  {
    name: "simulate_protocol",
    description: "Run local opentrons.simulate against a protocol file and return structured logs. When virtual_lab_steps (or validate_virtual_lab_state=true) is provided, runs deterministic Virtual Lab State validation first and blocks the Python simulation on any violation (Phase 1.5 gate).",
    inputSchema: {
      type: "object",
      properties: {
        protocol_path: { type: "string" },
        workspace_root: { type: "string" },
        api_root: { type: "string" },
        shared_data_root: { type: "string" },
        python_executable: { type: "string" },
        extra_args: {
          type: "array",
          items: { type: "string" },
        },
        max_log_chars: { type: "integer", default: 20000 },
        session_id: {
          type: "string",
          description: "Session whose Virtual Lab State seeds validation when initial_state is omitted.",
        },
        initial_state: {
          type: "object",
          description: "Optional Virtual Lab State override; defaults to the persisted session state.",
        },
        virtual_lab_steps: {
          type: "array",
          description: "Proposed protocol steps to validate before simulating. When provided, the gate runs and blocks on violations.",
          items: { type: "object" },
        },
        validate_virtual_lab_state: {
          type: "boolean",
          description: "Force the Virtual Lab State gate even when virtual_lab_steps is omitted (uses persisted session containers).",
        },
        skip_virtual_lab_state_validation: {
          type: "boolean",
          description: "Explicit escape hatch for the simulation-repair loop when intentionally simulating a known-bad protocol.",
        },
      },
      required: ["protocol_path"],
    },
  },
  {
    name: "parse_simulation_output",
    description: "Classify simulation stdout/stderr into structured repair categories.",
    inputSchema: {
      type: "object",
      properties: {
        simulation_output_json: { type: "string" },
        stdout: { type: "string" },
        stderr: { type: "string" },
        exit_code: { type: "integer" },
        protocol_path: { type: "string" },
      },
    },
  },
  {
    name: "health_check",
    description: "Comprehensive environment health check: MCP server, Python venv, opentrons package, git state, session state, and optional robot connectivity.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Optional robot IP to check connectivity (e.g. 10.31.2.149)" },
        python_executable: {
          type: "string",
          description: "Optional Python interpreter to inspect instead of the repo-local .venv.",
        },
      },
    },
  },
  {
    name: "runtime_recovery_self_test",
    description:
      "Run no-motion recovery invariants inside the loaded MCP process, including liquidNotFound classification, source-map mismatch handling, and manual-only liquid recovery.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "live_liquid_recovery_gate",
    description:
      "Read-only go/no-go gate before live liquid watcher or probe re-runs. Checks loaded recovery self-test, robot/module status, door/estop, source-map readiness, source identity, and attached-tip blockers without moving the robot. Returns an ordered resolution_plan for clearing blockers safely.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        session_id: { type: "string" },
        source_plan: {
          type: "string",
          enum: ["c3_d3_liquid_recovery"],
          description:
            "Optional built-in source-map plan. c3_d3_liquid_recovery expands to C3.A1 present, D3.A1-H1 present, and D3.A12 absent.",
        },
        required_sources: {
          type: "array",
          description:
            "Optional source-map requirements that must be present before live liquid re-runs. Each item includes slot_name, well_name, and optional expected_presence.",
          items: {
            type: "object",
            properties: {
              slot_name: { type: "string", description: "Deck slot such as C3 or D3" },
              well_name: { type: "string", description: "Well name such as A1" },
              expected_presence: { type: "boolean" },
            },
            required: ["slot_name", "well_name"],
          },
        },
        allow_observed_mismatch_reprobe: {
          type: "boolean",
          default: false,
          description:
            "When true, expected-present sources with observed_presence=false become a warning that permits only targeted no-aspirate probe_wells evidence collection, not resume.",
        },
        recovery_steps: {
          type: "array",
          description:
            "Optional Virtual Lab State steps for suffix sufficiency preflight during substitution auto-resume gating.",
        },
        error_step_index: {
          type: "integer",
          description: "Failed step index for suffix replay; required with recovery_steps for suffix gating.",
        },
        failed_source_key: { type: "string", description: "Optional substitution context for suffix gating." },
        failed_slot_name: { type: "string" },
        failed_well_name: { type: "string" },
        preferred_source_key: { type: "string" },
      },
      required: ["robot_ip"],
    },
  },
  {
    name: "live_readiness_check",
    description:
      "Read-only live readiness gate for Flex: combines local runtime health, restart/session guidance, robot/module status, home safety, and optional preflight into pass/warn/fail checks before create_run or play.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        session_id: { type: "string" },
        file_path: {
          type: "string",
          description: "Optional protocol file path; when set, also runs preflight_run_setup read-only checks.",
        },
        python_executable: {
          type: "string",
          description: "Optional Python interpreter for the local runtime readiness check.",
        },
        run_id: {
          type: "string",
          description: "Optional current run id for context; forwarded to preflight when provided.",
        },
      },
      required: ["robot_ip"],
    },
  },
  {
    name: "preflight_run_setup",
    description:
      "Before play: verify session reconciliation, robot readiness, and (Flex) declared protocol loads vs live deck snapshot. Callable standalone or invoked automatically inside run_protocol after run creation.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        file_path: { type: "string", description: "Path to protocol .py for declared deck extraction" },
        session_id: { type: "string" },
        run_id: {
          type: "string",
          description: "Optional; when set, includes this run's labware snapshot in observed deck state",
        },
        skip_deck_diff: {
          type: "boolean",
          description: "If true, skip protocol-source vs deck comparison (still checks reconciliation and robot readiness)",
        },
        strict_empty_labware_slots: {
          type: "boolean",
          description: "If true, treat empty observed slots as errors when the protocol declares labware there",
        },
      },
      required: ["robot_ip", "file_path"],
    },
  },
];

async function uploadProtocol(args) {
  const { robot_ip, file_path, protocol_kind, key, run_time_parameters } = args;
  const protocolPath = path.resolve(file_path);
  if (!fs.existsSync(protocolPath)) {
    throw new Error(`Protocol file not found: ${protocolPath}`);
  }

  const form = new FormData();
  const fileBuffer = fs.readFileSync(protocolPath);
  form.append(
    "files",
    new Blob([fileBuffer], { type: "text/x-python" }),
    path.basename(protocolPath),
  );

  if (protocol_kind) {
    form.append("protocolKind", protocol_kind);
  }
  if (key) {
    form.append("key", key);
  }
  if (run_time_parameters) {
    form.append("runTimeParameterValues", JSON.stringify(run_time_parameters));
  }

  return requestRobotJson("POST", robot_ip, "/protocols", { body: form });
}

async function readRobotStatus(args) {
  const [health, instruments, doorStatus, estopStatus, deckConfiguration] = await Promise.all([
    requestRobotJson("GET", args.robot_ip, "/health"),
    requestRobotJson("GET", args.robot_ip, "/instruments"),
    requestRobotJson("GET", args.robot_ip, "/robot/door/status"),
    requestRobotJson("GET", args.robot_ip, "/robot/control/estopStatus"),
    requestRobotJson("GET", args.robot_ip, "/deck_configuration"),
  ]);

  const snapshot = buildRobotStatusSnapshot({
    health,
    instruments,
    doorStatus,
    estopStatus,
    deckConfiguration,
  });

  return {
    data: snapshot,
    hardwareSnapshot: {
      health,
      instruments,
      door_status: doorStatus,
      estop_status: estopStatus,
      deck_configuration: deckConfiguration,
    },
  };
}

async function readModuleStatus(args) {
  const modules = await requestRobotJson("GET", args.robot_ip, "/modules");
  const snapshot = buildModuleStatusSnapshot(modules);

  return {
    data: snapshot,
    hardwareSnapshot: {
      modules,
    },
  };
}

async function readCameraStatus(args) {
  const camera = await requestRobotJson("GET", args.robot_ip, "/camera");
  const snapshot = buildCameraStatusSnapshot(camera);

  return {
    data: snapshot,
    hardwareSnapshot: {
      camera,
    },
  };
}

async function readRunHistory(args) {
  const pageLength = args.page_length ?? 10;
  const [run, commands] = await Promise.all([
    requestRobotJson("GET", args.robot_ip, `/runs/${args.run_id}`),
    requestRobotJson("GET", args.robot_ip, `/runs/${args.run_id}/commands`, {
      searchParams: { pageLength },
    }),
  ]);

  const snapshot = buildRunHistorySnapshot(run, commands);

  return {
    data: snapshot,
    hardwareSnapshot: {
      run,
      commands,
    },
    runId: snapshot.run_id || args.run_id,
  };
}

async function collectRunExecutionSnapshot({ robotIp, runId, pageLength = 20 } = {}) {
  const [robotStatusResult, moduleStatusResult, runHistoryResult] = await Promise.all([
    readRobotStatus({ robot_ip: robotIp }),
    readModuleStatus({ robot_ip: robotIp }),
    readRunHistory({
      robot_ip: robotIp,
      run_id: runId,
      page_length: pageLength,
    }),
  ]);

  return {
    robotStatusResult,
    moduleStatusResult,
    runHistoryResult,
  };
}

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

function buildSelfTestCheck(name, passed, details = {}) {
  return {
    name,
    status: passed ? "pass" : "fail",
    passed,
    details,
  };
}

function buildRuntimeRecoverySelfTestResult() {
  const buildLiquidProbeFailureCase = ({
    commandId,
    wellName,
    sourceMapEntry,
    sampleId,
  }) => {
    const failedCommand = {
      id: commandId,
      commandType: "liquidProbe",
      status: "failed",
      params: {
        pipetteId: "pipette-left",
        labwareId: "self-test-d3-plate",
        wellName,
      },
      error: {
        errorType: "liquidNotFound",
        detail: "Liquid Not Found",
        wrappedErrors: [
          {
            errorType: "PipetteLiquidNotFoundError",
            detail: "Liquid not found during probe.",
          },
        ],
      },
    };
    const run = {
      data: {
        id: "self-test-run",
        status: "awaiting-recovery",
        currentlyRecoveringFrom: failedCommand.id,
        labware: [
          {
            id: "self-test-d3-plate",
            loadName: "corning_96_wellplate_360ul_flat",
            location: {
              slotName: "D3",
            },
          },
        ],
      },
    };
    const commands = {
      data: [failedCommand],
    };
    const robotStatusSnapshot = {
      blockers: [],
      instruments_summary: [
        {
          mount: "left",
          instrument_name: "p1000_single_flex",
          tip_detected: true,
        },
      ],
    };
    const moduleStatusSnapshot = {
      blockers: [],
    };
    const sessionState = {
      state_revision: 0,
      deck: { slots: {} },
      pipettes: {},
      cleanup: { pending_actions: [] },
      liquid_tracking: {
        sources: {
          [`D3.${wellName}`]: {
            slot_name: "D3",
            well_name: wellName,
            labware_load_name: "corning_96_wellplate_360ul_flat",
            sample_id: sampleId,
            ...sourceMapEntry,
          },
        },
      },
      tip_tracking: { tipracks: {} },
    };

    const classification = classifyRecoveryError({
      run,
      commands,
      moduleStatusSnapshot,
      robotStatusSnapshot,
    });
    const recovery = buildRecoverySuggestion({
      errorCategory: classification.error_category,
      errorLeaf: classification.error_leaf,
      run,
      commands,
      robotStatusSnapshot,
      moduleStatusSnapshot,
      reconciliation: { diffs: [] },
      sessionState,
    });
    const actionSummary = buildActionSummary({
      recoverySuggestion: recovery,
      run,
    });

    return {
      failedCommand,
      classification,
      recovery,
      actionSummary,
    };
  };

  const emptySourceCase = buildLiquidProbeFailureCase({
    commandId: "self-test-liquid-empty-command",
    wellName: "A12",
    sampleId: "self-test-empty-source-d3-a12",
    sourceMapEntry: {
      liquid_name: "empty-control",
      expected_presence: false,
      notes: "Self-test fixture: empty source must not be auto-substituted.",
    },
  });
  const expectedPresentCase = buildLiquidProbeFailureCase({
    commandId: "self-test-liquid-expected-present-command",
    wellName: "A1",
    sampleId: "self-test-expected-present-d3-a1",
    sourceMapEntry: {
      liquid_name: "operator-confirmed-liquid",
      expected_presence: true,
      notes: "Self-test fixture: expected-present source that probes as empty must stop for human confirmation.",
    },
  });
  const failedCommand = emptySourceCase.failedCommand;
  const classification = emptySourceCase.classification;
  const recovery = emptySourceCase.recovery;
  const actionSummary = emptySourceCase.actionSummary;
  const expectedPresentActionSummary = expectedPresentCase.actionSummary;
  const expectedPresentRecovery = expectedPresentCase.recovery;
  const cleanupRequired = actionSummary.params?.cleanup_required || [];
  const expectedPresentCleanupRequired = expectedPresentActionSummary.params?.cleanup_required || [];
  const checks = [
    buildSelfTestCheck(
      "runtime_build_stamp",
      MCP_RUNTIME_CAPABILITIES.runtime_build === "liquid-source-map-v2",
      { runtime_build: MCP_RUNTIME_CAPABILITIES.runtime_build },
    ),
    buildSelfTestCheck(
      "liquid_not_found_classifies_as_insufficient_volume",
      classification.error_category === "INSUFFICIENT_VOLUME" &&
        classification.error_leaf === "INSUFFICIENT_VOLUME",
      {
        error_category: classification.error_category,
        error_leaf: classification.error_leaf,
      },
    ),
    buildSelfTestCheck("liquid_recovery_is_manual_only", recovery.action === "manual_only", {
      action: recovery.action,
    }),
    buildSelfTestCheck("liquid_recovery_is_not_auto_executable", recovery.auto_executable === false, {
      auto_executable: recovery.auto_executable,
    }),
    buildSelfTestCheck("liquid_recovery_does_not_resume_run", actionSummary.then_resume === false, {
      then_resume: actionSummary.then_resume,
    }),
    buildSelfTestCheck("source_map_resolves_failed_well", actionSummary.params?.source_map_key === "D3.A12", {
      source_map_key: actionSummary.params?.source_map_key,
    }),
    buildSelfTestCheck(
      "expected_absent_source_is_mismatch",
      actionSummary.params?.source_map_expectation_mismatch === true &&
        actionSummary.params?.source_map_expected_presence === false &&
        actionSummary.params?.observed_liquid_presence === false,
      {
        source_map_expectation_mismatch: actionSummary.params?.source_map_expectation_mismatch,
        source_map_expected_presence: actionSummary.params?.source_map_expected_presence,
        observed_liquid_presence: actionSummary.params?.observed_liquid_presence,
      },
    ),
    buildSelfTestCheck(
      "expected_present_source_probe_empty_is_mismatch",
      expectedPresentRecovery.action === "manual_only" &&
        expectedPresentRecovery.auto_executable === false &&
        expectedPresentActionSummary.then_resume === false &&
        expectedPresentActionSummary.params?.source_map_key === "D3.A1" &&
        expectedPresentActionSummary.params?.source_map_expectation_mismatch === true &&
        expectedPresentActionSummary.params?.source_map_expected_presence === true &&
        expectedPresentActionSummary.params?.observed_liquid_presence === false,
      {
        action: expectedPresentRecovery.action,
        auto_executable: expectedPresentRecovery.auto_executable,
        then_resume: expectedPresentActionSummary.then_resume,
        source_map_key: expectedPresentActionSummary.params?.source_map_key,
        source_map_expectation_mismatch: expectedPresentActionSummary.params?.source_map_expectation_mismatch,
        source_map_expected_presence: expectedPresentActionSummary.params?.source_map_expected_presence,
        observed_liquid_presence: expectedPresentActionSummary.params?.observed_liquid_presence,
      },
    ),
    buildSelfTestCheck("attached_tip_cleanup_is_reported", cleanupRequired.includes("drop_tip:left"), {
      cleanup_required: cleanupRequired,
    }),
    buildSelfTestCheck(
      "expected_present_attached_tip_cleanup_is_reported",
      expectedPresentCleanupRequired.includes("drop_tip:left"),
      { cleanup_required: expectedPresentCleanupRequired },
    ),
    buildSelfTestCheck(
      "source_change_requires_human_confirmation",
      actionSummary.params?.blocked_auto_recovery_reason ===
        "liquid_source_change_requires_human_confirmation" &&
        expectedPresentActionSummary.params?.blocked_auto_recovery_reason ===
          "liquid_source_change_requires_human_confirmation",
      {
        blocked_auto_recovery_reason: actionSummary.params?.blocked_auto_recovery_reason,
        expected_present_blocked_auto_recovery_reason:
          expectedPresentActionSummary.params?.blocked_auto_recovery_reason,
      },
    ),
  ];
  const failedChecks = checks.filter(check => !check.passed);

  return {
    data: {
      status: failedChecks.length === 0 ? "pass" : "fail",
      runtime_build: MCP_RUNTIME_CAPABILITIES.runtime_build,
      checks,
      failed_checks: failedChecks,
      classification,
      recovery,
      action_summary: actionSummary,
      expected_present_case: {
        classification: expectedPresentCase.classification,
        recovery: expectedPresentRecovery,
        action_summary: expectedPresentActionSummary,
        fixture: {
          command_id: expectedPresentCase.failedCommand.id,
          slot_name: "D3",
          well_name: "A1",
          expected_presence: true,
          motion: "none",
          network: "none",
        },
      },
      fixture: {
        run_id: "self-test-run",
        command_id: failedCommand.id,
        slot_name: "D3",
        well_name: "A12",
        motion: "none",
        network: "none",
      },
    },
  };
}

function buildGateCheck(name, status, summary, extra = {}) {
  return {
    name,
    status,
    summary,
    ...extra,
  };
}

function summarizeRuntimeSelfTestCoverage(selfTestData = {}) {
  return {
    expected_absent_source: {
      source_map_key: selfTestData.action_summary?.params?.source_map_key || null,
      source_map_expected_presence:
        selfTestData.action_summary?.params?.source_map_expected_presence ?? null,
      observed_liquid_presence:
        selfTestData.action_summary?.params?.observed_liquid_presence ?? null,
      manual_only: selfTestData.action_summary?.do_what === "manual_only",
      then_resume: selfTestData.action_summary?.then_resume ?? null,
    },
    expected_present_source: {
      source_map_key: selfTestData.expected_present_case?.action_summary?.params?.source_map_key || null,
      source_map_expected_presence:
        selfTestData.expected_present_case?.action_summary?.params?.source_map_expected_presence ?? null,
      observed_liquid_presence:
        selfTestData.expected_present_case?.action_summary?.params?.observed_liquid_presence ?? null,
      manual_only: selfTestData.expected_present_case?.action_summary?.do_what === "manual_only",
      then_resume: selfTestData.expected_present_case?.action_summary?.then_resume ?? null,
    },
  };
}

function summarizeAttachedLiquidGateTips(robotStatusSnapshot = {}) {
  return asArray(robotStatusSnapshot.instruments_summary)
    .filter(instrument => instrument?.mount && instrument.mount !== "extension" && instrument.tip_detected === true)
    .map(instrument => ({
      mount: instrument.mount,
      instrument_name: instrument.instrument_name || null,
      model: instrument.model || null,
      serial: instrument.serial || null,
    }));
}

function normalizeLiquidGateSourceRequirement(source = {}) {
  const slotName = source.slot_name || source.slotName;
  const wellName = source.well_name || source.wellName;
  const slot = slotName ? String(slotName).trim().toUpperCase() : null;
  const well = wellName ? String(wellName).trim().toUpperCase() : null;
  const rawExpectedPresence = source.expected_presence ?? source.expectedPresence ?? null;
  const expectedPresenceIsValid =
    rawExpectedPresence === null || typeof rawExpectedPresence === "boolean";
  return {
    slot_name: slot,
    well_name: well,
    key: slot && well ? `${slot}.${well}` : null,
    expected_presence: expectedPresenceIsValid ? rawExpectedPresence : null,
    invalid_reason: expectedPresenceIsValid
      ? null
      : `expected_presence must be boolean when provided, got ${typeof rawExpectedPresence}`,
  };
}

const LIQUID_GATE_SOURCE_PLANS = new Set(["c3_d3_liquid_recovery"]);

function expandLiquidGateSourcePlan(sourcePlan = null) {
  if (!sourcePlan) {
    return [];
  }

  switch (String(sourcePlan)) {
    case "c3_d3_liquid_recovery":
      return [
        { slot_name: "C3", well_name: "A1", expected_presence: true },
        ...["A", "B", "C", "D", "E", "F", "G", "H"].map(row => ({
          slot_name: "D3",
          well_name: `${row}1`,
          expected_presence: true,
        })),
        { slot_name: "D3", well_name: "A12", expected_presence: false },
      ];
    default:
      return [];
  }
}

function resolveLiquidGateRequiredSources({ sourcePlan = null, requiredSources = [] } = {}) {
  const normalizedPlan = sourcePlan ? String(sourcePlan) : null;
  const invalidSourcePlan =
    normalizedPlan && !LIQUID_GATE_SOURCE_PLANS.has(normalizedPlan) ? normalizedPlan : null;
  return {
    requiredSources: invalidSourcePlan
      ? asArray(requiredSources)
      : [...expandLiquidGateSourcePlan(normalizedPlan), ...asArray(requiredSources)],
    invalidSourcePlan,
  };
}

function buildLiquidSourceMapGateCheck(sessionState = {}, requiredSources = [], { allowObservedMismatchReprobe = false } = {}) {
  const requirements = asArray(requiredSources).map(normalizeLiquidGateSourceRequirement);
  const sources = sessionState?.liquid_tracking?.sources || {};
  const details = requirements.map(requirement => {
    const entry = requirement.key ? sources[requirement.key] || null : null;
    const expectedPresenceMatches =
      requirement.expected_presence === null ||
      (entry && entry.expected_presence === requirement.expected_presence);
    const observedPresenceMatches =
      requirement.expected_presence === null ||
      !entry ||
      entry.observed_presence !== false ||
      requirement.expected_presence === false;
    return {
      ...requirement,
      present_in_source_map: Boolean(entry),
      expected_presence_matches: Boolean(entry && expectedPresenceMatches),
      observed_presence_matches: Boolean(entry && observedPresenceMatches),
      liquid_name: entry?.liquid_name || null,
      sample_id: entry?.sample_id || null,
      actual_expected_presence: entry?.expected_presence ?? null,
      observed_presence: entry?.observed_presence ?? null,
      observed_run_id: entry?.observed_run_id || null,
    };
  });
  const invalidRequirements = details.filter(detail => !detail.key || detail.invalid_reason);
  const missingSources = details.filter(detail => detail.key && !detail.present_in_source_map);
  const mismatchedPresence = details.filter(
    detail => detail.present_in_source_map && detail.expected_presence_matches === false,
  );
  const observedPresenceMismatches = details.filter(
    detail => detail.present_in_source_map && detail.observed_presence_matches === false,
  );
  const observedMismatchReprobeAllowed =
    allowObservedMismatchReprobe &&
    observedPresenceMismatches.length > 0 &&
    invalidRequirements.length === 0 &&
    missingSources.length === 0 &&
    mismatchedPresence.length === 0;
  const failures = [
    ...invalidRequirements,
    ...missingSources,
    ...mismatchedPresence,
    ...(observedMismatchReprobeAllowed ? [] : observedPresenceMismatches),
  ];

  if (requirements.length === 0) {
    return buildGateCheck(
      "source_map_requirements",
      "pass",
      "No source-map requirements were requested for this gate.",
      {
        required_sources: [],
      },
    );
  }

  return buildGateCheck(
    "source_map_requirements",
    failures.length === 0 ? (observedMismatchReprobeAllowed ? "warn" : "pass") : "fail",
    failures.length === 0
      ? observedMismatchReprobeAllowed
        ? "Requested source-map entries are present, but live observations disagree; only targeted no-aspirate re-probe is allowed."
        : "All requested liquid source-map entries are present and match expected presence."
      : "One or more requested liquid source-map entries are missing or do not match expected presence.",
    {
      required_sources: details,
      missing_source_keys: missingSources.map(detail => detail.key),
      mismatched_presence_keys: mismatchedPresence.map(detail => detail.key),
      observed_presence_mismatch_keys: observedPresenceMismatches.map(detail => detail.key),
      observed_mismatch_reprobe_allowed: observedMismatchReprobeAllowed,
      allowed_probe_targets: observedMismatchReprobeAllowed
        ? observedPresenceMismatches.map(detail => detail.key)
        : [],
      invalid_requirements: invalidRequirements,
    },
  );
}

function buildLiquidSourceIdentityOperatorGuidance(sessionId = DEFAULT_SESSION_ID) {
  return {
    draft_markdown_path: "runs/self-recovery/artifacts/liquid-source-identity-draft.md",
    draft_json_path: "runs/self-recovery/artifacts/liquid-source-identity-draft.json",
    draft_tsv_path: "runs/self-recovery/artifacts/liquid-source-identity-draft.tsv",
    validation_report_path: "runs/self-recovery/artifacts/liquid-source-identity-md-validation-latest.json",
    generate_draft_command: [
      "node scripts/summarize-liquid-source-map.mjs",
      `--session-id ${sessionId}`,
      "--out runs/self-recovery/artifacts/liquid-source-map-summary-with-md-latest.json",
      "--template-json-out runs/self-recovery/artifacts/liquid-source-identity-draft.json",
      "--template-tsv-out runs/self-recovery/artifacts/liquid-source-identity-draft.tsv",
      "--template-md-out runs/self-recovery/artifacts/liquid-source-identity-draft.md",
    ].join(" "),
    validate_markdown_command: [
      "node scripts/summarize-liquid-source-map.mjs",
      `--session-id ${sessionId}`,
      "--validate-template-md runs/self-recovery/artifacts/liquid-source-identity-draft.md",
      "--report-out runs/self-recovery/artifacts/liquid-source-identity-md-validation-latest.json",
    ].join(" "),
    apply_markdown_command: [
      "node scripts/summarize-liquid-source-map.mjs",
      "--apply-template-md runs/self-recovery/artifacts/liquid-source-identity-draft.md",
      "--report-out runs/self-recovery/artifacts/liquid-source-identity-md-apply-latest.json",
    ].join(" "),
  };
}

function buildLiquidSourceIdentityMetadataGateCheck(sourceMapCheck = {}, { sessionId = DEFAULT_SESSION_ID } = {}) {
  const requiredSources = asArray(sourceMapCheck.required_sources);
  const checkedSources = requiredSources.filter(
    source =>
      source.present_in_source_map &&
      source.expected_presence_matches !== false &&
      source.expected_presence === true,
  );
  const incompleteSources = checkedSources
    .map(source => {
      const missing = [];
      if (!source.liquid_name) {
        missing.push("liquid_name");
      } else if (source.liquid_name === "operator-confirmed-liquid") {
        missing.push("specific_liquid_name");
      }
      if (!source.sample_id) {
        missing.push("sample_id");
      }
      return missing.length > 0 ? { ...source, missing_identity_fields: missing } : null;
    })
    .filter(Boolean);

  return buildGateCheck(
    "source_identity_metadata",
    incompleteSources.length > 0 ? "warn" : "pass",
    incompleteSources.length > 0
      ? "Some expected-present liquid sources have incomplete liquid/sample identity metadata."
      : "Expected-present liquid sources include liquid and sample identity metadata.",
    {
      checked_source_count: checkedSources.length,
      incomplete_source_count: incompleteSources.length,
      incomplete_sources: incompleteSources,
      operator_guidance: incompleteSources.length > 0
        ? buildLiquidSourceIdentityOperatorGuidance(sessionId)
        : null,
    },
  );
}

function buildLiquidSourceIdentityMetadataSummary(sourcesByKey = {}, { slotName = null } = {}) {
  const normalizedSlot = slotName ? String(slotName).trim().toUpperCase() : null;
  const entries = Object.entries(sourcesByKey || {})
    .map(([key, source]) => ({ key, ...source }))
    .filter(source => !normalizedSlot || source.slot_name === normalizedSlot)
    .sort((left, right) => left.key.localeCompare(right.key));
  const expectedPresent = entries.filter(source => source.expected_presence === true);
  const expectedAbsent = entries.filter(source => source.expected_presence === false);
  const unknownPresence = entries.filter(source => source.expected_presence !== true && source.expected_presence !== false);
  const observedPresenceMismatches = entries.filter(
    source =>
      (source.expected_presence === true || source.expected_presence === false) &&
      (source.observed_presence === true || source.observed_presence === false) &&
      source.expected_presence !== source.observed_presence,
  );
  const incompleteExpectedPresent = expectedPresent
    .map(source => {
      const missing = [];
      if (!source.liquid_name) {
        missing.push("liquid_name");
      } else if (source.liquid_name === "operator-confirmed-liquid") {
        missing.push("specific_liquid_name");
      }
      if (!source.sample_id) {
        missing.push("sample_id");
      }
      return missing.length > 0 ? { ...source, missing_identity_fields: missing } : null;
    })
    .filter(Boolean);
  const recordLiquidSourceMapTemplate = incompleteExpectedPresent.map(source => ({
    slot_name: source.slot_name,
    well_name: source.well_name,
    labware_load_name: source.labware_load_name || null,
    expected_presence: true,
    liquid_name: source.liquid_name && source.liquid_name !== "operator-confirmed-liquid"
      ? source.liquid_name
      : "TODO_specific_liquid_name",
    sample_id: source.sample_id || "TODO_sample_id",
    notes: source.notes || "Fill in exact liquid/sample identity before semantic recovery.",
  }));
  const recordLiquidSourceMapDraft = {
    sources: recordLiquidSourceMapTemplate,
  };

  return {
    source_count: entries.length,
    expected_present_count: expectedPresent.length,
    expected_absent_count: expectedAbsent.length,
    unknown_presence_count: unknownPresence.length,
    observed_presence_mismatch_count: observedPresenceMismatches.length,
    incomplete_expected_present_count: incompleteExpectedPresent.length,
    ready_for_semantic_recovery:
      incompleteExpectedPresent.length === 0 &&
      observedPresenceMismatches.length === 0 &&
      expectedPresent.length > 0,
    incomplete_expected_present_sources: incompleteExpectedPresent,
    observed_presence_mismatch_sources: observedPresenceMismatches,
    record_liquid_source_map_template: recordLiquidSourceMapTemplate,
    record_liquid_source_map_draft: recordLiquidSourceMapDraft,
    complete_expected_present_sources: expectedPresent.filter(
      source => !incompleteExpectedPresent.some(incomplete => incomplete.key === source.key),
    ),
    expected_absent_sources: expectedAbsent,
    unknown_presence_sources: unknownPresence,
    operator_action:
      incompleteExpectedPresent.length > 0
        ? "Record a specific liquid_name and sample_id for expected-present sources before semantic recovery or source substitution."
        : observedPresenceMismatches.length > 0
          ? "Review or correct sources where live probe observations disagree with the source map before semantic recovery or source substitution."
        : "Expected-present sources have specific liquid and sample identity metadata.",
  };
}

function buildLiquidSourcePlanGateCheck(sourcePlan = null, invalidSourcePlan = null) {
  return buildGateCheck(
    "source_plan",
    invalidSourcePlan ? "fail" : "pass",
    invalidSourcePlan
      ? "Unknown source plan; refusing to treat it as an empty source requirement set."
      : "Source plan is recognized or not requested.",
    {
      requested_source_plan: sourcePlan || null,
      supported_source_plans: [...LIQUID_GATE_SOURCE_PLANS],
    },
  );
}

function buildLiveLiquidGateNextAction({ failedCheckNames = [], warningCheckNames = [] } = {}) {
  const failed = new Set(failedCheckNames);
  const warned = new Set(warningCheckNames);

  if (failed.has("loaded_runtime_recovery_self_test")) {
    return {
      recommended_next_action: "reload_or_reinstall_mcp_runtime",
      allowed_next_tools: ["health_check", "runtime_recovery_self_test"],
      human_required: true,
      reason: "loaded_runtime_recovery_self_test_failed",
    };
  }
  if (failed.has("robot_readonly_connectivity")) {
    return {
      recommended_next_action: "restore_robot_connectivity",
      allowed_next_tools: ["health_check", "robot_status", "module_status"],
      human_required: true,
      reason: "robot_readonly_connectivity_failed",
    };
  }
  if (failed.has("door_and_estop")) {
    return {
      recommended_next_action: "resolve_door_or_estop",
      allowed_next_tools: ["robot_status"],
      human_required: true,
      reason: "door_or_estop_not_safe",
    };
  }
  if (failed.has("source_plan")) {
    return {
      recommended_next_action: "correct_gate_source_plan",
      allowed_next_tools: ["live_liquid_recovery_gate"],
      human_required: true,
      reason: "unknown_liquid_source_plan",
    };
  }
  if (failed.has("source_map_requirements")) {
    return {
      recommended_next_action: "record_or_correct_liquid_source_map",
      allowed_next_tools: ["record_liquid_source_map", "get_liquid_source_map", "live_liquid_recovery_gate"],
      human_required: true,
      reason: "required_liquid_sources_missing_or_mismatched",
    };
  }
  if (failed.has("pending_probe_writeback")) {
    return {
      recommended_next_action: "apply_pending_probe_writeback",
      allowed_next_tools: ["apply_liquid_probe_results", "live_liquid_recovery_gate"],
      human_required: false,
      reason: "pending_probe_writeback",
    };
  }
  if (failed.has("suffix_plan_not_sufficient")) {
    return {
      recommended_next_action: "review_suffix_recovery_plan",
      allowed_next_tools: ["plan_liquid_source_substitution", "validate_virtual_lab_state_steps", "live_liquid_recovery_gate"],
      human_required: true,
      reason: "suffix_plan_not_sufficient",
    };
  }
  if (warned.has("source_map_requirements")) {
    return {
      recommended_next_action: "run_observed_mismatch_reprobe",
      allowed_next_tools: ["probe_wells", "apply_liquid_probe_results", "live_liquid_recovery_gate"],
      human_required: false,
      reason: "observed_presence_mismatch_reprobe_allowed",
    };
  }
  if (failed.has("no_attached_tip_before_liquid_probe_rerun")) {
    return {
      recommended_next_action: "clear_attached_tip_before_liquid_rerun",
      allowed_next_tools: ["robot_status", "live_liquid_recovery_gate", "experiment_history"],
      human_required: true,
      reason: "attached_tip_blocks_liquid_probe_rerun",
    };
  }
  if (warned.has("source_identity_metadata")) {
    return {
      recommended_next_action: "confirm_liquid_source_identity_before_semantic_recovery",
      allowed_next_tools: ["record_liquid_source_map", "get_liquid_source_map", "live_liquid_recovery_gate"],
      human_required: true,
      reason: "liquid_source_identity_metadata_incomplete",
    };
  }
  if (warned.has("module_blockers")) {
    return {
      recommended_next_action: "wait_or_resolve_module_blockers",
      allowed_next_tools: ["module_status", "live_liquid_recovery_gate"],
      human_required: false,
      reason: "module_blockers_reported",
    };
  }
  return {
    recommended_next_action: "run_live_liquid_recovery_tests",
    allowed_next_tools: ["runtime_watch_poll", "probe_wells", "run_protocol", "experiment_history"],
    human_required: false,
    reason: "live_liquid_recovery_gate_passed",
  };
}

function buildLiveLiquidGateResolutionPlan({
  failedCheckNames = [],
  warningCheckNames = [],
  checks = [],
  sessionId = DEFAULT_SESSION_ID,
} = {}) {
  const failed = new Set(failedCheckNames);
  const warned = new Set(warningCheckNames);
  const checksByName = new Map(checks.map(item => [item.name, item]));
  const plan = [];
  const add = item => {
    plan.push({
      order: plan.length + 1,
      no_robot_motion: true,
      ...item,
    });
  };

  if (failed.has("loaded_runtime_recovery_self_test")) {
    add({
      check_name: "loaded_runtime_recovery_self_test",
      severity: "blocker",
      action: "reload_or_reinstall_mcp_runtime",
      human_required: true,
      allowed_next_tools: ["health_check", "runtime_recovery_self_test"],
      acceptance_criteria: [
        "Loaded runtime_recovery_self_test returns status=pass.",
        "health_check reports mcp_server.entrypoint under the expected labscriptai-ot clone root.",
        "health_check reports mcp_server.capabilities.runtime_build=liquid-source-map-v2.",
        "health_check reports mcp_server.required_runtime_tools.all_present=true.",
      ],
    });
  }
  if (failed.has("robot_readonly_connectivity")) {
    add({
      check_name: "robot_readonly_connectivity",
      severity: "blocker",
      action: "restore_robot_connectivity",
      human_required: true,
      allowed_next_tools: ["health_check", "robot_status", "module_status"],
      acceptance_criteria: ["robot_status can read the robot and reports robot_reachable=true."],
    });
  }
  if (failed.has("door_and_estop")) {
    add({
      check_name: "door_and_estop",
      severity: "blocker",
      action: "resolve_door_or_estop",
      human_required: true,
      allowed_next_tools: ["robot_status"],
      acceptance_criteria: ["Door is closed and estop is disengaged in robot_status."],
    });
  }
  if (failed.has("source_plan")) {
    add({
      check_name: "source_plan",
      severity: "blocker",
      action: "correct_gate_source_plan",
      human_required: true,
      allowed_next_tools: ["live_liquid_recovery_gate"],
      acceptance_criteria: [`source_plan is one of: ${[...LIQUID_GATE_SOURCE_PLANS].join(", ")}.`],
    });
  }
  if (failed.has("source_map_requirements")) {
    add({
      check_name: "source_map_requirements",
      severity: "blocker",
      action: "record_or_correct_liquid_source_map",
      human_required: true,
      allowed_next_tools: ["record_liquid_source_map", "get_liquid_source_map", "live_liquid_recovery_gate"],
      acceptance_criteria: [
        "All required source-map entries exist.",
        "Each required entry expected_presence matches the gate requirement.",
        "No required expected-present source has observed_presence=false from a live probe.",
      ],
    });
  }
  if (failed.has("pending_probe_writeback")) {
    const pendingCheck = checksByName.get("pending_probe_writeback") || {};
    add({
      check_name: "pending_probe_writeback",
      severity: "blocker",
      action: "apply_pending_probe_writeback",
      human_required: false,
      allowed_next_tools: ["apply_liquid_probe_results", "live_liquid_recovery_gate"],
      acceptance_criteria: [
        "Each pending probe well has a matching apply_liquid_probe_results writeback.",
        "Pending probe writeback clears before live liquid watcher/probe re-runs.",
      ],
      pending_probe_wells: pendingCheck.pending_probe_wells || [],
    });
  }
  if (failed.has("suffix_plan_not_sufficient")) {
    const suffixCheck = checksByName.get("suffix_plan_not_sufficient") || {};
    add({
      check_name: "suffix_plan_not_sufficient",
      severity: "blocker",
      action: "review_suffix_recovery_plan",
      human_required: true,
      allowed_next_tools: [
        "plan_liquid_source_substitution",
        "validate_virtual_lab_state_steps",
        "live_liquid_recovery_gate",
      ],
      acceptance_criteria: [
        "Suffix replay passes Virtual Lab State validation after the substitution patch.",
        "final_auto_resume_eligible is true only when suffix_sufficient and auto_resume_eligible are both true.",
      ],
      violations: suffixCheck.violations || [],
      caution: "Suffix preflight failure is a severe warning; do not auto-resume until violations are resolved.",
    });
  }
  if (warned.has("source_map_requirements")) {
    const sourceMapCheck = checksByName.get("source_map_requirements") || {};
    add({
      check_name: "source_map_requirements",
      severity: "warning",
      action: "run_observed_mismatch_reprobe",
      human_required: false,
      allowed_next_tools: ["probe_wells", "apply_liquid_probe_results", "live_liquid_recovery_gate"],
      acceptance_criteria: [
        "Only probe wells listed in allowed_probe_targets.",
        "The probe protocol uses require_liquid_presence or detect_presence only.",
        "The probe protocol has no aspirate or dispense commands.",
        "Apply the probe result back to source-map observed_presence before any resume.",
      ],
      allowed_probe_targets: sourceMapCheck.allowed_probe_targets || [],
      caution: "This warning permits evidence collection only; it does not permit runtime_watch, run_protocol resume, aspirate, or dispense.",
    });
  }
  if (failed.has("no_attached_tip_before_liquid_probe_rerun")) {
    add({
      check_name: "no_attached_tip_before_liquid_probe_rerun",
      severity: "blocker",
      action: "clear_attached_tip_before_liquid_rerun",
      human_required: true,
      allowed_next_tools: ["robot_status", "live_liquid_recovery_gate", "experiment_history"],
      acceptance_criteria: ["robot_status reports no pipette with tip_detected=true."],
      caution: "Do not auto-home or run liquid tests while a tip remains attached after Stall/Collision.",
    });
  }
  if (warned.has("source_identity_metadata")) {
    const identityCheck = checksByName.get("source_identity_metadata");
    add({
      check_name: "source_identity_metadata",
      severity: "warning",
      action: "confirm_liquid_source_identity_before_semantic_recovery",
      human_required: true,
      allowed_next_tools: ["record_liquid_source_map", "get_liquid_source_map", "live_liquid_recovery_gate"],
      acceptance_criteria: [
        "C3.A1 and D3.A1-H1 expected-present sources have specific liquid_name.",
        "C3.A1 and D3.A1-H1 expected-present sources have sample_id.",
        "validate-template-md report has status=pass before apply.",
      ],
      operator_guidance:
        identityCheck?.operator_guidance || buildLiquidSourceIdentityOperatorGuidance(sessionId),
      inputs_needed: (identityCheck?.incomplete_sources || []).map(source => ({
        key: source.key || `${source.slot_name}.${source.well_name}`,
        slot_name: source.slot_name || null,
        well_name: source.well_name || null,
        current_liquid_name: source.liquid_name || null,
        current_sample_id: source.sample_id || null,
        missing_identity_fields: source.missing_identity_fields || [],
      })),
    });
  }
  if (warned.has("module_blockers")) {
    add({
      check_name: "module_blockers",
      severity: "warning",
      action: "wait_or_resolve_module_blockers",
      human_required: false,
      allowed_next_tools: ["module_status", "live_liquid_recovery_gate"],
      acceptance_criteria: ["module_status reports no blockers."],
    });
  }

  if (plan.length === 0) {
    add({
      check_name: "live_liquid_recovery_gate",
      severity: "ready",
      action: "run_live_liquid_recovery_tests",
      human_required: false,
      no_robot_motion: false,
      allowed_next_tools: ["runtime_watch_poll", "probe_wells", "run_protocol", "experiment_history"],
      acceptance_criteria: [
        "D3 A12 empty-source watcher stops before aspirate and returns needs_user.",
        "C3.A1 and D3.A1-H1 positive liquid probes detect liquid as expected.",
      ],
    });
  }

  return plan;
}

function buildLiveLiquidGateOperatorRequest(resolutionPlan = []) {
  const humanSteps = resolutionPlan.filter(step => step?.human_required === true);
  const requests = humanSteps.map(step => {
    const request = {
      order: step.order,
      check_name: step.check_name,
      severity: step.severity,
      action: step.action,
      no_robot_motion: step.no_robot_motion !== false,
      prompt: `Please resolve ${step.action}.`,
      prompt_zh: `请处理：${step.action}。`,
      allowed_next_tools: step.allowed_next_tools || [],
      acceptance_criteria: step.acceptance_criteria || [],
    };
    if (step.check_name === "no_attached_tip_before_liquid_probe_rerun") {
      request.request_type = "physical_state";
      request.prompt =
        "Please clear or confirm the left attached-tip state, then let the agent verify with robot_status.";
      request.prompt_zh =
        "请先清除或确认左侧移液器仍挂着的枪头状态；之后让我用 robot_status 只读复查。";
      request.safety_note = step.caution || null;
      request.safety_note_zh =
        "上一次清理遇到 Stall/Collision 后，不要自动 home，也不要继续跑液体测试。";
    } else if (step.check_name === "source_identity_metadata") {
      request.request_type = "liquid_identity";
      request.prompt =
        "Please fill exact liquid_name and sample_id for C3.A1 and D3.A1-H1 before semantic liquid recovery.";
      request.prompt_zh =
        "请补全 C3.A1 和 D3.A1-H1 的具体 liquid_name 与 sample_id；否则只能判断有液体，不能判断是不是正确液体。";
      request.artifacts = {
        draft_markdown_path: step.operator_guidance?.draft_markdown_path || null,
        validation_report_path: step.operator_guidance?.validation_report_path || null,
      };
      request.inputs_needed = Array.isArray(step.inputs_needed) ? step.inputs_needed : [];
      request.commands = {
        generate_draft_command: step.operator_guidance?.generate_draft_command || null,
        validate_markdown_command: step.operator_guidance?.validate_markdown_command || null,
        apply_markdown_command: step.operator_guidance?.apply_markdown_command || null,
      };
    } else {
      request.request_type = "operator_action";
    }
    return request;
  });

  return {
    human_required: requests.length > 0,
    request_count: requests.length,
    summary:
      requests.length > 0
        ? "Human input is required before live liquid watcher/probe tests can continue."
        : "No operator input is required by the current gate result.",
    summary_zh:
      requests.length > 0
        ? "继续真机液体 watcher/probe 测试前，需要人先处理下面这些事项。"
        : "当前 gate 结果不需要人额外处理。",
    requests,
  };
}

function buildLiveLiquidRecoveryGateResult({
  robotIp,
  selfTestResult,
  robotStatusResult,
  moduleStatusResult,
  sessionState,
  requiredSources = [],
  sourcePlan = null,
  invalidSourcePlan = null,
  sessionId = DEFAULT_SESSION_ID,
  allowObservedMismatchReprobe = false,
  suffixEvaluation = null,
} = {}) {
  const selfTest = selfTestResult?.data || {};
  const robotStatus = robotStatusResult?.data || {};
  const moduleStatus = moduleStatusResult?.data || {};
  const attachedTips = summarizeAttachedLiquidGateTips(robotStatus);
  const sourcePlanCheck = buildLiquidSourcePlanGateCheck(sourcePlan, invalidSourcePlan);
  const sourceMapCheck = buildLiquidSourceMapGateCheck(sessionState, requiredSources, {
    allowObservedMismatchReprobe,
  });
  const sourceIdentityCheck = buildLiquidSourceIdentityMetadataGateCheck(sourceMapCheck, {
    sessionId,
  });
  const pendingProbeWells = getPendingProbeWritebackWells(sessionId);
  const pendingProbeCheck = buildGateCheck(
    "pending_probe_writeback",
    pendingProbeWells.length === 0 ? "pass" : "fail",
    pendingProbeWells.length === 0
      ? "No pending live probe writebacks remain."
      : "One or more live probe wells still require apply_liquid_probe_results writeback.",
    {
      pending_probe_wells: pendingProbeWells,
      pending_probe_count: pendingProbeWells.length,
    },
  );
  const suffixCheck = (() => {
    if (!suffixEvaluation) {
      return null;
    }
    if (suffixEvaluation.blocked_reason === "suffix_steps_unavailable") {
      return buildGateCheck(
        "suffix_plan_not_sufficient",
        "warn",
        "Suffix recovery steps were not available for preflight.",
        {
          blocked_reason: "suffix_steps_unavailable",
          suffix_sufficient: false,
          substitution_plan: suffixEvaluation.plan || null,
        },
      );
    }
    if (suffixEvaluation.suffix_sufficient === true) {
      return buildGateCheck(
        "suffix_plan_not_sufficient",
        "pass",
        "Suffix replay passed Virtual Lab State validation.",
        {
          suffix_sufficient: true,
          final_auto_resume_eligible: suffixEvaluation.final_auto_resume_eligible === true,
          substitution_plan: suffixEvaluation.plan || null,
          violations: [],
        },
      );
    }
    return buildGateCheck(
      "suffix_plan_not_sufficient",
      "fail",
      "Suffix replay failed Virtual Lab State validation; auto-resume is blocked.",
      {
        blocked_reason: "suffix_plan_not_sufficient",
        suffix_sufficient: false,
        final_auto_resume_eligible: false,
        substitution_plan: suffixEvaluation.plan || null,
        violations: (suffixEvaluation.violations || []).map(violation => ({
          ...violation,
          step_index: violation.step_index ?? violation.step?.index ?? null,
        })),
      },
    );
  })();
  const checks = [
    buildGateCheck(
      "loaded_runtime_recovery_self_test",
      selfTest.status === "pass" ? "pass" : "fail",
      selfTest.status === "pass"
        ? "Loaded MCP runtime recovery self-test passed."
        : "Loaded MCP runtime recovery self-test failed.",
      {
        runtime_build: selfTest.runtime_build || null,
        failed_checks: selfTest.failed_checks || [],
        coverage: summarizeRuntimeSelfTestCoverage(selfTest),
      },
    ),
    buildGateCheck(
      "robot_readonly_connectivity",
      robotStatus.robot_reachable === true ? "pass" : "fail",
      robotStatus.robot_reachable === true
        ? "Robot read-only status endpoints are reachable."
        : "Robot read-only status endpoints are not reachable.",
      {
        robot_ip: robotIp || null,
        health_summary: robotStatus.health_summary || {},
      },
    ),
    buildGateCheck(
      "door_and_estop",
      robotStatus.door?.open === false && robotStatus.estop?.engaged === false ? "pass" : "fail",
      "Door must be closed and estop disengaged before live liquid watcher/probe re-runs.",
      {
        door: robotStatus.door || null,
        estop: robotStatus.estop || null,
      },
    ),
    buildGateCheck(
      "no_attached_tip_before_liquid_probe_rerun",
      attachedTips.length === 0 ? "pass" : "fail",
      attachedTips.length === 0
        ? "No pipette reports an attached tip."
        : "A pipette still reports an attached tip; clear this state before repeating live liquid watcher/probe tests.",
      {
        attached_tips: attachedTips,
      },
    ),
    buildGateCheck(
      "module_blockers",
      (moduleStatus.blockers || []).length === 0 ? "pass" : "warn",
      (moduleStatus.blockers || []).length === 0
        ? "No module blockers were reported."
        : "One or more module blockers were reported.",
      {
        blockers: moduleStatus.blockers || [],
      },
    ),
    sourcePlanCheck,
    sourceMapCheck,
    sourceIdentityCheck,
    pendingProbeCheck,
    ...(suffixCheck ? [suffixCheck] : []),
  ];
  const failedChecks = checks.filter(check => check.status === "fail");
  const warningChecks = checks.filter(check => check.status === "warn");
  const failedCheckNames = failedChecks.map(check => check.name);
  const warningCheckNames = warningChecks.map(check => check.name);
  const nextAction = buildLiveLiquidGateNextAction({
    failedCheckNames,
    warningCheckNames,
  });
  const resolutionPlan = buildLiveLiquidGateResolutionPlan({
    failedCheckNames,
    warningCheckNames,
    checks,
    sessionId,
  });
  const operatorRequest = buildLiveLiquidGateOperatorRequest(resolutionPlan);
  const blockedBy =
    failedCheckNames.includes("pending_probe_writeback")
      ? "pending_probe_writeback"
      : failedCheckNames.includes("suffix_plan_not_sufficient")
        ? "suffix_plan_not_sufficient"
        : null;

  return {
    status: failedChecks.length > 0 ? "blocked" : warningChecks.length > 0 ? "warn" : "pass",
    ok_for_live_liquid_rerun: failedChecks.length === 0,
    blocked_by: blockedBy,
    pending_probe_wells: pendingProbeWells,
    substitution_plan: suffixEvaluation?.plan || null,
    suffix_sufficient: suffixEvaluation?.suffix_sufficient ?? null,
    final_auto_resume_eligible: suffixEvaluation?.final_auto_resume_eligible ?? null,
    suffix_violations: suffixEvaluation?.violations || null,
    source_plan: sourcePlan || null,
    allow_observed_mismatch_reprobe: allowObservedMismatchReprobe,
    checks,
    failed_checks: failedCheckNames,
    warning_checks: warningCheckNames,
    ...nextAction,
    resolution_plan: resolutionPlan,
    operator_request: operatorRequest,
    next_steps: [
      failedCheckNames.includes("source_plan")
        ? `Use a supported source plan: ${[...LIQUID_GATE_SOURCE_PLANS].join(", ")}.`
        : null,
      failedCheckNames.includes("source_map_requirements")
        ? "Record or correct required liquid source-map entries before repeating liquid handling."
        : null,
      warningCheckNames.includes("source_map_requirements")
        ? "Only targeted no-aspirate re-probe is allowed for source-map/live-observation mismatches."
        : null,
      warningCheckNames.includes("source_identity_metadata")
        ? "Fill and validate runs/self-recovery/artifacts/liquid-source-identity-draft.md before semantic liquid recovery or source substitution."
        : null,
      failedCheckNames.includes("pending_probe_writeback")
        ? "Apply apply_liquid_probe_results for each pending probe well before repeating live liquid watcher/probe tests."
        : null,
      failedCheckNames.includes("suffix_plan_not_sufficient")
        ? "Resolve suffix replay violations before any substitution auto-resume."
        : null,
      attachedTips.length > 0 ? "Clear the attached pipette tip state before any liquid watcher/probe re-run." : null,
      failedChecks.length === 0
        ? "Proceed to D3 A12 empty-source watcher and C3/D3 positive liquid probe re-runs using the loaded MCP client."
        : "Do not run live liquid watcher/probe tests until failed gate checks are resolved.",
    ].filter(Boolean),
  };
}

function resolveSessionId(args, robotStatusResult) {
  return (
    args.session_id ||
    robotStatusResult?.data?.health_summary?.robot_serial ||
    DEFAULT_SESSION_ID
  );
}

function recordResultLog(entry) {
  try {
    return appendResultLogEntry(entry);
  } catch {
    // Result logging must never break the main MCP flow.
    return null;
  }
}

function resolveLoggedStatus({ result = null, error = null, fallback = "completed" } = {}) {
  return (
    result?.data?.final_status ||
    result?.data?.final_run_history?.status ||
    result?.data?.run_history?.status ||
    result?.data?.status ||
    (error?.toolContext?.data?.blocked_real_execution ? "blocked" : null) ||
    (error ? "error" : null) ||
    fallback
  );
}

function resolveLoggedSessionId({ args = {}, result = null, error = null, fallback = DEFAULT_SESSION_ID } = {}) {
  return result?.sessionId || error?.toolContext?.sessionId || args.session_id || fallback;
}

function resolveLoggedRunId({ result = null, error = null } = {}) {
  return result?.runId || error?.toolContext?.runId || null;
}

function recordToolResultLog({
  toolName,
  eventKind,
  args = {},
  result = null,
  error = null,
  summary = null,
  data = {},
  fallbackSessionId = DEFAULT_SESSION_ID,
  fallbackStatus = "completed",
} = {}) {
  return recordResultLog({
    session_id: resolveLoggedSessionId({ args, result, error, fallback: fallbackSessionId }),
    run_id: resolveLoggedRunId({ result, error }),
    tool_name: toolName,
    event_kind: eventKind || toolName,
    status: resolveLoggedStatus({ result, error, fallback: fallbackStatus }),
    summary,
    protocol_path: args.file_path || null,
    robot_ip: args.robot_ip || null,
    state_revision: result?.stateRevision ?? error?.toolContext?.stateRevision ?? 0,
    requires_attention:
      result?.data?.requires_attention ??
      error?.toolContext?.data?.requires_attention ??
      null,
    data,
    error: error
      ? {
          message: error instanceof Error ? error.message : String(error),
        }
      : null,
  });
}

function resolvePreviewOutputPath(args, contentType) {
  if (args.output_path) {
    return path.resolve(args.output_path);
  }

  const imageSettings = buildCameraImageSettings(args);
  const filename = buildPreviewArtifactName({
    robotIp: args.robot_ip,
    cameraId: imageSettings.cameraId,
    contentType,
  });
  return path.join(DEFAULT_CAMERA_ARTIFACT_DIR, filename);
}

function resolveCapturedImageOutputPath(args, { contentType, fileName = null } = {}) {
  if (args.output_path) {
    return path.resolve(args.output_path);
  }
  if (fileName) {
    const baseName = path.basename(fileName);
    if (path.extname(baseName)) {
      return path.join(DEFAULT_CAMERA_ARTIFACT_DIR, baseName);
    }
    return path.join(
      DEFAULT_CAMERA_ARTIFACT_DIR,
      `${baseName}.${contentTypeToExtension(contentType)}`,
    );
  }
  return resolvePreviewOutputPath(args, contentType);
}

function sanitizeProbeFilenamePart(value, fallback = "probe") {
  const normalized = String(value || fallback)
    .trim()
    .replace(/[^a-zA-Z0-9._-]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return normalized || fallback;
}

function resolveProbeProtocolOutputPath(args) {
  if (args.output_path) {
    return path.resolve(args.output_path);
  }
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const baseName = [
    "probe-wells",
    sanitizeProbeFilenamePart(args.mode || "detect_presence"),
    sanitizeProbeFilenamePart(args.labware_slot || "unknown-slot"),
    timestamp,
  ].join("_");
  return path.join(DEFAULT_PROBE_PROTOCOL_DIR, `${baseName}.py`);
}

function resolveContinuationProtocolOutputPath(args, runId) {
  if (args.output_path) {
    return path.resolve(args.output_path);
  }
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const baseName = [
    "continuation",
    sanitizeProbeFilenamePart(runId || "run"),
    timestamp,
  ].join("_");
  return path.join(DEFAULT_CONTINUATION_PROTOCOL_DIR, `${baseName}.py`);
}

function resolveLiquidSubstitutionProtocolOutputPath(args, failedSourceKey, selectedSourceKey) {
  if (args.output_path) {
    return path.resolve(args.output_path);
  }
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const baseName = [
    "liquid-source-substitution",
    sanitizeProbeFilenamePart(failedSourceKey || "failed-source"),
    sanitizeProbeFilenamePart(selectedSourceKey || args.preferred_source_key || "replacement"),
    timestamp,
  ].join("_");
  return path.join(DEFAULT_LIQUID_SUBSTITUTION_PROTOCOL_DIR, `${baseName}.py`);
}

function resolveLiquidSubstitutionRecoveryBundleOutputPath(args, failedSourceKey, selectedSourceKey) {
  if (args.output_path) {
    return path.resolve(args.output_path);
  }
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const baseName = [
    "liquid-source-substitution-recovery",
    sanitizeProbeFilenamePart(failedSourceKey || "failed-source"),
    sanitizeProbeFilenamePart(selectedSourceKey || args.preferred_source_key || "replacement"),
    timestamp,
  ].join("_");
  return path.join(DEFAULT_LIQUID_SUBSTITUTION_PROTOCOL_DIR, `${baseName}.json`);
}

function selectProtocolAnalysis(analysesPayload) {
  const analyses = asArray(unwrapData(analysesPayload));
  return (
    analyses.find(analysis => analysis?.status === "completed" && Array.isArray(analysis.commands)) ||
    analyses.find(analysis => Array.isArray(analysis?.commands)) ||
    null
  );
}

async function readProtocolAnalysisForRun(robotIp, runDetail) {
  const runRecord = unwrapData(runDetail) || {};
  const protocolId = readNested(runRecord, [["protocolId"]], null);
  if (!protocolId) {
    throw new Error("generate_continuation_protocol could not resolve protocolId from source run.");
  }

  const analyses = await requestRobotJson("GET", robotIp, `/protocols/${protocolId}/analyses`);
  const analysis = selectProtocolAnalysis(analyses);
  if (!analysis) {
    throw new Error(`generate_continuation_protocol found no analysis commands for protocol ${protocolId}.`);
  }

  return {
    protocolId,
    analysis,
    analysisCommands: asArray(analysis.commands),
  };
}

function rewriteVisionEndpointError(error, endpoint) {
  if (!(error instanceof Error)) {
    return error;
  }

  try {
    const parsed = JSON.parse(error.message);
    if (parsed?.status === 404) {
      return new Error(
        `Robot endpoint ${endpoint} is not available on this robot software. Current behavior observed on this Flex: GET /camera works, but some POST camera endpoints may return 404 and therefore cannot be used for autonomous preview capture yet.`,
      );
    }
  } catch {
    return error;
  }

  return error;
}

function requireNumericArg(args, key, toolName) {
  if (typeof args[key] !== "number") {
    throw new Error(`${toolName} requires numeric field ${key} for this action.`);
  }
}

function requireArrayArg(args, key, toolName) {
  if (!Array.isArray(args[key]) || args[key].length === 0) {
    throw new Error(`${toolName} requires non-empty array field ${key} for this action.`);
  }
}

async function readRunContext(args, { includeCommands = false, pageLength = 20 } = {}) {
  if (args.run_id) {
    const run = await requestRobotJson("GET", args.robot_ip, `/runs/${args.run_id}`);
    const commands = includeCommands
      ? await requestRobotJson("GET", args.robot_ip, `/runs/${args.run_id}/commands`, {
          searchParams: { pageLength },
        })
      : null;
    return {
      run,
      commands,
      runId: readNested(unwrapData(run) || {}, [["id"]], args.run_id),
    };
  }

  const runs = await requestRobotJson("GET", args.robot_ip, "/runs");
  const currentRun = asArray(unwrapData(runs)).find(run => run?.current) || null;
  const runId = readNested(currentRun, [["id"]], null);

  if (!runId || !includeCommands) {
    return {
      runs,
      run: currentRun,
      commands: null,
      runId,
    };
  }

  const commands = await requestRobotJson("GET", args.robot_ip, `/runs/${runId}/commands`, {
    searchParams: { pageLength },
  });

  return {
    runs,
    run: currentRun,
    commands,
    runId,
  };
}

async function readAnyContext(args, { includeCommands = false, pageLength = 20 } = {}) {
  if (args.context_id) {
    const contextResult = await readExecutionContext(
      args.robot_ip,
      args.context_type || "maintenance",
      args.context_id,
      { includeCommands, pageLength },
    );
    return {
      contextType: contextResult.contextType,
      run: contextResult.detail,
      commands: contextResult.commands,
      runId: deriveContextRunId(contextResult.contextType, contextResult.contextId),
      contextId: contextResult.contextId,
    };
  }

  const runContext = await readRunContext(args, { includeCommands, pageLength });
  return {
    contextType: "protocol",
    ...runContext,
    contextId: runContext.runId,
  };
}

async function readExecutionContext(robotIp, contextType, contextId, { includeCommands = false, pageLength = 20 } = {}) {
  const paths = buildContextPaths(contextType, contextId);
  const detail = await requestRobotJson("GET", robotIp, paths.detailPath);
  const commands = includeCommands
    ? await requestRobotJson("GET", robotIp, paths.commandsPath, {
        searchParams: { pageLength },
      })
    : null;

  return {
    contextType: paths.contextType,
    detail,
    commands,
    contextId: readNested(unwrapData(detail) || {}, [["id"]], contextId),
  };
}

async function readDataFileInfo(robotIp, dataFileId) {
  return requestRobotJson("GET", robotIp, `/dataFiles/${dataFileId}`);
}

async function downloadDataFile(robotIp, dataFileId) {
  return requestRobotBytes("GET", robotIp, `/dataFiles/${dataFileId}/download`);
}

async function pollCommandToTerminal({
  robotIp,
  contextType,
  contextId,
  commandId,
  timeoutMs = 20000,
  pollIntervalMs = 500,
}) {
  const paths = buildContextPaths(contextType, contextId);
  const startedAt = Date.now();
  let latest = null;

  while (Date.now() - startedAt <= timeoutMs) {
    latest = await requestRobotJson("GET", robotIp, paths.commandPath(commandId));
    const status = readNested(unwrapData(latest) || {}, [["status"]], null);
    if (isTerminalCommandStatus(status)) {
      return latest;
    }
    await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
  }

  throw new Error(
    `Timed out waiting for command ${commandId} in ${paths.contextType} context ${contextId} to reach terminal status.`,
  );
}

async function pollRunToTerminal({
  robotIp,
  runId,
  timeoutMs = 1800000,
  pollIntervalMs = 1000,
}) {
  const startedAt = Date.now();
  let latest = null;

  while (Date.now() - startedAt <= timeoutMs) {
    latest = await requestRobotJson("GET", robotIp, `/runs/${runId}`);
    const status = readNested(unwrapData(latest) || {}, [["status"]], null);
    if (isTerminalRunStatus(status)) {
      return latest;
    }
    await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
  }

  throw new Error(`Timed out waiting for run ${runId} to reach a terminal status.`);
}

async function enqueueAndPollCommand({
  robotIp,
  contextType,
  contextId,
  commandPayload,
  timeoutMs = 20000,
  pollIntervalMs = 500,
}) {
  const paths = buildContextPaths(contextType, contextId);
  const created = await requestRobotJson("POST", robotIp, paths.commandsPath, {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(commandPayload),
  });
  const commandId = readNested(unwrapData(created) || {}, [["id"]], null);
  if (!commandId) {
    throw new Error("Command creation did not return a command id.");
  }

  const terminal = await pollCommandToTerminal({
    robotIp,
    contextType,
    contextId,
    commandId,
    timeoutMs,
    pollIntervalMs,
  });

  return {
    created,
    terminal,
  };
}

function deriveContextRunId(contextType, contextId) {
  return normalizeContextType(contextType) === "protocol" ? contextId : null;
}

function assertCommandSucceeded(result, label) {
  const terminal = unwrapData(result?.terminal) || {};
  const status = readNested(terminal, [["status"]], null);
  if (status !== "succeeded") {
    const commandType = readNested(terminal, [["commandType"]], label);
    const detail = readNested(terminal, [["error", "detail"]], null);
    throw new Error(
      `${label || commandType || "command"} failed with status ${status || "unknown"}${detail ? `: ${detail}` : ""}`,
    );
  }
}

function resolveContextSessionId(args, robotStatusResult, contextId = null) {
  return args.session_id || contextId || resolveSessionId(args, robotStatusResult);
}

async function collectExecutionSnapshot({
  robotIp,
  contextType,
  contextId,
  includeCommands = false,
}) {
  const [robotStatusResult, moduleStatusResult, contextResult] = await Promise.all([
    readRobotStatus({ robot_ip: robotIp }),
    readModuleStatus({ robot_ip: robotIp }),
    readExecutionContext(robotIp, contextType, contextId, { includeCommands }),
  ]);

  return {
    robotStatusResult,
    moduleStatusResult,
    contextResult,
  };
}

function syncSessionStateFromExecution({
  sessionState,
  robotStatusResult,
  moduleStatusResult,
  contextDetail,
  contextRunId,
  forceCommit = false,
}) {
  const observedDeckState = buildObservedDeckState({
    deckConfiguration: robotStatusResult.hardwareSnapshot.deck_configuration,
    modules: moduleStatusResult.hardwareSnapshot.modules,
    run: contextDetail,
  });

  const reconciliation = buildReconciliationResult({
    sessionState,
    robotStatusSnapshot: robotStatusResult.data,
    moduleStatusSnapshot: moduleStatusResult.data,
    observedDeckState,
    run: contextDetail,
  });

  if (forceCommit) {
    reconciliation.proposed_commit.needs_reconciliation = false;
  }

  applyObservedDeckToSessionState(sessionState, reconciliation.proposed_commit);
  sessionState.last_run_id = contextRunId || sessionState.last_run_id || null;
  const homeSafety = buildHomeSafetyResult({
    robotStatusSnapshot: robotStatusResult.data,
    sessionState,
  });
  setCleanupState(sessionState, {
    pending_actions: homeSafety.minimum_cleanup_actions,
    auto_home_allowed: homeSafety.auto_home_allowed,
  });

  return {
    observedDeckState,
    reconciliation,
    homeSafety,
  };
}

function getModuleSnapshotById(moduleStatusResult, moduleId) {
  return asArray(moduleStatusResult?.data?.modules).find(module => {
    const candidates = [module?.id, module?.serial].filter(Boolean);
    return candidates.includes(moduleId);
  }) || null;
}

function summarizeCommandExecution(action, commandResult) {
  const terminal = unwrapData(commandResult?.terminal) || {};
  return {
    action,
    command_created: commandResult?.created || null,
    command: commandResult?.terminal || null,
    status: readNested(terminal, [["status"]], null),
    error: readNested(terminal, [["error", "detail"], ["error", "message"]], null),
  };
}

function readCommandErrorDetail(commandResult) {
  const terminal = unwrapData(commandResult?.terminal) || {};
  return readNested(terminal, [["error", "detail"], ["error", "message"]], null);
}

function resolveFailedWellAndTiprackSlot({ args, run, failedCommand } = {}) {
  const failedWell = args.failed_well || readNested(failedCommand, [["params", "wellName"]], null);
  const explicitTiprackSlot = args.tiprack_slot || null;
  if (explicitTiprackSlot) {
    return {
      failedWell,
      tiprackSlot: explicitTiprackSlot,
    };
  }

  const labwareId = readNested(failedCommand, [["params", "labwareId"]], null);
  const labware = asArray(readNested(unwrapData(run) || {}, [["labware"]], [])).find(
    item => readNested(item, [["id"]], null) === labwareId,
  );

  return {
    failedWell,
    tiprackSlot: readNested(labware, [["location", "slotName"]], null),
  };
}

function readProtocolSourceForTipBinding(args = {}) {
  if (typeof args.protocol_source === "string" && args.protocol_source.trim()) {
    return {
      source: args.protocol_source,
      sourceType: "protocol_source",
      filePath: null,
    };
  }

  const inputPath = args.file_path || args.protocol_path || null;
  if (!inputPath) {
    return null;
  }

  const resolved = path.resolve(inputPath);
  if (!fs.existsSync(resolved)) {
    throw new Error(`Protocol file not found for tip binding classification: ${resolved}`);
  }

  return {
    source: fs.readFileSync(resolved, "utf8"),
    sourceType: "file_path",
    filePath: resolved,
  };
}

function resolveTipBindingClassification(args = {}) {
  if (args.tip_binding_mode) {
    const mode = String(args.tip_binding_mode).trim().toLowerCase();
    if (!["auto", "explicit", "starting_tip"].includes(mode)) {
      throw new Error(`Unsupported tip_binding_mode: ${args.tip_binding_mode}`);
    }
    return {
      mode,
      reason: "operator_supplied",
      source_type: "argument",
      file_path: null,
    };
  }

  const protocolSource = readProtocolSourceForTipBinding(args);
  if (!protocolSource) {
    return null;
  }

  const classification = classifyTipBindingModeDetail(protocolSource.source);
  return {
    ...classification,
    source_type: protocolSource.sourceType,
    file_path: protocolSource.filePath,
  };
}

async function readRunFailureGuidance(args, runId, sessionId = null) {
  const parseResult = await TOOL_HANDLERS.parse_error({
    ...args,
    run_id: runId,
    session_id: sessionId,
  });
  const recoveryResult = await TOOL_HANDLERS.suggest_recovery_action({
    ...args,
    run_id: runId,
    session_id: parseResult.sessionId || sessionId,
    target_slot: parseResult.data?.target_slot || args.target_slot,
    failed_well: parseResult.data?.failed_well || args.failed_well,
  });
  return {
    parsedError: parseResult.data,
    recovery: recoveryResult.data,
    hardwareSnapshot: recoveryResult.hardwareSnapshot || parseResult.hardwareSnapshot || {},
    sessionId: recoveryResult.sessionId || parseResult.sessionId || sessionId,
    stateRevision: recoveryResult.stateRevision ?? parseResult.stateRevision ?? 0,
  };
}

async function enforceSimulationGate(args) {
  const doctor = await runDoctorTool(args);
  if (!doctor?.ok || !doctor?.opentrons_simulate?.ok) {
    const doctorIssue = buildTaxonomyIssue({
      phase: "simulation",
      errorLeaf: doctor?.python ? "RUNTIME_UNAVAILABLE" : "PYTHON_ENV_BROKEN",
      message: "Simulation gate blocked because the local runtime is not ready.",
      overrides: {
        default_next_step: "doctor_local_runtime",
        evidence_sources: ["doctor_local_runtime"],
      },
    });
    const error = new Error("Simulation gate blocked real execution because the local runtime is not ready.");
    error.toolContext = {
      data: {
        blocked_real_execution: true,
        gate_stage: "doctor_local_runtime",
        doctor_local_runtime: doctor,
        parsed_simulation_output: {
          success: false,
          phase: "simulation",
          status: "failed",
          primary_issue: doctorIssue,
          error_domain: doctorIssue.error_domain,
          error_leaf: doctorIssue.error_leaf,
          recoverability: doctorIssue.recoverability,
          requires_human_review: doctorIssue.requires_human_review,
          default_next_step: doctorIssue.default_next_step,
          evidence_sources: doctorIssue.evidence_sources,
          issues: [doctorIssue],
        },
      },
    };
    throw error;
  }

  const simulation = await runSimulationTool({
    ...args,
    protocol_path: args.file_path,
  });
  const parsed = parseSimulationLog({
    simulation_output_json: simulation,
    protocol_path: simulation.protocol || args.file_path,
  });

  if (!simulation?.ok || parsed?.success === false) {
    const error = new Error("Simulation gate blocked real execution because the protocol did not pass local simulation.");
    error.toolContext = {
      data: {
        blocked_real_execution: true,
        gate_stage: "simulate_protocol",
        doctor_local_runtime: doctor,
        simulation_output: simulation,
        parsed_simulation_output: parsed,
      },
    };
    throw error;
  }

  return {
    doctor,
    simulation,
    parsed,
  };
}

function getLatestFailedCommand(commandsPayload) {
  if (!Array.isArray(unwrapData(commandsPayload))) {
    return null;
  }
  return [...unwrapData(commandsPayload)].reverse().find(command => command?.status === "failed") || null;
}

async function waitForModuleRecoveryReady({
  robotIp,
  timeoutMs = 120000,
  pollIntervalMs = 1000,
} = {}) {
  const startedAt = Date.now();
  let latest = null;

  while (Date.now() - startedAt <= timeoutMs) {
    latest = await readModuleStatus({ robot_ip: robotIp });
    if ((latest?.data?.blockers || []).length === 0) {
      return {
        ready: true,
        waited_ms: Date.now() - startedAt,
        module_status: latest.data,
      };
    }
    await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
  }

  return {
    ready: false,
    waited_ms: Date.now() - startedAt,
    module_status: latest?.data || null,
  };
}

function selectRecoveryDestinationSlot({
  recovery,
  requestedDestinationSlot = null,
  allowLowConfidence = false,
} = {}) {
  const candidates = Array.isArray(recovery?.candidate_destination_slots)
    ? recovery.candidate_destination_slots
    : [];
  if (candidates.length === 0) {
    throw new Error("execute_protocol_recovery did not receive any candidate destination slots.");
  }

  if (requestedDestinationSlot) {
    const requested = String(requestedDestinationSlot).toUpperCase();
    const matched =
      candidates.find(candidate => String(candidate?.slot_name || "").toUpperCase() === requested) || null;
    if (!matched) {
      throw new Error(
        `execute_protocol_recovery destination_slot ${requested} is not one of the suggested candidates.`,
      );
    }
    return matched;
  }

  const highConfidenceCandidate = candidates.find(candidate => candidate?.confidence === "high") || null;
  if (highConfidenceCandidate && recovery?.escalate_to_human !== true) {
    return highConfidenceCandidate;
  }
  if (allowLowConfidence) {
    return candidates[0];
  }

  throw new Error(
    "execute_protocol_recovery requires destination_slot (or allow_low_confidence_destination) for this human-reviewed destination recovery branch.",
  );
}

async function finalizeProtocolRecovery({
  args,
  sessionId,
  executionResult = {},
  waitForTerminal = true,
} = {}) {
  const resumeAction = await requestRobotJson("POST", args.robot_ip, `/runs/${args.run_id}/actions`, {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      data: {
        actionType: "resume-from-recovery",
      },
    }),
  });

  if (waitForTerminal) {
    await pollRunToTerminal({
      robotIp: args.robot_ip,
      runId: args.run_id,
      timeoutMs: args.timeout_ms ?? 120000,
      pollIntervalMs: args.poll_interval_ms ?? 500,
    });
  }

  const snapshot = await collectRunExecutionSnapshot({
    robotIp: args.robot_ip,
    runId: args.run_id,
    pageLength: args.page_length ?? 20,
  });
  const finalStatus = snapshot.runHistoryResult.data?.status || null;
  let postRecoveryGuidance = null;
  if (shouldAttachRecoveryGuidance(finalStatus)) {
    postRecoveryGuidance = await readRunFailureGuidance(args, args.run_id, sessionId);
  }

  const finalSessionId = postRecoveryGuidance?.sessionId || sessionId;
  let reconciliation = null;
  let homeSafety = null;
  const { state } = mutateSessionState(finalSessionId, sessionState => {
    ({ reconciliation, homeSafety } = syncSessionStateFromExecution({
      sessionState,
      robotStatusResult: snapshot.robotStatusResult,
      moduleStatusResult: snapshot.moduleStatusResult,
      contextDetail: snapshot.runHistoryResult.hardwareSnapshot.run,
      contextRunId: args.run_id,
      forceCommit: true,
    }));
    return sessionState;
  });

  return {
    data: {
      executed_action: executionResult.executedAction || null,
      executed_params: executionResult.executedParams || {},
      fixit_command: executionResult.fixitCommand || null,
      module_wait: executionResult.moduleWait || null,
      resume_action: resumeAction,
      terminal_poll_skipped: !waitForTerminal,
      final_run_history: snapshot.runHistoryResult.data,
      parsed_error: postRecoveryGuidance?.parsedError || null,
      recovery: postRecoveryGuidance?.recovery || null,
      reconciliation,
      home_safety: homeSafety,
    },
    hardwareSnapshot:
      postRecoveryGuidance?.hardwareSnapshot && Object.keys(postRecoveryGuidance.hardwareSnapshot).length > 0
        ? postRecoveryGuidance.hardwareSnapshot
        : {
            ...snapshot.robotStatusResult.hardwareSnapshot,
            ...snapshot.moduleStatusResult.hardwareSnapshot,
            ...snapshot.runHistoryResult.hardwareSnapshot,
          },
    stateRevision: state.state_revision,
    sessionId: finalSessionId,
    runId: args.run_id,
  };
}

async function executeProtocolRecovery(args, { expectedAction = null, watchMode = false } = {}) {
  const sessionId = args.session_id || args.run_id;
  const guidance = await readRunFailureGuidance(args, args.run_id, sessionId);
  const parsedError = guidance.parsedError || {};
  const recovery = guidance.recovery?.recovery || guidance.recovery || {};
  const actionSummary = guidance.recovery?.action_summary || null;
  const action = recovery.action || null;
  const guardedExpectedAction = expectedAction || args.expected_action || null;

  if (guardedExpectedAction && action !== guardedExpectedAction) {
    throw new Error(
      `execute_protocol_recovery expected ${guardedExpectedAction}, got ${action || "unknown"}.`,
    );
  }

  if (recovery.auto_executable !== true) {
    throw new Error(
      `execute_protocol_recovery only supports recovery branches marked auto_executable=true; got ${String(
        recovery.auto_executable,
      )} for action ${action || "unknown"}.`,
    );
  }

  const context = await readExecutionContext(args.robot_ip, "protocol", args.run_id, {
    includeCommands: true,
    pageLength: args.page_length ?? 20,
  });
  const runStatus = readNested(unwrapData(context.detail) || {}, [["status"]], null);
  if (String(runStatus || "").toLowerCase() !== "awaiting-recovery") {
    throw new Error(`execute_protocol_recovery requires run status awaiting-recovery, got ${runStatus || "unknown"}.`);
  }

  const failedCommand = getLatestFailedCommand(context.commands);
  let executionResult = {
    executedAction: action,
    executedParams: {},
    fixitCommand: null,
    moduleWait: null,
  };

  switch (action) {
    case "retry_pick_up_tip_with_next_candidate": {
      if (parsedError.error_category !== "TIP_PHYSICALLY_MISSING") {
        throw new Error(
          `execute_protocol_recovery expected TIP_PHYSICALLY_MISSING, got ${parsedError.error_category || "unknown"}.`,
        );
      }
      const labwareId = readNested(failedCommand, [["params", "labwareId"]], null);
      const pipetteId = readNested(failedCommand, [["params", "pipetteId"]], null);
      if (!labwareId || !pipetteId) {
        throw new Error("execute_protocol_recovery could not resolve labwareId/pipetteId from failed pickUpTip.");
      }

      const nextWell =
        args.recovery_well ||
        readNested(recovery, [["suggested_tip", "well_name"]], null) ||
        readNested(actionSummary, [["params", "well"]], null);
      const nextTiprackSlot =
        args.tiprack_slot ||
        readNested(recovery, [["suggested_tip", "tiprack_slot"]], null) ||
        readNested(actionSummary, [["params", "tiprack_slot"]], null);
      if (!nextWell) {
        throw new Error("execute_protocol_recovery could not determine the next recovery well.");
      }

      const fixitCommand = await enqueueAndPollCommand({
        robotIp: args.robot_ip,
        contextType: "protocol",
        contextId: args.run_id,
        commandPayload: buildCommandPayload({
          commandType: "pickUpTip",
          intent: "fixit",
          params: {
            pipetteId,
            labwareId,
            wellName: nextWell,
          },
        }),
        timeoutMs: args.timeout_ms ?? 120000,
        pollIntervalMs: args.poll_interval_ms ?? 500,
      });

      if (nextTiprackSlot && nextWell) {
        mutateSessionState(sessionId, sessionState => {
          markTipWellStatus(sessionState, {
            slotName: nextTiprackSlot,
            wellName: nextWell,
            status: "depleted",
          });
          return sessionState;
        });
      }

      executionResult = {
        executedAction: action,
        executedParams: {
          well: nextWell,
          tiprack_slot: nextTiprackSlot,
          pipette_id: pipetteId,
          labware_id: labwareId,
        },
        fixitCommand: fixitCommand.terminal,
        moduleWait: null,
      };
      break;
    }

    case "suggest_new_destination_slot": {
      const selectedDestination = selectRecoveryDestinationSlot({
        recovery,
        requestedDestinationSlot: args.destination_slot,
        allowLowConfidence: args.allow_low_confidence_destination === true,
      });
      const labwareId = readNested(failedCommand, [["params", "labwareId"]], null);
      if (!labwareId) {
        throw new Error("execute_protocol_recovery could not resolve labwareId from failed moveLabware.");
      }

      const fixitCommand = await enqueueAndPollCommand({
        robotIp: args.robot_ip,
        contextType: "protocol",
        contextId: args.run_id,
        commandPayload: buildMoveLabwareCommand({
          labwareId,
          newLocation: { slotName: selectedDestination.slot_name },
          strategy: readNested(failedCommand, [["params", "strategy"]], "usingGripper"),
          pickUpOffset: readNested(failedCommand, [["params", "pickUpOffset"]], null),
          dropOffset: readNested(failedCommand, [["params", "dropOffset"]], null),
          intent: "fixit",
          key: args.idempotency_key ? `${args.idempotency_key}:moveLabware` : null,
        }),
        timeoutMs: args.timeout_ms ?? 120000,
        pollIntervalMs: args.poll_interval_ms ?? 500,
      });

      executionResult = {
        executedAction: action,
        executedParams: {
          destination_slot: selectedDestination.slot_name,
          destination_confidence: selectedDestination.confidence || null,
          labware_id: labwareId,
        },
        fixitCommand: fixitCommand.terminal,
        moduleWait: null,
      };
      break;
    }

    case "wait_and_poll_module_status": {
      const moduleWait = await waitForModuleRecoveryReady({
        robotIp: args.robot_ip,
        timeoutMs: args.module_wait_timeout_ms ?? args.timeout_ms ?? 120000,
        pollIntervalMs: args.module_poll_interval_ms ?? 1000,
      });
      if (!moduleWait.ready) {
        throw new Error("execute_protocol_recovery timed out waiting for modules to become ready.");
      }

      executionResult = {
        executedAction: action,
        executedParams: {
          blockers_cleared: true,
        },
        fixitCommand: null,
        moduleWait,
      };
      break;
    }

    case "reconcile_state_first": {
      const diffs = Array.isArray(recovery?.diffs) ? recovery.diffs : [];
      const onlyModuleBlockers =
        diffs.length > 0 && diffs.every(diff => diff?.type === "module_blockers");
      if (!onlyModuleBlockers) {
        throw new Error(
          "execute_protocol_recovery only supports automatic reconcile_state_first when the pending diffs are module blockers.",
        );
      }

      const moduleWait = await waitForModuleRecoveryReady({
        robotIp: args.robot_ip,
        timeoutMs: args.module_wait_timeout_ms ?? args.timeout_ms ?? 120000,
        pollIntervalMs: args.module_poll_interval_ms ?? 1000,
      });
      if (!moduleWait.ready) {
        throw new Error("execute_protocol_recovery timed out waiting for module blockers to clear.");
      }

      executionResult = {
        executedAction: action,
        executedParams: {
          diffs_resolved: diffs.map(diff => diff.type),
        },
        fixitCommand: null,
        moduleWait,
      };
      break;
    }

    default:
      throw new Error(
        `execute_protocol_recovery does not support automatic execution for action ${action || "unknown"}.`,
      );
  }

  return finalizeProtocolRecovery({
    args,
    sessionId,
    executionResult,
    waitForTerminal: !(watchMode || args.watch_mode === true || args.skip_terminal_poll === true),
  });
}

async function runPreflightRunSetup(args) {
  if (!args.robot_ip) {
    throw new Error("preflight_run_setup requires robot_ip.");
  }
  if (!args.file_path) {
    throw new Error("preflight_run_setup requires file_path.");
  }

  const robotStatusResult = await readRobotStatus(args);
  const moduleStatusResult = await readModuleStatus(args);
  const sessionId = resolveSessionId(args, robotStatusResult);
  const sessionState = readSessionState(sessionId);
  const runContext = await readRunContext(
    { ...args, run_id: args.run_id || undefined },
    { includeCommands: false },
  );

  const preflight = buildPreflightRunSetupResult({
    filePath: args.file_path,
    sessionState,
    robotStatusSnapshot: robotStatusResult.data,
    deckConfigurationPayload: robotStatusResult.hardwareSnapshot.deck_configuration,
    modulesPayload: moduleStatusResult.hardwareSnapshot.modules,
    moduleStatusSnapshot: moduleStatusResult.data,
    runRecord: runContext.run || null,
    skipDeckDiff: Boolean(args.skip_deck_diff),
    strictEmptyLabwareSlots: Boolean(args.strict_empty_labware_slots),
  });

  return {
    data: preflight,
    hardwareSnapshot: {
      ...robotStatusResult.hardwareSnapshot,
      ...moduleStatusResult.hardwareSnapshot,
      run: runContext.run || null,
    },
    stateRevision: sessionState.state_revision,
    sessionId,
  };
}

async function executeRestartReview(args) {
  const limit = Math.max(1, Math.min(Number(args.limit || 20), 200));
  const hardwareSnapshot = {};
  let sessionId = args.session_id || DEFAULT_SESSION_ID;
  let sessionState = readSessionState(sessionId);
  let homeSafety = null;

  if (args.robot_ip) {
    const robotStatusResult = await readRobotStatus(args);
    Object.assign(hardwareSnapshot, robotStatusResult.hardwareSnapshot);
    sessionId = resolveSessionId(args, robotStatusResult);
    sessionState = readSessionState(sessionId);
    homeSafety = buildHomeSafetyResult({
      robotStatusSnapshot: robotStatusResult.data,
      sessionState,
    });
  }

  const logEntries = readResultLogEntries({ session_id: sessionId, limit });
  const data = buildRestartReview({
    sessionState,
    logEntries,
    homeSafety,
  });

  return {
    data,
    hardwareSnapshot,
    stateRevision: sessionState.state_revision,
    sessionId,
  };
}

function buildReadinessErrorCheck(name, summary, errorLeaf, error, evidenceSources = []) {
  return {
    name,
    status: "fail",
    summary,
    ...buildErrorTaxonomy({
      phase: "live_readiness",
      errorLeaf,
      overrides: {
        auto_executable: false,
        evidence_sources: evidenceSources,
      },
    }),
    error: error?.message || String(error || ""),
  };
}

async function executeLiveReadinessCheck(args) {
  const healthReport = buildHealthCheck(args);
  healthReport.robot = await checkRobotHealth(args.robot_ip);

  const hardwareSnapshot = {};
  const extraChecks = [];
  let robotStatusResult = null;
  let moduleStatusResult = null;
  let homeSafety = null;
  let preflight = null;
  let sessionId = args.session_id || DEFAULT_SESSION_ID;
  let sessionState = readSessionState(sessionId);

  if (healthReport.robot.status === "reachable") {
    try {
      robotStatusResult = await readRobotStatus(args);
      Object.assign(hardwareSnapshot, robotStatusResult.hardwareSnapshot);
      sessionId = resolveSessionId(args, robotStatusResult);
      sessionState = readSessionState(sessionId);
      homeSafety = buildHomeSafetyResult({
        robotStatusSnapshot: robotStatusResult.data,
        sessionState,
      });
    } catch (error) {
      extraChecks.push(
        buildReadinessErrorCheck(
          "robot_status",
          "Robot health endpoint is reachable, but live status endpoints failed.",
          "MCP_CONFIG_MISMATCH",
          error,
          ["robot_status"],
        ),
      );
    }

    try {
      moduleStatusResult = await readModuleStatus(args);
      Object.assign(hardwareSnapshot, moduleStatusResult.hardwareSnapshot);
    } catch (error) {
      extraChecks.push(
        buildReadinessErrorCheck(
          "module_status",
          "Live module status could not be read from the robot.",
          "MCP_CONFIG_MISMATCH",
          error,
          ["module_status"],
        ),
      );
    }

    if (args.file_path && robotStatusResult && moduleStatusResult) {
      try {
        const preflightWrap = await runPreflightRunSetup({
          robot_ip: args.robot_ip,
          file_path: args.file_path,
          session_id: sessionId,
          run_id: args.run_id,
        });
        preflight = preflightWrap.data;
      } catch (error) {
        preflight = {
          ok: false,
          allowed_to_play: false,
          robot_model: robotStatusResult?.data?.health_summary?.robot_model || null,
          deck_model: "flex_12_slot",
          blocking_checks: [
            {
              status: "fail",
              code: "preflight_execution_failed",
              message: error?.message || "preflight_run_setup failed unexpectedly.",
              ...buildErrorTaxonomy({
                phase: "preflight",
                errorLeaf: "UNKNOWN_NEEDS_HUMAN",
                overrides: {
                  auto_executable: false,
                  evidence_sources: ["preflight_run_setup"],
                },
              }),
            },
          ],
          warning_checks: [],
          errors: [],
          warnings: [],
          summary: error?.message || "preflight_run_setup failed unexpectedly.",
        };
      }
    }
  }

  const logEntries = readResultLogEntries({ session_id: sessionId, limit: 20 });
  const restartReviewData = buildRestartReview({
    sessionState,
    logEntries,
    homeSafety,
  });
  const safeNextAction = buildSafeNextAction(restartReviewData);
  const readiness = buildLiveReadinessReport({
    healthReport,
    restartReviewData,
    safeNextAction,
    robotStatusSnapshot: robotStatusResult?.data || null,
    moduleStatusSnapshot: moduleStatusResult?.data || null,
    homeSafety,
    preflight,
    hasFilePath: Boolean(args.file_path),
    extraChecks,
  });

  return {
    data: readiness,
    hardwareSnapshot,
    stateRevision: sessionState.state_revision,
    sessionId,
    runId: args.run_id || sessionState.last_run_id || null,
  };
}

function evaluateVirtualLabStateGate(args) {
  if (!args || args.skip_virtual_lab_state_validation === true) {
    return null;
  }
  const steps = Array.isArray(args.virtual_lab_steps) ? args.virtual_lab_steps : null;
  const explicitValidate = args.validate_virtual_lab_state === true;
  if (!steps && !explicitValidate) {
    return null;
  }
  if (steps && steps.length === 0) {
    return null;
  }

  const sessionId = args.session_id || DEFAULT_SESSION_ID;
  const initialState = args.initial_state || readSessionState(sessionId);
  const validation = validateVirtualLabStateSteps(initialState, steps || []);
  if (validation.ok) {
    return null;
  }

  return {
    data: {
      ok: false,
      error: {
        error_type: "VirtualLabStateViolations",
        error: `Virtual Lab State validation blocked simulation: ${validation.violations.length} violation(s).`,
      },
      blocked_by: "virtual_lab_state_validation",
      virtual_lab_validation: {
        ok: validation.ok,
        violation_count: validation.violations.length,
        violations: validation.violations,
        final_state: validation.state,
        no_robot_motion: true,
        persisted: false,
      },
      stdout: "",
      stderr: "",
      helper: {
        runner_python: null,
        helper_script: null,
        helper_exit_code: null,
      },
      no_robot_motion: true,
    },
    stateRevision: initialState.state_revision ?? null,
    sessionId: initialState.session_id || sessionId,
  };
}

const TOOL_HANDLERS = {
  async robot_health(args) {
    const health = await requestRobotJson("GET", args.robot_ip, "/health");
    return {
      data: {
        health,
      },
      hardwareSnapshot: {
        health,
      },
    };
  },

  async robot_status(args) {
    return readRobotStatus(args);
  },

  async module_status(args) {
    return readModuleStatus(args);
  },

  async get_slot_occupation(args) {
    const [robotStatusResult, moduleStatusResult, runContext] = await Promise.all([
      readRobotStatus(args),
      readModuleStatus(args),
      readAnyContext(args),
    ]);
    const sessionId = resolveSessionId(args, robotStatusResult);
    const sessionState = readSessionState(sessionId);
    const observedDeckState = buildObservedDeckState({
      deckConfiguration: robotStatusResult.hardwareSnapshot.deck_configuration,
      modules: moduleStatusResult.hardwareSnapshot.modules,
      run: runContext.run,
    });
    const slotOccupation = getSlotOccupationSummary({
      slotName: args.slot_name,
      observedDeckState,
      sessionState,
    });

    return {
      data: {
        slot_occupation: slotOccupation,
      },
      hardwareSnapshot: {
        ...robotStatusResult.hardwareSnapshot,
        ...moduleStatusResult.hardwareSnapshot,
        run: runContext.run || null,
      },
      stateRevision: sessionState.state_revision,
      sessionId,
      runId: runContext.runId || null,
    };
  },

  async list_available_slots(args) {
    const [robotStatusResult, moduleStatusResult, runContext] = await Promise.all([
      readRobotStatus(args),
      readModuleStatus(args),
      readAnyContext(args),
    ]);
    const sessionId = resolveSessionId(args, robotStatusResult);
    const sessionState = readSessionState(sessionId);
    const observedDeckState = buildObservedDeckState({
      deckConfiguration: robotStatusResult.hardwareSnapshot.deck_configuration,
      modules: moduleStatusResult.hardwareSnapshot.modules,
      run: runContext.run,
    });
    const availableSlots = listAvailableSlots({
      observedDeckState,
      sessionState,
      filter: args.filter || "all",
    });

    return {
      data: {
        available_slots: availableSlots,
      },
      hardwareSnapshot: {
        ...robotStatusResult.hardwareSnapshot,
        ...moduleStatusResult.hardwareSnapshot,
        run: runContext.run || null,
      },
      stateRevision: sessionState.state_revision,
      sessionId,
      runId: runContext.runId || null,
    };
  },

  async list_tip_candidates(args) {
    const [robotStatusResult, runContext] = await Promise.all([
      readRobotStatus(args),
      readRunContext(args),
    ]);
    const sessionId = resolveSessionId(args, robotStatusResult);
    let candidates;
    const { state } = mutateSessionState(sessionId, sessionState => {
      candidates = listTipCandidates({
        sessionState,
        run: runContext.run,
        tiprackSlots: args.tiprack_slots,
      });
      return sessionState;
    });

    return {
      data: candidates,
      hardwareSnapshot: {
        ...robotStatusResult.hardwareSnapshot,
        run: runContext.run || null,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: runContext.runId || null,
    };
  },

  async suggest_next_tip_well(args) {
    const [robotStatusResult, runContext] = await Promise.all([
      readRobotStatus(args),
      readRunContext(args, { includeCommands: true }),
    ]);
    const sessionId = resolveSessionId(args, robotStatusResult);
    const failedCommand =
      runContext.commands && Array.isArray(unwrapData(runContext.commands))
        ? [...unwrapData(runContext.commands)].reverse().find(command => command?.status === "failed") || null
        : null;
    const { failedWell, tiprackSlot } = resolveFailedWellAndTiprackSlot({
      args,
      run: runContext.run,
      failedCommand,
    });

    let suggestion;
    const { state } = mutateSessionState(sessionId, sessionState => {
      suggestion = suggestNextTipWell({
        sessionState,
        run: runContext.run,
        tiprackSlots: args.tiprack_slots,
        tiprackSlot,
        failedWell,
        failureStatus: args.failure_status || "missing",
      });
      return sessionState;
    });

    return {
      data: suggestion,
      hardwareSnapshot: {
        ...robotStatusResult.hardwareSnapshot,
        run: runContext.run || null,
        commands: runContext.commands || null,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: runContext.runId || null,
    };
  },

  async record_liquid_source_map(args) {
    const sessionId = args.session_id || DEFAULT_SESSION_ID;
    const sources = Array.isArray(args.sources) ? args.sources : [];
    if (sources.length === 0) {
      throw new Error("record_liquid_source_map requires at least one source.");
    }

    const recorded = [];
    const { state } = mutateSessionState(sessionId, sessionState => {
      for (const source of sources) {
        const entry = setLiquidSourceState(sessionState, source);
        if (entry) {
          recorded.push(entry);
        }
      }
      return sessionState;
    });

    return {
      data: {
        recorded_sources: recorded,
        liquid_tracking: state.liquid_tracking,
      },
      stateRevision: state.state_revision,
      sessionId,
    };
  },

  async apply_liquid_probe_results(args) {
    const hasBatchInput =
      (Array.isArray(args.probe_results) && args.probe_results.length > 0) ||
      Boolean(args.probe_artifact_path || args.probe_artifact);
    if (hasBatchInput) {
      const result = await applyLiquidProbeResults(args, {
        writeObservedProbeResults,
        summarizeLiquidSourceMap: TOOL_HANDLERS.summarize_liquid_source_map.bind(TOOL_HANDLERS),
      });

      recordToolResultLog({
        toolName: "apply_liquid_probe_results",
        eventKind: "liquid_probe_writeback",
        args,
        result,
        fallbackSessionId: result.sessionId || args.session_id || DEFAULT_SESSION_ID,
        fallbackStatus: "pass",
        summary: `Applied live probe writeback for ${result.data.applied_count} well(s).`,
        data: result.data,
      });

      return result;
    }

    const sessionId = args.session_id || DEFAULT_SESSION_ID;
    const slotName = String(args.slot_name || "").trim().toUpperCase();
    const wellName = String(args.well_name || "").trim().toUpperCase();
    if (!slotName || !wellName) {
      throw new Error("apply_liquid_probe_results requires slot_name and well_name.");
    }

    const containerKey = liquidContainerKey({ slotName, wellName });
    const sessionStateBefore = readSessionState(sessionId);
    const existing =
      sessionStateBefore.liquid_tracking?.containers?.[containerKey] ||
      sessionStateBefore.liquid_tracking?.sources?.[containerKey] ||
      {};
    const expectedPresence = existing.expected_presence ?? null;

    let volumeUl = null;
    let method = "presence_only";
    let observedPresence = args.observed_presence;

    if (args.actual_volume_ul !== undefined && args.actual_volume_ul !== null) {
      volumeUl = Number(args.actual_volume_ul);
      method = "explicit";
    } else if (args.height_mm !== undefined && args.height_mm !== null) {
      const conversion = callHeightMmToVolumeUl({
        height_mm: args.height_mm,
        labware_load_name: args.labware_load_name || existing.labware_load_name || null,
        well_name: wellName,
      });
      if (!conversion) {
        throw new Error(
          "apply_liquid_probe_results received height_mm but heightMmToVolumeUl is unavailable or could not convert.",
        );
      }
      volumeUl = conversion.volume_ul ?? null;
      method = conversion.method || "height_conversion";
    } else if (observedPresence === true || observedPresence === false) {
      volumeUl = null;
      method = "presence_only";
    } else {
      throw new Error(
        "apply_liquid_probe_results requires actual_volume_ul, height_mm, or observed_presence.",
      );
    }

    if (observedPresence === undefined || observedPresence === null) {
      if (volumeUl !== null && Number.isFinite(volumeUl)) {
        observedPresence = volumeUl > 0;
      } else if (args.height_mm !== undefined && args.height_mm !== null) {
        observedPresence = true;
      }
    }

    const currentTrust = existing.trust_level || "declared";
    if (!canOverwriteTrust(currentTrust, "observed") && args.force !== true) {
      return {
        data: {
          blocked_by: "trust_downgrade_blocked",
          trust_level: currentTrust,
          attempted_trust_level: "observed",
          container_key: containerKey,
          session_id: sessionId,
        },
        stateRevision: sessionStateBefore.state_revision,
        sessionId,
      };
    }

    const observedAt = new Date().toISOString();
    const runId = args.run_id || null;
    const { state } = mutateSessionState(sessionId, sessionState => {
      setLiquidContainerState(sessionState, {
        slot_name: slotName,
        well_name: wellName,
        labware_load_name: args.labware_load_name || existing.labware_load_name || null,
        volume_ul: volumeUl,
        observed_presence: observedPresence ?? null,
        trust_level: "observed",
        observed_source: "live_probe",
        observed_at: observedAt,
        observed_run_id: runId,
        role: existing.role || "source",
        why: "apply_liquid_probe_results",
      });
      return sessionState;
    });

    clearPendingProbeWell(sessionId, slotName, wellName, runId);

    const updated =
      state.liquid_tracking?.containers?.[containerKey] ||
      state.liquid_tracking?.sources?.[containerKey] ||
      {};
    const observedPresenceMismatch =
      (expectedPresence === true || expectedPresence === false) &&
      (observedPresence === true || observedPresence === false) &&
      expectedPresence !== observedPresence;

    const result = {
      data: {
        trust_level: updated.trust_level || "observed",
        volume_ul: volumeUl,
        method,
        observed_presence: observedPresence ?? null,
        observed_presence_mismatch: observedPresenceMismatch,
        session_id: sessionId,
        container_key: containerKey,
        observed_at: observedAt,
        observed_run_id: runId,
      },
      stateRevision: state.state_revision,
      sessionId,
    };

    recordToolResultLog({
      toolName: "apply_liquid_probe_results",
      eventKind: "liquid_probe_writeback",
      args,
      result,
      fallbackSessionId: sessionId,
      fallbackStatus: "pass",
      summary: `Applied live probe writeback for ${containerKey} (${method}).`,
      data: result.data,
    });

    return result;
  },

  async get_liquid_source_map(args) {
    const sessionId = args.session_id || DEFAULT_SESSION_ID;
    const sessionState = readSessionState(sessionId);
    const sourcesByKey = sessionState.liquid_tracking?.sources || {};
    const slotFilter = args.slot_name ? String(args.slot_name).trim().toUpperCase() : null;
    const wellFilter = args.well_name ? String(args.well_name).trim().toUpperCase() : null;
    const entries = Object.entries(sourcesByKey)
      .filter(([, source]) => {
        if (slotFilter && source.slot_name !== slotFilter) {
          return false;
        }
        if (wellFilter && source.well_name !== wellFilter) {
          return false;
        }
        return true;
      })
      .map(([key, source]) => ({ key, ...source }))
      .sort((left, right) => left.key.localeCompare(right.key));

    return {
      data: {
        sources: entries,
        source_count: entries.length,
        liquid_tracking: sessionState.liquid_tracking || { sources: {} },
      },
      stateRevision: sessionState.state_revision,
      sessionId,
    };
  },

  async summarize_liquid_source_map(args) {
    const sessionId = args.session_id || DEFAULT_SESSION_ID;
    const sessionState = readSessionState(sessionId);
    const slotName = args.slot_name || args.slotName || null;
    const summary = buildLiquidSourceIdentityMetadataSummary(
      sessionState.liquid_tracking?.sources || {},
      { slotName },
    );
    const result = {
      data: {
        ...summary,
        slot_filter: slotName ? String(slotName).trim().toUpperCase() : null,
        record_liquid_source_map_draft: {
          session_id: sessionId,
          ...summary.record_liquid_source_map_draft,
        },
      },
      stateRevision: sessionState.state_revision,
      sessionId,
    };

    recordToolResultLog({
      toolName: "summarize_liquid_source_map",
      eventKind: "source_map_readiness",
      args,
      result,
      fallbackSessionId: sessionId,
      fallbackStatus: result.data.ready_for_semantic_recovery ? "pass" : "warn",
      summary: result.data.ready_for_semantic_recovery
        ? "Liquid source map has specific identity metadata for expected-present sources."
        : "Liquid source map is not ready for semantic recovery; expected-present source identity metadata is incomplete.",
      data: {
        slot_filter: result.data.slot_filter,
        source_count: result.data.source_count,
        expected_present_count: result.data.expected_present_count,
        expected_absent_count: result.data.expected_absent_count,
        unknown_presence_count: result.data.unknown_presence_count,
        incomplete_expected_present_count: result.data.incomplete_expected_present_count,
        ready_for_semantic_recovery: result.data.ready_for_semantic_recovery,
        incomplete_expected_present_sources: result.data.incomplete_expected_present_sources,
        record_liquid_source_map_template: result.data.record_liquid_source_map_template,
        record_liquid_source_map_draft: {
          session_id: sessionId,
          ...result.data.record_liquid_source_map_draft,
        },
        operator_action: result.data.operator_action,
      },
    });

    return result;
  },

  async validate_virtual_lab_state_steps(args) {
    const sessionId = args.session_id || DEFAULT_SESSION_ID;
    const initialState = args.initial_state || readSessionState(sessionId);
    const validation = validateVirtualLabStateSteps(initialState, args.steps || []);
    return {
      data: {
        ok: validation.ok,
        violation_count: validation.violations.length,
        violations: validation.violations,
        final_state: validation.state,
        no_robot_motion: true,
        persisted: false,
      },
      stateRevision: initialState.state_revision ?? null,
      sessionId: initialState.session_id || sessionId,
    };
  },

  async list_recovery_playbooks(args) {
    const includeMotion = args.include_motion !== false;
    const playbooks = listRecoveryPlaybooks({ includeMotion });
    return {
      data: {
        playbooks,
        playbook_count: playbooks.length,
        include_motion: includeMotion,
        no_robot_motion: true,
      },
    };
  },

  async plan_liquid_source_substitution(args) {
    const sessionId = args.session_id || DEFAULT_SESSION_ID;
    const sessionState = readSessionState(sessionId);
    const plan = buildLiquidSourceSubstitutionPlan({
      sessionState,
      failedSourceKey: args.failed_source_key,
      failedSlotName: args.failed_slot_name,
      failedWellName: args.failed_well_name,
      preferredSourceKey: args.preferred_source_key,
    });
    const result = {
      data: plan,
      stateRevision: sessionState.state_revision,
      sessionId,
    };

    recordToolResultLog({
      toolName: "plan_liquid_source_substitution",
      eventKind: "liquid_source_substitution_plan",
      args,
      result,
      fallbackSessionId: sessionId,
      fallbackStatus: plan.status === "planned" ? "pass" : "blocked",
      summary: plan.selected_source_key
        ? `Liquid source substitution planned from ${plan.failed_source_key} to ${plan.selected_source_key}.`
        : `Liquid source substitution blocked for ${plan.failed_source_key || "unknown source"}.`,
      data: {
        status: plan.status,
        failed_source_key: plan.failed_source_key,
        selected_source_key: plan.selected_source_key,
        candidate_count: plan.candidate_count,
        ready_for_registered_executor: plan.ready_for_registered_executor,
        auto_resume_eligible: plan.auto_resume_eligible,
        auto_resume_blocker: plan.auto_resume_blocker,
        blocked_reason: plan.blocked_reason,
        required_next_step: plan.required_next_step,
        no_robot_motion: plan.no_robot_motion,
        playbook: plan.playbook,
        semantic_invariants: plan.semantic_invariants,
        patch: plan.patch,
      },
    });

    return result;
  },

  async generate_liquid_source_substitution_protocol(args) {
    const sessionId = args.session_id || DEFAULT_SESSION_ID;
    const sessionState = readSessionState(sessionId);
    const previewPlan = buildLiquidSourceSubstitutionPlan({
      sessionState,
      failedSourceKey: args.failed_source_key,
      failedSlotName: args.failed_slot_name,
      failedWellName: args.failed_well_name,
      preferredSourceKey: args.preferred_source_key,
    });
    const outputPath = resolveLiquidSubstitutionProtocolOutputPath(
      args,
      previewPlan.failed_source_key || args.failed_source_key,
      previewPlan.selected_source_key,
    );
    const generated = generateLiquidSourceSubstitutionValidationProtocol({
      sessionState,
      failedSourceKey: args.failed_source_key,
      failedSlotName: args.failed_slot_name,
      failedWellName: args.failed_well_name,
      preferredSourceKey: args.preferred_source_key,
      pipetteName: args.pipette_name,
      mount: args.mount,
      tiprackLoadName: args.tiprack_load_name,
      tiprackSlot: args.tiprack_slot,
      outputPath,
      protocolOptions: {
        apiLevel: args.api_level || "2.24",
        robotType: args.robot_type || "Flex",
        tiprackNamespace: args.tiprack_namespace || "opentrons",
        tiprackVersion: args.tiprack_version ?? 1,
        labwareNamespace: args.labware_namespace || "opentrons",
        labwareVersion: args.labware_version ?? 1,
        trashSlot: args.trash_slot || null,
      },
    });
    const result = {
      data: {
        generated_protocol_path: generated.output_path,
        protocol_source: generated.protocol_source,
        plan: generated.plan,
        validation_protocol: generated.validation_protocol,
        next_required_gates: [
          "simulate_protocol",
          "live_liquid_recovery_gate",
          "run_protocol_only_after_operator_opt_in",
        ],
      },
      stateRevision: sessionState.state_revision,
      sessionId,
    };

    recordToolResultLog({
      toolName: "generate_liquid_source_substitution_protocol",
      eventKind: "liquid_source_substitution_protocol",
      args: { ...args, output_path: generated.output_path },
      result,
      fallbackSessionId: sessionId,
      fallbackStatus: "generated",
      summary: `Liquid source substitution validation protocol generated at ${generated.output_path}.`,
      data: {
        generated_protocol_path: generated.output_path,
        failed_source_key: generated.plan.failed_source_key,
        selected_source_key: generated.plan.selected_source_key,
        candidate_count: generated.plan.candidate_count,
        no_aspirate_or_dispense: generated.validation_protocol.no_aspirate_or_dispense,
        liquid_guard_analysis: generated.validation_protocol.liquid_guard_analysis,
        semantic_invariants: generated.validation_protocol.semantic_invariants,
        next_required_gates: result.data.next_required_gates,
      },
    });

    return result;
  },

  async prepare_liquid_source_substitution_recovery(args) {
    const sessionId = args.session_id || DEFAULT_SESSION_ID;
    const sessionState = readSessionState(sessionId);
    const previewPlan = buildLiquidSourceSubstitutionPlan({
      sessionState,
      failedSourceKey: args.failed_source_key,
      failedSlotName: args.failed_slot_name,
      failedWellName: args.failed_well_name,
      preferredSourceKey: args.preferred_source_key,
    });
    const protocolOutputPath = args.output_protocol_path
      ? path.resolve(args.output_protocol_path)
      : resolveLiquidSubstitutionProtocolOutputPath(
          {},
          previewPlan.failed_source_key || args.failed_source_key,
          previewPlan.selected_source_key || args.preferred_source_key,
        );
    const generated = generateLiquidSourceSubstitutionValidationProtocol({
      sessionState,
      failedSourceKey: args.failed_source_key,
      failedSlotName: args.failed_slot_name,
      failedWellName: args.failed_well_name,
      preferredSourceKey: args.preferred_source_key,
      pipetteName: args.pipette_name,
      mount: args.mount,
      tiprackLoadName: args.tiprack_load_name,
      tiprackSlot: args.tiprack_slot,
      outputPath: protocolOutputPath,
      protocolOptions: {
        apiLevel: args.api_level || "2.24",
        robotType: args.robot_type || "Flex",
        tiprackNamespace: args.tiprack_namespace || "opentrons",
        tiprackVersion: args.tiprack_version ?? 1,
        labwareNamespace: args.labware_namespace || "opentrons",
        labwareVersion: args.labware_version ?? 1,
        trashSlot: args.trash_slot || null,
      },
    });
    const simulation = await TOOL_HANDLERS.simulate_protocol({
      protocol_path: generated.output_path,
      ...(args.python_executable ? { python_executable: args.python_executable } : {}),
      max_log_chars: 12000,
    });
    const parsed = await TOOL_HANDLERS.parse_simulation_output({
      simulation_output_json: JSON.stringify(simulation.data),
    });
    const simulationParse = parsed.data;
    const semanticInvariants = validateLiquidSourceSubstitutionInvariants({
      plan: generated.plan,
      validationProtocol: generated.validation_protocol,
      simulationParse,
      liveGatePassed: false,
      operatorOptIn: false,
      liveExecutionAllowed: false,
      liveProtocolRunAllowed: false,
    });
    const prepared =
      simulationParse?.status === "passed" &&
      semanticInvariants.experiment_intent_violation_count === 0;
    const bundleOutputPath = resolveLiquidSubstitutionRecoveryBundleOutputPath(
      args,
      generated.plan.failed_source_key,
      generated.plan.selected_source_key,
    );
    const recoveryBundle = {
      status: prepared ? "prepared" : "blocked",
      playbook: LIQUID_SOURCE_SUBSTITUTION_PLAYBOOK_ID,
      playbook_contract: generated.plan.playbook,
      session_id: sessionId,
      state_revision: sessionState.state_revision,
      failed_source_key: generated.plan.failed_source_key,
      selected_source_key: generated.plan.selected_source_key,
      generated_protocol_path: generated.output_path,
      no_robot_motion: true,
      no_aspirate_or_dispense: generated.validation_protocol.no_aspirate_or_dispense,
      plan: generated.plan,
      validation_protocol: generated.validation_protocol,
      semantic_invariants: semanticInvariants,
      simulation: {
        ok: simulation.data?.ok ?? null,
        status: simulationParse?.status || null,
        issue_count: simulationParse?.issue_count ?? null,
        parsed: simulationParse,
      },
      execution: {
        registered_executor: LIQUID_SOURCE_SUBSTITUTION_PLAYBOOK_ID,
        fixed_script_prepared: prepared,
        auto_resume_eligible: prepared && generated.plan.auto_resume_eligible === true,
        live_execution_allowed: false,
        live_protocol_run_allowed: false,
        experiment_intent_violation_count: semanticInvariants.experiment_intent_violation_count,
        semantic_gate_blocker_count: semanticInvariants.gate_blocker_count,
        semantic_invariant_status: semanticInvariants.status,
        next_tool: prepared ? "live_liquid_recovery_gate" : "inspect_simulation_output",
        required_next_gates: [
          "live_liquid_recovery_gate",
          "run_protocol_only_after_operator_opt_in",
        ],
        blocked_reason: prepared
          ? "live_gate_and_operator_opt_in_required_before_any_robot_motion"
          : semanticInvariants.experiment_intent_violation_count > 0
            ? "experiment_intent_invariant_failed"
            : simulationParse?.primary_issue?.category || simulationParse?.status || "simulation_failed",
      },
    };

    fs.mkdirSync(path.dirname(bundleOutputPath), { recursive: true });
    fs.writeFileSync(bundleOutputPath, `${JSON.stringify(recoveryBundle, null, 2)}\n`);

    const result = {
      data: {
        ...recoveryBundle,
        output_path: bundleOutputPath,
      },
      stateRevision: sessionState.state_revision,
      sessionId,
    };

    const logEntry = recordToolResultLog({
      toolName: "prepare_liquid_source_substitution_recovery",
      eventKind: "liquid_source_substitution_recovery_bundle",
      args: {
        ...args,
        output_path: bundleOutputPath,
        output_protocol_path: generated.output_path,
      },
      result,
      fallbackSessionId: sessionId,
      fallbackStatus: recoveryBundle.status,
      summary: prepared
        ? `Liquid source substitution recovery prepared for ${generated.plan.failed_source_key} -> ${generated.plan.selected_source_key}.`
        : `Liquid source substitution recovery blocked for ${generated.plan.failed_source_key || "unknown source"}.`,
      data: {
        output_path: bundleOutputPath,
        generated_protocol_path: generated.output_path,
        failed_source_key: generated.plan.failed_source_key,
        selected_source_key: generated.plan.selected_source_key,
        playbook: recoveryBundle.playbook,
        fixed_script_prepared: prepared,
        no_robot_motion: true,
        no_aspirate_or_dispense: generated.validation_protocol.no_aspirate_or_dispense,
        liquid_guard_analysis: generated.validation_protocol.liquid_guard_analysis,
        semantic_invariants: recoveryBundle.semantic_invariants,
        experiment_intent_violation_count:
          recoveryBundle.execution.experiment_intent_violation_count,
        semantic_gate_blocker_count: recoveryBundle.execution.semantic_gate_blocker_count,
        semantic_invariant_status: recoveryBundle.execution.semantic_invariant_status,
        simulation_status: simulationParse?.status || null,
        simulation_issue_count: simulationParse?.issue_count ?? null,
        auto_resume_eligible: recoveryBundle.execution.auto_resume_eligible,
        live_execution_allowed: false,
        live_protocol_run_allowed: false,
        next_tool: recoveryBundle.execution.next_tool,
        blocked_reason: recoveryBundle.execution.blocked_reason,
        required_next_gates: recoveryBundle.execution.required_next_gates,
      },
    });
    result.data.result_log_entry_id = logEntry?.entry_id || null;
    recoveryBundle.result_log_entry_id = result.data.result_log_entry_id;
    fs.writeFileSync(bundleOutputPath, `${JSON.stringify({ ...recoveryBundle, output_path: bundleOutputPath }, null, 2)}\n`);

    return result;
  },

  async is_home_safe(args) {
    const robotStatusResult = await readRobotStatus(args);
    const sessionId = resolveSessionId(args, robotStatusResult);
    const sessionState = readSessionState(sessionId);
    const homeSafety = buildHomeSafetyResult({
      robotStatusSnapshot: robotStatusResult.data,
      sessionState,
    });

    return {
      data: homeSafety,
      hardwareSnapshot: {
        ...robotStatusResult.hardwareSnapshot,
      },
      stateRevision: sessionState.state_revision,
      sessionId,
    };
  },

  async reconcile_state(args) {
    const [robotStatusResult, moduleStatusResult, runContext] = await Promise.all([
      readRobotStatus(args),
      readModuleStatus(args),
      readAnyContext(args),
    ]);
    const sessionId = resolveSessionId(args, robotStatusResult);
    const observedDeckState = buildObservedDeckState({
      deckConfiguration: robotStatusResult.hardwareSnapshot.deck_configuration,
      modules: moduleStatusResult.hardwareSnapshot.modules,
      run: runContext.run,
    });

    let reconciliation;
    const { state } = mutateSessionState(sessionId, sessionState => {
      reconciliation = buildReconciliationResult({
        sessionState,
        robotStatusSnapshot: robotStatusResult.data,
        moduleStatusSnapshot: moduleStatusResult.data,
        observedDeckState,
        observedLiquidTracking: args.observed_liquid_tracking ||
          (Array.isArray(args.observed_liquid_containers)
            ? { containers: Object.fromEntries(args.observed_liquid_containers.map((container, index) => [
                container.container_key ||
                  container.containerKey ||
                  container.key ||
                  (container.slot_name || container.slotName
                    ? `${String(container.slot_name || container.slotName).toUpperCase()}.${String(container.well_name || container.wellName || "").toUpperCase()}`
                    : `observed-${index}`),
                container,
              ])) }
            : null),
        run: runContext.run,
      });
      applyObservedDeckToSessionState(sessionState, reconciliation.proposed_commit);
      const homeSafety = buildHomeSafetyResult({
        robotStatusSnapshot: robotStatusResult.data,
        sessionState,
      });
      reconciliation.proposed_commit.cleanup.auto_home_allowed = homeSafety.auto_home_allowed;
      reconciliation.proposed_commit.cleanup.pending_actions = homeSafety.minimum_cleanup_actions;
      sessionState.cleanup.auto_home_allowed = homeSafety.auto_home_allowed;
      sessionState.cleanup.pending_actions = homeSafety.minimum_cleanup_actions;
      return sessionState;
    });

    const result = {
      data: reconciliation,
      hardwareSnapshot: {
        ...robotStatusResult.hardwareSnapshot,
        ...moduleStatusResult.hardwareSnapshot,
        run: runContext.run || null,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: runContext.runId || null,
    };
    recordToolResultLog({
      toolName: "reconcile_state",
      eventKind: "reconciliation",
      args,
      result,
      fallbackSessionId: sessionId,
      summary:
        reconciliation?.diffs?.length > 0
          ? `Reconciliation found ${reconciliation.diffs.length} diff(s).`
          : "Reconciliation found no actionable deck diffs.",
      data: {
        diff_count: Array.isArray(reconciliation?.diffs) ? reconciliation.diffs.length : 0,
        escalate_to_human: reconciliation?.escalate_to_human || false,
        needs_reconciliation: reconciliation?.proposed_commit?.needs_reconciliation ?? false,
        auto_home_allowed: reconciliation?.proposed_commit?.cleanup?.auto_home_allowed ?? null,
      },
    });
    return result;
  },

  async suggest_recovery_action(args) {
    const [robotStatusResult, moduleStatusResult, runContext] = await Promise.all([
      readRobotStatus(args),
      readModuleStatus(args),
      readAnyContext(args, { includeCommands: true }),
    ]);
    const sessionId = resolveSessionId(args, robotStatusResult);
    const observedDeckState = buildObservedDeckState({
      deckConfiguration: robotStatusResult.hardwareSnapshot.deck_configuration,
      modules: moduleStatusResult.hardwareSnapshot.modules,
      run: runContext.run,
    });
    const sessionState = readSessionState(sessionId);
    const classification = classifyRecoveryError({
      run: runContext.run,
      commands: runContext.commands,
      moduleStatusSnapshot: moduleStatusResult.data,
      robotStatusSnapshot: robotStatusResult.data,
    });
    const { failedWell, tiprackSlot } = resolveFailedWellAndTiprackSlot({
      args,
      run: runContext.run,
      failedCommand: classification.failed_command,
    });

    let nextTipSuggestion = null;
    let tipBindingClassification = null;
    let stateAfterSuggestion = sessionState;
    if ((args.error_category || classification.error_category) === "TIP_PHYSICALLY_MISSING") {
      tipBindingClassification = resolveTipBindingClassification(args);
      const result = mutateSessionState(sessionId, session => {
        nextTipSuggestion = suggestNextTipWell({
          sessionState: session,
          run: runContext.run,
          tiprackSlots: args.tiprack_slots,
          tiprackSlot,
          failedWell,
          failureStatus: "missing",
        });
        return session;
      });
      stateAfterSuggestion = result.state;
    }

    const reconciliation = buildReconciliationResult({
      sessionState: stateAfterSuggestion,
      robotStatusSnapshot: robotStatusResult.data,
      moduleStatusSnapshot: moduleStatusResult.data,
      observedDeckState,
      run: runContext.run,
    });
    const slotOccupation = args.target_slot
      ? getSlotOccupationSummary({
          slotName: args.target_slot,
          observedDeckState,
          sessionState: stateAfterSuggestion,
        })
      : null;
    const alternativeSlots =
      (args.target_slot || classification.error_category === "DESTINATION_OCCUPIED")
        ? suggestAlternativeSlots({
            observedDeckState,
            sessionState: stateAfterSuggestion,
            targetSlot: args.target_slot,
          })
        : [];
    const recoverySuggestion = enrichRecoverySuggestion(
      buildRecoverySuggestion({
      errorCategory: args.error_category || classification.error_category,
      errorLeaf: classification.error_leaf,
      run: runContext.run,
      commands: runContext.commands,
      robotStatusSnapshot: robotStatusResult.data,
      moduleStatusSnapshot: moduleStatusResult.data,
      nextTipSuggestion,
      slotOccupation,
      reconciliation,
      alternativeSlots,
      tipBindingMode: tipBindingClassification?.mode || null,
      tipBindingClassification,
      sessionState: stateAfterSuggestion,
      }),
    );
    const actionSummary = buildActionSummary({
      recoverySuggestion,
      nextTipSuggestion,
      run: runContext.run,
    });

    return {
      data: {
        action_summary: actionSummary,
        classification,
        recovery: recoverySuggestion,
        next_tip_suggestion: nextTipSuggestion,
        tip_binding_classification: tipBindingClassification,
        slot_occupation: slotOccupation,
        alternative_slots: alternativeSlots,
        reconciliation,
      },
      hardwareSnapshot: {
        ...robotStatusResult.hardwareSnapshot,
        ...moduleStatusResult.hardwareSnapshot,
        run: runContext.run || null,
        commands: runContext.commands || null,
      },
      stateRevision: stateAfterSuggestion.state_revision,
      sessionId,
      runId: runContext.runId || null,
    };
  },

  async parse_error(args) {
    const [robotStatusResult, moduleStatusResult, contextResult] = await Promise.all([
      readRobotStatus(args),
      readModuleStatus(args),
      readAnyContext(args, { includeCommands: true, pageLength: args.page_length ?? 20 }),
    ]);
    const sessionId = resolveSessionId(args, robotStatusResult);
    const parsed = parseRuntimeError({
      run: contextResult.run,
      commands: contextResult.commands,
      moduleStatusSnapshot: moduleStatusResult.data,
      robotStatusSnapshot: robotStatusResult.data,
    });

    return {
      data: parsed,
      hardwareSnapshot: {
        ...robotStatusResult.hardwareSnapshot,
        ...moduleStatusResult.hardwareSnapshot,
        run: contextResult.run || null,
        commands: contextResult.commands || null,
      },
      stateRevision: readSessionState(sessionId).state_revision,
      sessionId,
      runId: contextResult.runId || null,
    };
  },

  async create_run_context(args) {
    const labwareOffsets = await resolveRunLabwareOffsets(args.robot_ip, args.labware_offsets);
    const request = buildCreateRunContextRequest({
      contextType: args.context_type,
      protocolId: args.protocol_id,
      runTimeParameters: args.run_time_parameters,
      labwareOffsets,
    });
    const created = await requestRobotJson("POST", args.robot_ip, request.path, {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request.body),
    });
    const contextId = readNested(unwrapData(created) || {}, [["id"]], null);
    const [robotStatusResult, moduleStatusResult, contextResult] = await Promise.all([
      readRobotStatus(args),
      readModuleStatus(args),
      readExecutionContext(args.robot_ip, request.contextType, contextId),
    ]);
    const sessionId = resolveContextSessionId(args, robotStatusResult, contextId);

    const { state } = mutateSessionState(sessionId, sessionState => {
      sessionState.last_run_id =
        request.contextType === "protocol" ? contextResult.contextId : sessionState.last_run_id;
      if (robotStatusResult.data.health_summary.robot_serial) {
        sessionState.robot_serial = robotStatusResult.data.health_summary.robot_serial;
      }
      return sessionState;
    });

    return {
      data: {
        context_type: request.contextType,
        context_id: contextResult.contextId,
        context: contextResult.detail,
      },
      hardwareSnapshot: {
        ...robotStatusResult.hardwareSnapshot,
        ...moduleStatusResult.hardwareSnapshot,
        context: contextResult.detail,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: deriveContextRunId(request.contextType, contextResult.contextId),
    };
  },

  async load_pipette(args) {
    const contextType = normalizeContextType(args.context_type);
    const commandPayload = buildLoadPipetteCommand({
      pipetteName: args.pipette_name,
      mount: args.mount,
      pipetteId: args.pipette_id,
      tipOverlapNotAfterVersion: args.tip_overlap_not_after_version,
      liquidPresenceDetection: args.liquid_presence_detection,
      intent: args.intent || "setup",
      key: args.key,
    });
    const commandResult = await enqueueAndPollCommand({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
      commandPayload,
      timeoutMs: args.timeout_ms ?? 20000,
      pollIntervalMs: args.poll_interval_ms ?? 500,
    });
    const snapshot = await collectExecutionSnapshot({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
    });
    const sessionId = resolveContextSessionId(args, snapshot.robotStatusResult);

    let reconciliation;
    let homeSafety;
    const { state } = mutateSessionState(sessionId, sessionState => {
      ({ reconciliation, homeSafety } = syncSessionStateFromExecution({
        sessionState,
        robotStatusResult: snapshot.robotStatusResult,
        moduleStatusResult: snapshot.moduleStatusResult,
        contextDetail: snapshot.contextResult.detail,
        contextRunId: deriveContextRunId(contextType, args.context_id),
        forceCommit: true,
      }));
      setPipetteState(sessionState, args.mount, {
        instrument_name: args.pipette_name,
        tip_attached: false,
      });
      return sessionState;
    });

    return {
      data: {
        context_type: contextType,
        context_id: args.context_id,
        command_created: commandResult.created,
        command: commandResult.terminal,
        context: snapshot.contextResult.detail,
        reconciliation,
        home_safety: homeSafety,
      },
      hardwareSnapshot: {
        ...snapshot.robotStatusResult.hardwareSnapshot,
        ...snapshot.moduleStatusResult.hardwareSnapshot,
        context: snapshot.contextResult.detail,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: deriveContextRunId(contextType, args.context_id),
    };
  },

  async drop_attached_tip(args) {
    const contextType = "maintenance";
    const mount = args.mount || "left";
    const sessionId = args.session_id || args.context_id || DEFAULT_SESSION_ID;
    const robotStatusBefore = await readRobotStatus(args);
    const instrument =
      (robotStatusBefore.data?.instruments_summary || []).find(item => item.mount === mount) || null;

    if (!instrument) {
      throw new Error(`drop_attached_tip could not find a pipette on mount ${mount}.`);
    }
    if (instrument.tip_detected !== true) {
      throw new Error(`drop_attached_tip refused: robot_status does not show an attached tip on ${mount}.`);
    }

    const pipetteName = args.pipette_name || instrument.instrument_name;
    if (!pipetteName) {
      throw new Error(`drop_attached_tip could not resolve pipette_name for mount ${mount}.`);
    }

    const timeoutMs = args.timeout_ms ?? 30000;
    const pollIntervalMs = args.poll_interval_ms ?? 500;
    const loadResult = await enqueueAndPollCommand({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
      commandPayload: buildLoadPipetteCommand({
        pipetteName,
        mount,
        pipetteId: args.pipette_id,
        intent: "fixit",
      }),
      timeoutMs,
      pollIntervalMs,
    });
    assertCommandSucceeded(loadResult, "loadPipette cleanup");
    const loadedPipetteId =
      args.pipette_id ||
      readNested(unwrapData(loadResult.terminal) || {}, [["params", "pipetteId"], ["data", "params", "pipetteId"]], null) ||
      readNested(unwrapData(loadResult.terminal) || {}, [["result", "pipetteId"], ["data", "result", "pipetteId"]], null);

    if (!loadedPipetteId) {
      throw new Error("drop_attached_tip could not resolve pipetteId from loadPipette.");
    }

    const alternateDropLocation = args.alternate_drop_location === true;
    const moveToDropResult = await enqueueAndPollCommand({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
      commandPayload: buildMoveToAddressableAreaForDropTipCommand({
        pipetteId: loadedPipetteId,
        intent: "fixit",
        alternateDropLocation,
      }),
      timeoutMs,
      pollIntervalMs,
    });
    assertCommandSucceeded(moveToDropResult, "moveToAddressableAreaForDropTip cleanup");
    const dropResult = await enqueueAndPollCommand({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
      commandPayload: buildDropTipInPlaceCommand({
        pipetteId: loadedPipetteId,
        intent: "fixit",
      }),
      timeoutMs,
      pollIntervalMs,
    });
    assertCommandSucceeded(dropResult, "dropTipInPlace cleanup");

    const snapshot = await collectExecutionSnapshot({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
    });
    const robotStatusAfter = snapshot.robotStatusResult;
    const afterInstrument =
      (robotStatusAfter.data?.instruments_summary || []).find(item => item.mount === mount) || null;
    const tipStillAttached = afterInstrument?.tip_detected === true;

    let reconciliation;
    let homeSafety;
    const { state } = mutateSessionState(sessionId, sessionState => {
      ({ reconciliation, homeSafety } = syncSessionStateFromExecution({
        sessionState,
        robotStatusResult: snapshot.robotStatusResult,
        moduleStatusResult: snapshot.moduleStatusResult,
        contextDetail: snapshot.contextResult.detail,
        contextRunId: null,
        forceCommit: true,
      }));
      setPipetteState(sessionState, mount, {
        instrument_name: pipetteName,
        tip_attached: tipStillAttached,
      });
      const pendingActions = (sessionState.cleanup?.pending_actions || []).filter(
        action => action !== `drop_tip:${mount}`,
      );
      setCleanupState(sessionState, {
        pending_actions: tipStillAttached
          ? uniqueSessionStrings([...pendingActions, `drop_tip:${mount}`])
          : pendingActions,
      });
      homeSafety = buildHomeSafetyResult({
        robotStatusSnapshot: snapshot.robotStatusResult.data,
        sessionState,
      });
      setCleanupState(sessionState, {
        pending_actions: sessionState.cleanup.pending_actions,
        auto_home_allowed: homeSafety.auto_home_allowed,
      });
      return sessionState;
    });

    const result = {
      data: {
        context_type: contextType,
        context_id: args.context_id,
        mount,
        pipette_name: pipetteName,
        pipette_id: loadedPipetteId,
        load_command: loadResult.terminal,
        move_to_drop_command: moveToDropResult.terminal,
        drop_command: dropResult.terminal,
        tip_still_attached: tipStillAttached,
        reconciliation,
        home_safety: homeSafety,
      },
      hardwareSnapshot: {
        ...robotStatusBefore.hardwareSnapshot,
        ...snapshot.robotStatusResult.hardwareSnapshot,
        ...snapshot.moduleStatusResult.hardwareSnapshot,
        context: snapshot.contextResult.detail,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: null,
    };
    recordToolResultLog({
      toolName: "drop_attached_tip",
      eventKind: "cleanup_action",
      args,
      result,
      fallbackSessionId: sessionId,
      summary: tipStillAttached
        ? `Drop attached tip attempted on ${mount}, but robot still reports a tip.`
        : `Dropped attached tip from ${mount}.`,
      data: {
        mount,
        pipette_name: pipetteName,
        tip_still_attached: tipStillAttached,
      },
    });
    return result;
  },

  async load_labware(args) {
    const contextType = normalizeContextType(args.context_type);
    const commandPayload = buildLoadLabwareCommand({
      location: { slotName: args.slot_name },
      loadName: args.load_name,
      namespace: args.namespace,
      version: args.version,
      labwareId: args.labware_id,
      displayName: args.display_name,
      intent: args.intent || "setup",
      key: args.key,
    });
    const commandResult = await enqueueAndPollCommand({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
      commandPayload,
      timeoutMs: args.timeout_ms ?? 20000,
      pollIntervalMs: args.poll_interval_ms ?? 500,
    });
    const snapshot = await collectExecutionSnapshot({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
    });
    const sessionId = resolveContextSessionId(args, snapshot.robotStatusResult);

    let reconciliation;
    let homeSafety;
    const { state } = mutateSessionState(sessionId, sessionState => {
      ({ reconciliation, homeSafety } = syncSessionStateFromExecution({
        sessionState,
        robotStatusResult: snapshot.robotStatusResult,
        moduleStatusResult: snapshot.moduleStatusResult,
        contextDetail: snapshot.contextResult.detail,
        contextRunId: deriveContextRunId(contextType, args.context_id),
        forceCommit: true,
      }));
      if (String(args.load_name).toLowerCase().includes("tiprack")) {
        ensureTiprackState(sessionState, {
          slotName: String(args.slot_name).toUpperCase(),
          loadName: args.load_name,
        });
      }
      return sessionState;
    });

    return {
      data: {
        context_type: contextType,
        context_id: args.context_id,
        command_created: commandResult.created,
        command: commandResult.terminal,
        context: snapshot.contextResult.detail,
        reconciliation,
        home_safety: homeSafety,
      },
      hardwareSnapshot: {
        ...snapshot.robotStatusResult.hardwareSnapshot,
        ...snapshot.moduleStatusResult.hardwareSnapshot,
        context: snapshot.contextResult.detail,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: deriveContextRunId(contextType, args.context_id),
    };
  },

  async validate_labware_name(args) {
    return {
      data: validateLabwareLoadName(args.load_name, {
        limit: args.limit ?? 5,
      }),
    };
  },

  async estimate_tip_budget(args) {
    return {
      data: estimateTipBudget({
        protocol_source: args.protocol_source,
        file_path: args.file_path,
        tip_rack_count: args.tip_rack_count,
        tip_rack_capacity: args.tip_rack_capacity,
      }),
    };
  },

  async inspect_labware_definition(args) {
    return {
      data: inspectLabwareDefinition(args.load_name, {
        limit: args.limit ?? 5,
      }),
    };
  },

  async load_module(args) {
    const contextType = normalizeContextType(args.context_type);
    const commandPayload = buildLoadModuleCommand({
      model: args.module_model,
      location: { slotName: args.slot_name },
      moduleId: args.module_id,
      intent: args.intent || "setup",
      key: args.key,
    });
    const commandResult = await enqueueAndPollCommand({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
      commandPayload,
      timeoutMs: args.timeout_ms ?? 20000,
      pollIntervalMs: args.poll_interval_ms ?? 500,
    });
    const snapshot = await collectExecutionSnapshot({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
    });
    const sessionId = resolveContextSessionId(args, snapshot.robotStatusResult);

    let reconciliation;
    let homeSafety;
    const { state } = mutateSessionState(sessionId, sessionState => {
      ({ reconciliation, homeSafety } = syncSessionStateFromExecution({
        sessionState,
        robotStatusResult: snapshot.robotStatusResult,
        moduleStatusResult: snapshot.moduleStatusResult,
        contextDetail: snapshot.contextResult.detail,
        contextRunId: deriveContextRunId(contextType, args.context_id),
        forceCommit: true,
      }));
      return sessionState;
    });

    return {
      data: {
        context_type: contextType,
        context_id: args.context_id,
        command_created: commandResult.created,
        command: commandResult.terminal,
        loaded_module_id: readNested(unwrapData(commandResult.terminal) || {}, [["result", "moduleId"]], null),
        context: snapshot.contextResult.detail,
        reconciliation,
        home_safety: homeSafety,
      },
      hardwareSnapshot: {
        ...snapshot.robotStatusResult.hardwareSnapshot,
        ...snapshot.moduleStatusResult.hardwareSnapshot,
        context: snapshot.contextResult.detail,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: deriveContextRunId(contextType, args.context_id),
    };
  },

  async control_temperature_module(args) {
    if (args.action === "set_target_temperature") {
      requireNumericArg(args, "celsius", "control_temperature_module");
    }
    const contextType = normalizeContextType(args.context_type);
    const commandPayload = buildTemperatureModuleCommand({
      action: args.action,
      moduleId: args.module_id,
      celsius: args.celsius,
      intent: args.intent || "setup",
      key: args.key,
    });
    const commandResult = await enqueueAndPollCommand({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
      commandPayload,
      timeoutMs: args.timeout_ms ?? 120000,
      pollIntervalMs: args.poll_interval_ms ?? 500,
    });
    const snapshot = await collectExecutionSnapshot({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
    });
    const sessionId = resolveContextSessionId(args, snapshot.robotStatusResult);
    let reconciliation;
    let homeSafety;
    const { state } = mutateSessionState(sessionId, sessionState => {
      ({ reconciliation, homeSafety } = syncSessionStateFromExecution({
        sessionState,
        robotStatusResult: snapshot.robotStatusResult,
        moduleStatusResult: snapshot.moduleStatusResult,
        contextDetail: snapshot.contextResult.detail,
        contextRunId: deriveContextRunId(contextType, args.context_id),
        forceCommit: true,
      }));
      return sessionState;
    });
    return {
      data: {
        module_id: args.module_id,
        action: args.action,
        command_created: commandResult.created,
        command: commandResult.terminal,
        module_status: snapshot.moduleStatusResult.data,
        reconciliation,
        home_safety: homeSafety,
      },
      hardwareSnapshot: {
        ...snapshot.robotStatusResult.hardwareSnapshot,
        ...snapshot.moduleStatusResult.hardwareSnapshot,
        context: snapshot.contextResult.detail,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: deriveContextRunId(contextType, args.context_id),
    };
  },

  async control_heater_shaker(args) {
    if (["set_target_temperature", "wait_for_temperature"].includes(args.action)) {
      if (args.action === "set_target_temperature") {
        requireNumericArg(args, "celsius", "control_heater_shaker");
      }
    }
    if (["set_shake_speed", "set_and_wait_for_shake_speed"].includes(args.action)) {
      requireNumericArg(args, "rpm", "control_heater_shaker");
    }
    const contextType = normalizeContextType(args.context_type);
    const commandOptions = {
      moduleId: args.module_id,
      celsius: args.celsius,
      rpm: args.rpm,
      intent: args.intent || "setup",
      key: args.key,
    };
    const enqueueHeaterShakerAction = action =>
      enqueueAndPollCommand({
        robotIp: args.robot_ip,
        contextType,
        contextId: args.context_id,
        commandPayload: buildHeaterShakerCommand({
          ...commandOptions,
          action,
        }),
        timeoutMs: args.timeout_ms ?? 120000,
        pollIntervalMs: args.poll_interval_ms ?? 500,
      });
    let initialLatchStatus = null;
    const preflightCommands = [];
    let retriedAfterLatchClose = false;

    if (args.action === "deactivate_shaker" && args.ensure_latch_closed !== false) {
      const preflightSnapshot = await collectExecutionSnapshot({
        robotIp: args.robot_ip,
        contextType,
        contextId: args.context_id,
      });
      const moduleSnapshot = getModuleSnapshotById(preflightSnapshot.moduleStatusResult, args.module_id);
      initialLatchStatus = moduleSnapshot?.labware_latch_status ?? null;

      if (
        shouldPreflightCloseHeaterShakerLatch({
          action: args.action,
          latchStatus: initialLatchStatus,
          ensureLatchClosed: args.ensure_latch_closed,
        })
      ) {
        const closeResult = await enqueueHeaterShakerAction("close_labware_latch");
        preflightCommands.push(summarizeCommandExecution("close_labware_latch", closeResult));
      }
    }

    let commandResult = await enqueueHeaterShakerAction(args.action);
    const firstAttemptFailed =
      String(readNested(unwrapData(commandResult.terminal) || {}, [["status"]], "")).toLowerCase() ===
      "failed";
    const firstAttemptError = readCommandErrorDetail(commandResult);

    if (
      args.action === "deactivate_shaker" &&
      args.ensure_latch_closed !== false &&
      firstAttemptFailed &&
      shouldRetryHeaterShakerAfterLatchError(firstAttemptError) &&
      preflightCommands.length === 0 &&
      (initialLatchStatus == null || isHeaterShakerLatchClosed(initialLatchStatus))
    ) {
      const closeResult = await enqueueHeaterShakerAction("close_labware_latch");
      preflightCommands.push(
        summarizeCommandExecution("close_labware_latch_retry_after_precondition_error", closeResult),
      );
      retriedAfterLatchClose = true;
      commandResult = await enqueueHeaterShakerAction(args.action);
    }

    const snapshot = await collectExecutionSnapshot({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
    });
    const sessionId = resolveContextSessionId(args, snapshot.robotStatusResult);
    let reconciliation;
    let homeSafety;
    const { state } = mutateSessionState(sessionId, sessionState => {
      ({ reconciliation, homeSafety } = syncSessionStateFromExecution({
        sessionState,
        robotStatusResult: snapshot.robotStatusResult,
        moduleStatusResult: snapshot.moduleStatusResult,
        contextDetail: snapshot.contextResult.detail,
        contextRunId: deriveContextRunId(contextType, args.context_id),
        forceCommit: true,
      }));
      return sessionState;
    });
    return {
      data: {
        module_id: args.module_id,
        action: args.action,
        initial_latch_status: initialLatchStatus,
        preflight_commands: preflightCommands,
        retried_after_latch_close: retriedAfterLatchClose,
        command_created: commandResult.created,
        command: commandResult.terminal,
        module_status: snapshot.moduleStatusResult.data,
        reconciliation,
        home_safety: homeSafety,
      },
      hardwareSnapshot: {
        ...snapshot.robotStatusResult.hardwareSnapshot,
        ...snapshot.moduleStatusResult.hardwareSnapshot,
        context: snapshot.contextResult.detail,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: deriveContextRunId(contextType, args.context_id),
    };
  },

  async control_thermocycler(args) {
    if (["set_block_temperature", "set_lid_temperature"].includes(args.action)) {
      requireNumericArg(args, "celsius", "control_thermocycler");
    }
    if (args.action === "run_profile") {
      requireArrayArg(args, "profile", "control_thermocycler");
    }
    const contextType = normalizeContextType(args.context_type);
    const commandPayload = buildThermocyclerCommand({
      action: args.action,
      moduleId: args.module_id,
      celsius: args.celsius,
      holdTimeSeconds: args.hold_time_seconds,
      blockMaxVolumeUl: args.block_max_volume_ul,
      rampRate: args.ramp_rate,
      profile: args.profile,
      intent: args.intent || "setup",
      key: args.key,
    });
    const commandResult = await enqueueAndPollCommand({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
      commandPayload,
      timeoutMs: args.timeout_ms ?? 120000,
      pollIntervalMs: args.poll_interval_ms ?? 500,
    });
    const snapshot = await collectExecutionSnapshot({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
    });
    const sessionId = resolveContextSessionId(args, snapshot.robotStatusResult);
    let reconciliation;
    let homeSafety;
    const { state } = mutateSessionState(sessionId, sessionState => {
      ({ reconciliation, homeSafety } = syncSessionStateFromExecution({
        sessionState,
        robotStatusResult: snapshot.robotStatusResult,
        moduleStatusResult: snapshot.moduleStatusResult,
        contextDetail: snapshot.contextResult.detail,
        contextRunId: deriveContextRunId(contextType, args.context_id),
        forceCommit: true,
      }));
      return sessionState;
    });
    return {
      data: {
        module_id: args.module_id,
        action: args.action,
        command_created: commandResult.created,
        command: commandResult.terminal,
        module_status: snapshot.moduleStatusResult.data,
        reconciliation,
        home_safety: homeSafety,
      },
      hardwareSnapshot: {
        ...snapshot.robotStatusResult.hardwareSnapshot,
        ...snapshot.moduleStatusResult.hardwareSnapshot,
        context: snapshot.contextResult.detail,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: deriveContextRunId(contextType, args.context_id),
    };
  },

  async move_labware(args) {
    const contextType = normalizeContextType(args.context_type || "maintenance");
    const commandPayload = buildMoveLabwareCommand({
      labwareId: args.labware_id,
      newLocation: { slotName: args.new_slot_name },
      strategy: args.strategy || "usingGripper",
      pickUpOffset: args.pick_up_offset,
      dropOffset: args.drop_offset,
      intent: args.intent,
      key: args.key,
    });
    const commandResult = await enqueueAndPollCommand({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
      commandPayload,
      timeoutMs: args.timeout_ms ?? 30000,
      pollIntervalMs: args.poll_interval_ms ?? 500,
    });
    const snapshot = await collectExecutionSnapshot({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
    });
    const sessionId = resolveContextSessionId(args, snapshot.robotStatusResult);

    let reconciliation;
    let homeSafety;
    const { state } = mutateSessionState(sessionId, sessionState => {
      ({ reconciliation } = syncSessionStateFromExecution({
        sessionState,
        robotStatusResult: snapshot.robotStatusResult,
        moduleStatusResult: snapshot.moduleStatusResult,
        contextDetail: snapshot.contextResult.detail,
        contextRunId: deriveContextRunId(contextType, args.context_id),
        forceCommit: true,
      }));
      const pendingActions = uniqueSessionStrings([
        ...(sessionState.cleanup?.pending_actions || []),
        ...(deriveCleanupPendingActions("moveLabware") || []),
      ]);
      setCleanupState(sessionState, {
        pending_actions: pendingActions,
      });
      homeSafety = buildHomeSafetyResult({
        robotStatusSnapshot: snapshot.robotStatusResult.data,
        sessionState,
      });
      setCleanupState(sessionState, {
        pending_actions: sessionState.cleanup.pending_actions,
        auto_home_allowed: homeSafety.auto_home_allowed,
      });
      return sessionState;
    });

    return {
      data: {
        context_type: contextType,
        context_id: args.context_id,
        command_created: commandResult.created,
        command: commandResult.terminal,
        context: snapshot.contextResult.detail,
        reconciliation,
        home_safety: homeSafety,
      },
      hardwareSnapshot: {
        ...snapshot.robotStatusResult.hardwareSnapshot,
        ...snapshot.moduleStatusResult.hardwareSnapshot,
        context: snapshot.contextResult.detail,
      },
      stateRevision: state.state_revision,
      sessionId,
      runId: deriveContextRunId(contextType, args.context_id),
    };
  },

  async cleanup_motion(args) {
    const contextType = "maintenance";
    const timeoutMs = args.timeout_ms ?? 30000;
    const pollIntervalMs = args.poll_interval_ms ?? 500;
    const sessionId = args.session_id || args.context_id || DEFAULT_SESSION_ID;
    const steps = [];

    const runStep = async commandPayload => {
      const result = await enqueueAndPollCommand({
        robotIp: args.robot_ip,
        contextType,
        contextId: args.context_id,
        commandPayload,
        timeoutMs,
        pollIntervalMs,
      });
      steps.push({
        created: result.created,
        terminal: result.terminal,
      });
      return result;
    };

    await runStep(buildOpenGripperJawCommand({ intent: "setup" }));
    await runStep(
      buildMoveToMaintenancePositionCommand({
        mount: args.mount || "extension",
        maintenancePosition: args.maintenance_position,
        intent: "setup",
      }),
    );

    const preHomeSnapshot = await collectExecutionSnapshot({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
    });

    let homeSafety;
    let executedHome = false;
    let reconciliation;
    const afterPreHome = mutateSessionState(sessionId, sessionState => {
      ({ reconciliation } = syncSessionStateFromExecution({
        sessionState,
        robotStatusResult: preHomeSnapshot.robotStatusResult,
        moduleStatusResult: preHomeSnapshot.moduleStatusResult,
        contextDetail: preHomeSnapshot.contextResult.detail,
        contextRunId: null,
        forceCommit: true,
      }));
      setCleanupState(sessionState, {
        pending_actions: deriveCleanupPendingActions("calibration/moveToMaintenancePosition") || [],
      });
      homeSafety = buildHomeSafetyResult({
        robotStatusSnapshot: preHomeSnapshot.robotStatusResult.data,
        sessionState,
      });
      setCleanupState(sessionState, {
        pending_actions: sessionState.cleanup.pending_actions,
        auto_home_allowed: homeSafety.auto_home_allowed,
      });
      return sessionState;
    });

    let finalSnapshot = preHomeSnapshot;
    if ((args.allow_home ?? true) && homeSafety.auto_home_allowed) {
      await runStep(
        buildHomeCommand({
          axes: args.home_axes,
          intent: "setup",
        }),
      );
      finalSnapshot = await collectExecutionSnapshot({
        robotIp: args.robot_ip,
        contextType,
        contextId: args.context_id,
      });
      mutateSessionState(sessionId, sessionState => {
        syncSessionStateFromExecution({
          sessionState,
          robotStatusResult: finalSnapshot.robotStatusResult,
          moduleStatusResult: finalSnapshot.moduleStatusResult,
          contextDetail: finalSnapshot.contextResult.detail,
          contextRunId: null,
          forceCommit: true,
        });
        setCleanupState(sessionState, {
          pending_actions: [],
        });
        const postHomeSafety = buildHomeSafetyResult({
          robotStatusSnapshot: finalSnapshot.robotStatusResult.data,
          sessionState,
        });
        setCleanupState(sessionState, {
          pending_actions: sessionState.cleanup.pending_actions,
          auto_home_allowed: postHomeSafety.auto_home_allowed,
        });
        homeSafety = postHomeSafety;
        return sessionState;
      });
      executedHome = true;
    }

    const finalState = readSessionState(sessionId);

    return {
      data: {
        context_type: contextType,
        context_id: args.context_id,
        executed_steps: steps,
        executed_home: executedHome,
        reconciliation,
        home_safety: homeSafety,
        context: finalSnapshot.contextResult.detail,
      },
      hardwareSnapshot: {
        ...finalSnapshot.robotStatusResult.hardwareSnapshot,
        ...finalSnapshot.moduleStatusResult.hardwareSnapshot,
        context: finalSnapshot.contextResult.detail,
      },
      stateRevision: finalState.state_revision,
      sessionId,
      runId: null,
    };
  },

  async camera_status(args) {
    const cameraStatusResult = await readCameraStatus(args);
    return {
      data: cameraStatusResult.data,
      hardwareSnapshot: cameraStatusResult.hardwareSnapshot,
    };
  },

  async configure_camera(args) {
    const shouldUpdateCameraState =
      typeof args.camera_enabled === "boolean" ||
      typeof args.live_stream_enabled === "boolean" ||
      typeof args.error_recovery_camera_enabled === "boolean";
    const imageSettings = buildCameraImageSettings(args);
    const shouldUpdateImageSettings = Object.keys(imageSettings).length > 0;

    if (!shouldUpdateCameraState && !shouldUpdateImageSettings) {
      throw new Error(
        "configure_camera requires at least one camera state field or one image setting field.",
      );
    }

    let cameraStateUpdate = null;
    let imageSettingsUpdate = null;

    if (shouldUpdateCameraState) {
      try {
        cameraStateUpdate = await requestRobotJson("POST", args.robot_ip, "/camera", {
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildCameraControlBody(args)),
        });
      } catch (error) {
        throw rewriteVisionEndpointError(error, "/camera");
      }
    }

    if (shouldUpdateImageSettings) {
      try {
        imageSettingsUpdate = await requestRobotJson(
          "POST",
          args.robot_ip,
          "/camera/cameraSettings",
          {
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(buildCameraImageSettingsBody(args)),
          },
        );
      } catch (error) {
        throw rewriteVisionEndpointError(error, "/camera/cameraSettings");
      }
    }

    const cameraStatusResult = await readCameraStatus(args);
    return {
      data: {
        camera_status: cameraStatusResult.data,
        applied_state_update: shouldUpdateCameraState ? buildCameraControlBody(args).data : null,
        applied_image_settings: shouldUpdateImageSettings ? imageSettings : null,
        update_results: {
          camera: cameraStateUpdate,
          image_settings: imageSettingsUpdate,
        },
      },
      hardwareSnapshot: {
        ...cameraStatusResult.hardwareSnapshot,
        camera_update: cameraStateUpdate,
        camera_settings_update: imageSettingsUpdate,
      },
    };
  },

  async capture_preview_image(args) {
    const imageSettings = buildCameraImageSettings(args);
    let previewResult;
    try {
      previewResult = await requestRobotBytes("POST", args.robot_ip, "/camera/capturePreviewImage", {
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: imageSettings }),
      });
    } catch (error) {
      throw rewriteVisionEndpointError(error, "/camera/capturePreviewImage");
    }
    const outputPath = resolvePreviewOutputPath(args, previewResult.contentType);
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, previewResult.data);

    const cameraStatusResult = await readCameraStatus(args);
    return {
      data: {
        saved_to: outputPath,
        bytes: previewResult.data.length,
        content_type: previewResult.contentType,
        image_settings: imageSettings,
        camera_status: cameraStatusResult.data,
      },
      hardwareSnapshot: {
        ...cameraStatusResult.hardwareSnapshot,
      },
    };
  },

  async capture_run_image(args) {
    const contextType = normalizeContextType(args.context_type || "maintenance");
    const captureParams = buildCaptureImageParams(args);
    const commandPayload = buildCaptureImageCommand({
      ...captureParams,
      intent: args.intent || "setup",
      key: args.key,
    });
    const commandResult = await enqueueAndPollCommand({
      robotIp: args.robot_ip,
      contextType,
      contextId: args.context_id,
      commandPayload,
      timeoutMs: args.timeout_ms ?? 30000,
      pollIntervalMs: args.poll_interval_ms ?? 500,
    });
    const terminalCommand = unwrapData(commandResult.terminal) || {};
    const fileId = readNested(terminalCommand, [["result", "fileId"]], null);
    if (!fileId) {
      throw new Error(
        "capture_run_image command reached terminal state but did not return a fileId. On the current robot software, maintenance-context image capture may succeed without exposing a downloadable data file.",
      );
    }

    const [fileInfo, downloadResult, snapshot, cameraStatusResult] = await Promise.all([
      readDataFileInfo(args.robot_ip, fileId),
      downloadDataFile(args.robot_ip, fileId),
      collectExecutionSnapshot({
        robotIp: args.robot_ip,
        contextType,
        contextId: args.context_id,
        includeCommands: true,
      }),
      readCameraStatus(args),
    ]);
    const outputPath = resolveCapturedImageOutputPath(args, {
      contentType: downloadResult.contentType,
      fileName: readNested(unwrapData(fileInfo) || {}, [["filename"]], captureParams.fileName),
    });
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, downloadResult.data);

    return {
      data: {
        context_type: contextType,
        context_id: args.context_id,
        command_created: commandResult.created,
        command: commandResult.terminal,
        file_id: fileId,
        file_info: unwrapData(fileInfo) || fileInfo,
        saved_to: outputPath,
        bytes: downloadResult.data.length,
        content_type: downloadResult.contentType,
        camera_status: cameraStatusResult.data,
        module_status: snapshot.moduleStatusResult.data,
      },
      hardwareSnapshot: {
        ...cameraStatusResult.hardwareSnapshot,
        ...snapshot.robotStatusResult.hardwareSnapshot,
        ...snapshot.moduleStatusResult.hardwareSnapshot,
        context: snapshot.contextResult.detail,
      },
      sessionId: resolveContextSessionId(args, snapshot.robotStatusResult),
      runId: deriveContextRunId(contextType, args.context_id),
    };
  },

  async list_data_files(args) {
    const dataFiles = await requestRobotJson("GET", args.robot_ip, "/dataFiles");
    return {
      data: {
        data_files: unwrapData(dataFiles) || dataFiles,
      },
    };
  },

  async download_data_file(args) {
    const [fileInfo, downloadResult] = await Promise.all([
      readDataFileInfo(args.robot_ip, args.data_file_id),
      downloadDataFile(args.robot_ip, args.data_file_id),
    ]);
    const normalizedInfo = unwrapData(fileInfo) || {};
    const fallbackName = normalizedInfo.filename || normalizedInfo.name || args.data_file_id;
    const outputPath = args.output_path
      ? path.resolve(args.output_path)
      : path.join(
          DEFAULT_CAMERA_ARTIFACT_DIR,
          path.extname(fallbackName)
            ? path.basename(fallbackName)
            : `${path.basename(fallbackName)}.${contentTypeToExtension(downloadResult.contentType)}`,
        );
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, downloadResult.data);
    return {
      data: {
        data_file_id: args.data_file_id,
        file_info: normalizedInfo,
        saved_to: outputPath,
        bytes: downloadResult.data.length,
        content_type: downloadResult.contentType,
      },
    };
  },

  async analyze_image_with_ark(args) {
    const result = await analyzeImageWithArk({
      imagePath: args.image_path,
      apiKey: args.api_key,
      baseUrl: args.base_url,
      modelEndpoint: args.model_endpoint,
      prompt: args.prompt,
      expectedLayout: args.expected_layout,
      maxOutputTokens: args.max_output_tokens,
    });

    return {
      data: result,
    };
  },

  async analyze_image_with_kimi(args) {
    const { dataUrl, imagePath, mimeType } = buildImageDataUrl(args.image_path);
    const apiKey = resolveSiliconFlowApiKey({ apiKey: args.api_key });
    const prompt = buildDeckPhotoAnalysisPrompt({
      prompt: args.prompt,
      expectedLayout: args.expected_layout,
    });
    const baseRequest = {
      model: args.model || "Pro/moonshotai/Kimi-K2.5",
      imageDataUrl: dataUrl,
      prompt,
      detail: args.detail || "high",
      systemPrompt: args.system_prompt || null,
      temperature: args.temperature ?? 0.1,
      maxTokens: args.max_tokens ?? 1200,
    };
    const body = buildSiliconFlowChatBody({
      ...baseRequest,
      jsonMode: true,
    });
    let response = await callSiliconFlowChatCompletion({
      apiKey,
      baseUrl: args.base_url || "https://api.siliconflow.cn/v1",
      body,
    });
    let assistantText = extractAssistantText(response.json);
    let parsed = parseAssistantJson(assistantText);
    let fallbackUsed = false;

    if (!parsed || (typeof assistantText === "string" && assistantText.trim().length < 10)) {
      const fallbackBody = buildSiliconFlowChatBody({
        ...baseRequest,
        prompt: `${prompt}\n如果你不能稳定输出 JSON，也请先给出清晰中文分析，并尽量包含一个 JSON 对象。`,
        jsonMode: false,
      });
      response = await callSiliconFlowChatCompletion({
        apiKey,
        baseUrl: args.base_url || "https://api.siliconflow.cn/v1",
        body: fallbackBody,
      });
      assistantText = extractAssistantText(response.json);
      parsed = parseAssistantJson(assistantText);
      fallbackUsed = true;
    }

    return {
      data: {
        image_path: imagePath,
        mime_type: mimeType,
        model: body.model,
        trace_id: response.traceId,
        prompt,
        fallback_used: fallbackUsed,
        parsed_result: parsed,
        raw_text: assistantText,
        usage: response.json?.usage || null,
      },
    };
  },

  async vision_check(args) {
    const annotatedDir = args.annotated_output_dir
      ? path.resolve(args.annotated_output_dir)
      : DEFAULT_VISION_ANNOTATED_DIR;
    fs.mkdirSync(annotatedDir, { recursive: true });

    const result = await runVisionCheck({
      mode: args.mode || "deck",
      imagePath: args.image_path,
      expectedLayout: args.expected_layout,
      referenceImagePath: args.reference_image_path,
      confThreshold: args.conf_threshold ?? 0.25,
      weights: args.weights,
      useTextPrompts: args.use_text_prompts,
      annotatedOutputDir: annotatedDir,
      pythonExecutable: args.python_executable,
      deckCornersNorm: args.deck_corners_norm,
      loadLabelsSidecar: args.load_labels_sidecar,
      classPrompts: args.class_prompts,
      canonicalLabels: args.canonical_labels,
    });

    return {
      data: result,
    };
  },

  async deck_vision_check(args) {
    if (!isPreflightVisionEnabled()) {
      return {
        data: {
          skipped: true,
          reason: "OPENTRONS_PREFLIGHT_VISION=off",
          subphase: "deck_vision",
          consensus: {
            status: "passed",
            summary: "Deck vision preflight skipped by environment flag.",
            recommended_next_actions: ["list_critical_probe_targets"],
          },
        },
      };
    }

    const captureResult = await TOOL_HANDLERS.capture_preview_image({
      robot_ip: args.robot_ip,
      output_path: args.output_path,
    });
    const imagePath = captureResult.data.saved_to;
    const yoloResult = (
      await TOOL_HANDLERS.vision_check({
        mode: "deck",
        image_path: imagePath,
        expected_layout: args.expected_layout,
        conf_threshold: args.conf_threshold,
        weights: args.weights,
      })
    ).data;

    const escalation = shouldEscalateToVlm(yoloResult, { force: Boolean(args.force_vlm) });
    const provider = resolveVlmProvider({ provider: args.vlm_provider });
    const { vlmResult, vlmError } = await runVlmSecondOpinion({
      escalate: escalation.escalate,
      provider,
      imagePath,
      expectedLayout: args.expected_layout,
      analyzeArk: payload => TOOL_HANDLERS.analyze_image_with_ark(payload),
      analyzeKimi: payload => TOOL_HANDLERS.analyze_image_with_kimi(payload),
    });

    const result = buildDeckVisionPreflightResult({
      imagePath,
      yoloResult,
      vlmResult,
      vlmError,
      escalation,
      expectedLayout: args.expected_layout,
      provider,
    });

    return {
      data: result,
      hardwareSnapshot: captureResult.hardwareSnapshot || null,
      sessionId: args.session_id || DEFAULT_SESSION_ID,
    };
  },

  async list_critical_probe_targets(args) {
    const sessionId = args.session_id || DEFAULT_SESSION_ID;
    const sessionState = readSessionState(sessionId);
    const summary = listCriticalProbeTargets({
      sessionState,
      criticalSources: args.critical_sources,
      includeAllExpectedPresent: Boolean(args.include_all_expected_present_fallback),
    });

    return {
      data: {
        session_id: sessionId,
        ...summary,
        no_robot_motion: true,
        subphase: "critical_probe",
      },
      stateRevision: sessionState.state_revision,
      sessionId,
    };
  },

  async get_protocols(args) {
    const protocols = await requestRobotJson("GET", args.robot_ip, "/protocols");
    return {
      data: {
        protocols,
      },
    };
  },

  async upload_protocol(args) {
    const uploaded = await uploadProtocol(args);
    return {
      data: {
        protocol: uploaded,
      },
    };
  },

  async run_protocol(args) {
    try {
      const simulationGate = await enforceSimulationGate(args);
      const uploaded = await uploadProtocol(args);
      const protocolId = readNested(unwrapData(uploaded) || {}, [["id"]], null);
      if (!protocolId) {
        throw new Error("Protocol upload did not return a protocol id.");
      }

      const labwareOffsets = await resolveRunLabwareOffsets(args.robot_ip, args.labware_offsets);
      const createdRun = await requestRobotJson("POST", args.robot_ip, "/runs", {
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          buildProtocolRunCreateBody({
            protocolId,
            runTimeParameters: args.run_time_parameters,
            labwareOffsets,
          }),
        ),
      });
      const runId = readNested(unwrapData(createdRun) || {}, [["id"]], null);
      if (!runId) {
        throw new Error("Run creation did not return a run id.");
      }

      let preflightGate;
      if (args.skip_preflight === true) {
        preflightGate = {
          ok: true,
          allowed_to_play: true,
          skipped: true,
          summary: "Preflight skipped (skip_preflight=true).",
        };
      } else {
        const preflightWrap = await runPreflightRunSetup({
          robot_ip: args.robot_ip,
          file_path: args.file_path,
          session_id: args.session_id || runId,
          run_id: runId,
          skip_deck_diff: args.skip_preflight_deck_diff === true,
          strict_empty_labware_slots: args.strict_preflight_labware_slots === true,
        });
        preflightGate = preflightWrap.data;
        if (!preflightGate.ok) {
          const preflightError = new Error(
            preflightGate.summary || "Preflight blocked real execution before play.",
          );
          preflightError.toolContext = {
            data: {
              blocked_real_execution: true,
              gate_stage: "preflight_run_setup",
              preflight_run_setup: preflightGate,
              simulation_gate: simulationGate,
            },
          };
          throw preflightError;
        }
      }

      const autoPlay = args.auto_play ?? true;
      let playAction = null;
      if (autoPlay) {
        playAction = await requestRobotJson("POST", args.robot_ip, `/runs/${runId}/actions`, {
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            data: {
              actionType: "play",
            },
          }),
        });
        await pollRunToTerminal({
          robotIp: args.robot_ip,
          runId,
          timeoutMs: args.timeout_ms ?? 1800000,
          pollIntervalMs: args.poll_interval_ms ?? 1000,
        });
      }

      const snapshot = await collectRunExecutionSnapshot({
        robotIp: args.robot_ip,
        runId,
        pageLength: args.page_length ?? 20,
      });
      const finalStatus = snapshot.runHistoryResult.data?.status || null;
      let failureGuidance = null;
      if (shouldAttachRecoveryGuidance(finalStatus)) {
        failureGuidance = await readRunFailureGuidance(args, runId, args.session_id || runId);
      }

      const result = {
        data: buildRunProtocolResult({
          protocol: uploaded,
          created_run: createdRun,
          play_action: playAction,
          final_run_history: snapshot.runHistoryResult.data,
          parsed_error: failureGuidance?.parsedError || null,
          recovery: failureGuidance?.recovery || null,
          simulation_gate: simulationGate,
          preflight_gate: preflightGate,
        }),
        hardwareSnapshot:
          failureGuidance?.hardwareSnapshot && Object.keys(failureGuidance.hardwareSnapshot).length > 0
            ? failureGuidance.hardwareSnapshot
            : {
                ...snapshot.robotStatusResult.hardwareSnapshot,
                ...snapshot.moduleStatusResult.hardwareSnapshot,
                ...snapshot.runHistoryResult.hardwareSnapshot,
              },
        stateRevision: failureGuidance?.stateRevision ?? 0,
        sessionId: failureGuidance?.sessionId || args.session_id || runId,
        runId,
      };
      recordToolResultLog({
        toolName: "run_protocol",
        eventKind: "protocol_run",
        args,
        result,
        fallbackSessionId: args.session_id || runId,
        summary: `Protocol run finished with status ${result.data.final_status || "unknown"}.`,
        data: {
          simulation_gate_success: result.data.simulation_gate?.parsed?.success ?? null,
          preflight_gate_ok: result.data.preflight_gate?.ok ?? null,
          parsed_error_category: result.data.parsed_error?.error_category || null,
          recovery_action:
            result.data.recovery?.recovery?.action || result.data.recovery?.action || null,
          command_total: result.data.final_run_history?.command_counts?.total ?? null,
        },
      });
      return result;
    } catch (error) {
      recordToolResultLog({
        toolName: "run_protocol",
        eventKind: "protocol_run",
        args,
        error,
        fallbackSessionId: args.session_id || DEFAULT_SESSION_ID,
        fallbackStatus: error?.toolContext?.data?.blocked_real_execution ? "blocked" : "error",
        summary: error?.toolContext?.data?.blocked_real_execution
          ? `Real execution blocked at ${error?.toolContext?.data?.gate_stage || "unknown_gate"}.`
          : "Protocol run failed before completion.",
        data: {
          blocked_real_execution: error?.toolContext?.data?.blocked_real_execution || false,
          gate_stage: error?.toolContext?.data?.gate_stage || null,
          parsed_simulation_output: error?.toolContext?.data?.parsed_simulation_output || null,
        },
      });
      throw error;
    }
  },

  async probe_wells(args) {
    const wells = Array.isArray(args.wells)
      ? args.wells.map(well => String(well || "").trim().toUpperCase()).filter(Boolean)
      : [];
    if (wells.length === 0) {
      throw new Error("probe_wells requires at least one target well.");
    }

    const outputPath = resolveProbeProtocolOutputPath(args);
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    const protocolText = buildProbeWellsProtocol({
      pipetteName: args.pipette_name,
      mount: args.mount,
      tiprackLoadName: args.tiprack_load_name,
      tiprackSlot: args.tiprack_slot,
      labwareLoadName: args.labware_load_name,
      labwareSlot: args.labware_slot,
      trashSlot: args.trash_slot || null,
      wells,
      mode: args.mode || "detect_presence",
      apiLevel: args.api_level || "2.24",
      liquidPresenceDetection: args.liquid_presence_detection ?? true,
      startingTip: args.starting_tip,
    });
    fs.writeFileSync(outputPath, `${protocolText}\n`);

    const simulation = await runSimulationTool({
      protocol_path: outputPath,
      workspace_root: args.workspace_root,
      api_root: args.api_root,
      shared_data_root: args.shared_data_root,
      python_executable: args.python_executable,
      extra_args: args.extra_args,
      max_log_chars: 12000,
    });
    const parsedSimulationOutput = parseSimulationLog({
      stdout: simulation.stdout,
      stderr: simulation.stderr,
      exit_code: simulation.exit_code,
      file_path: outputPath,
    });
    const executeOnRobot = args.execute_on_robot === true;

    if (!executeOnRobot) {
      const result = {
        data: {
          mode: args.mode || "detect_presence",
          generated_protocol_path: outputPath,
          wells,
          execute_on_robot: false,
          simulation,
          parsed_simulation_output: parsedSimulationOutput,
        },
      };
      recordToolResultLog({
        toolName: "probe_wells",
        eventKind: "probe_preview",
        args: { ...args, file_path: outputPath },
        result,
        fallbackSessionId: args.session_id || DEFAULT_SESSION_ID,
        fallbackStatus: parsedSimulationOutput.success ? "simulated" : "simulation_failed",
        summary: parsedSimulationOutput.success
          ? "Probe wells protocol generated and simulated locally."
          : "Probe wells protocol generation succeeded, but local simulation failed.",
        data: {
          mode: args.mode || "detect_presence",
          well_count: wells.length,
          simulation_success: parsedSimulationOutput.success,
        },
      });
      return result;
    }

    if (process.env.OPENTRONS_ENABLE_PROBE_WELLS !== "1") {
      throw new Error(
        "Live probe_wells execution is disabled by default. Before real robot probing, confirm with the operator and set OPENTRONS_ENABLE_PROBE_WELLS=1 explicitly.",
      );
    }
    if (!parsedSimulationOutput.success) {
      throw new Error("probe_wells will not execute on the robot because local simulation did not pass.");
    }
    if (!args.robot_ip) {
      throw new Error("probe_wells requires robot_ip when execute_on_robot is true.");
    }

    const runResult = await TOOL_HANDLERS.run_protocol({
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
    const rawCommands = await requestRobotJson("GET", args.robot_ip, `/runs/${runResult.runId}/commands`, {
      searchParams: {
        pageLength: args.page_length ?? 50,
      },
    });
    const probeResults = extractProbeResultsFromCommands(rawCommands);
    const mode = args.mode || "detect_presence";
    const sessionId = args.session_id || runResult.sessionId || DEFAULT_SESSION_ID;
    const enrichedProbeResults = enrichProbeResultsForWriteback({
      probeResults,
      labwareSlot: args.labware_slot,
      labwareLoadName: args.labware_load_name,
      mode,
    });
    const needsWriteback = PROBE_STATE_WRITEBACK_MODES.has(mode);
    let applyResult = null;
    if (args.auto_apply_to_session === true && probeResults.length > 0) {
      applyResult = await TOOL_HANDLERS.apply_liquid_probe_results({
        session_id: sessionId,
        probe_results: probeResults,
        generated_protocol_path: outputPath,
        slot_name: args.labware_slot,
        labware_load_name: args.labware_load_name,
        run_id: runResult.runId || null,
        mode,
      });
    } else if (needsWriteback) {
      recordPendingProbeRun(sessionId, {
        runId: runResult.runId || null,
        labwareSlot: args.labware_slot,
        labwareLoadName: args.labware_load_name,
        mode,
        probeResults,
      });
    }
    const result = {
      data: {
        mode,
        generated_protocol_path: outputPath,
        wells,
        execute_on_robot: true,
        simulation,
        parsed_simulation_output: parsedSimulationOutput,
        run_protocol: runResult.data,
        probe_results: enrichedProbeResults,
        apply_liquid_probe_results: applyResult?.data || null,
        ...(needsWriteback && args.auto_apply_to_session !== true
          ? {
              pending_state_writeback: true,
              required_next_tool: "apply_liquid_probe_results",
            }
          : {}),
      },
      hardwareSnapshot: runResult.hardwareSnapshot,
      stateRevision: runResult.stateRevision,
      sessionId: runResult.sessionId,
      runId: runResult.runId,
    };
    recordToolResultLog({
      toolName: "probe_wells",
      eventKind: "probe_execution",
      args: { ...args, file_path: outputPath },
      result,
      fallbackSessionId: args.session_id || runResult.sessionId || DEFAULT_SESSION_ID,
      summary: `Probe wells run finished with ${probeResults.length} parsed probe result(s).`,
      data: {
        mode: args.mode || "detect_presence",
        well_count: wells.length,
        wells,
        execute_on_robot: true,
        generated_protocol_path: outputPath,
        no_aspirate_or_dispense: !/\.aspirate\(|\.dispense\(/.test(protocolText),
        probe_result_count: probeResults.length,
        probe_results: probeResults,
        run_id: runResult.runId || null,
        final_status: runResult.data?.final_status || null,
      },
    });
    return result;
  },

  async create_run(args) {
    const labwareOffsets = await resolveRunLabwareOffsets(args.robot_ip, args.labware_offsets);
    const run = await requestRobotJson("POST", args.robot_ip, "/runs", {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        buildProtocolRunCreateBody({
          protocolId: args.protocol_id,
          runTimeParameters: args.run_time_parameters,
          labwareOffsets,
        }),
      ),
    });
    const runId = run?.data?.id || run?.id || null;
    const snapshot = await collectRunExecutionSnapshot({
      robotIp: args.robot_ip,
      runId,
      pageLength: args.page_length ?? 10,
    });

    return {
      data: {
        run,
        run_history: snapshot.runHistoryResult.data,
      },
      hardwareSnapshot: {
        ...snapshot.robotStatusResult.hardwareSnapshot,
        ...snapshot.moduleStatusResult.hardwareSnapshot,
        ...snapshot.runHistoryResult.hardwareSnapshot,
      },
      runId,
    };
  },

  async control_run(args) {
    const actionResult = await requestRobotJson(
      "POST",
      args.robot_ip,
      `/runs/${args.run_id}/actions`,
      {
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data: {
            actionType: args.action,
          },
        }),
      },
    );
    const snapshot = await collectRunExecutionSnapshot({
      robotIp: args.robot_ip,
      runId: args.run_id,
      pageLength: args.page_length ?? 10,
    });
    const finalStatus = snapshot.runHistoryResult.data?.status || null;
    let failureGuidance = null;
    if (shouldAttachRecoveryGuidance(finalStatus)) {
      failureGuidance = await readRunFailureGuidance(args, args.run_id, args.session_id || args.run_id);
    }

    const result = {
      data: {
        action: actionResult,
        run_history: snapshot.runHistoryResult.data,
        parsed_error: failureGuidance?.parsedError || null,
        recovery: failureGuidance?.recovery || null,
      },
      hardwareSnapshot:
        failureGuidance?.hardwareSnapshot && Object.keys(failureGuidance.hardwareSnapshot).length > 0
          ? failureGuidance.hardwareSnapshot
          : {
              ...snapshot.robotStatusResult.hardwareSnapshot,
              ...snapshot.moduleStatusResult.hardwareSnapshot,
              ...snapshot.runHistoryResult.hardwareSnapshot,
            },
      stateRevision: failureGuidance?.stateRevision ?? 0,
      sessionId: failureGuidance?.sessionId || args.session_id || args.run_id,
      runId: args.run_id,
    };
    recordToolResultLog({
      toolName: "control_run",
      eventKind: "run_action",
      args,
      result,
      fallbackSessionId: args.session_id || args.run_id,
      summary: `Run action ${args.action} ended with status ${result.data.run_history?.status || "unknown"}.`,
      data: {
        action_type: args.action,
        parsed_error_category: result.data.parsed_error?.error_category || null,
        recovery_action: result.data.recovery?.recovery?.action || result.data.recovery?.action || null,
      },
    });
    return result;
  },

  async generate_continuation_protocol(args) {
    const context = await readExecutionContext(args.robot_ip, "protocol", args.run_id, {
      includeCommands: true,
      pageLength: args.page_length ?? 200,
    });
    const { protocolId, analysis, analysisCommands } = await readProtocolAnalysisForRun(
      args.robot_ip,
      context.detail,
    );
    const sessionState =
      args.use_session_state === true && args.session_id
        ? readSessionState(args.session_id)
        : null;
    const outputPath = resolveContinuationProtocolOutputPath(args, context.contextId || args.run_id);
    const generated = generateTipContinuationProtocol({
      run: context.detail,
      runCommands: unwrapData(context.commands),
      analysisCommands,
      sessionState,
      outputPath,
      protocolName: args.protocol_name || null,
    });
    const runRecord = unwrapData(context.detail) || {};
    const result = {
      data: {
        generated_protocol_path: generated.output_path,
        starting_tip: generated.starting_tip,
        remaining_cycles: generated.remaining_cycles,
        operations: generated.operations,
        ledger: generated.ledger,
        source_run_id: context.contextId || args.run_id,
        source_run_status: readNested(runRecord, [["status"]], null),
        source_protocol_id: protocolId,
        analysis_id: readNested(analysis, [["id"]], null),
        analysis_status: readNested(analysis, [["status"]], null),
        protocol_source: generated.protocol_source,
      },
      hardwareSnapshot: {
        run: context.detail,
        commands: context.commands,
        protocol_analysis: analysis,
      },
      sessionId: args.session_id || context.contextId || args.run_id,
      runId: context.contextId || args.run_id,
    };
    recordToolResultLog({
      toolName: "generate_continuation_protocol",
      eventKind: "continuation_protocol",
      args: { ...args, file_path: generated.output_path },
      result,
      fallbackSessionId: args.session_id || args.run_id,
      summary: `Continuation protocol generated from run ${context.contextId || args.run_id}.`,
      data: {
        generated_protocol_path: generated.output_path,
        starting_tip: generated.starting_tip,
        remaining_cycles: generated.remaining_cycles,
        source_run_status: result.data.source_run_status,
      },
    });
    return result;
  },

  async execute_protocol_recovery(args) {
    const result = await executeProtocolRecovery(args);
    recordToolResultLog({
      toolName: "execute_protocol_recovery",
      eventKind: "protocol_recovery",
      args,
      result,
      fallbackSessionId: args.session_id || args.run_id,
      summary: `Recovery executed action ${result.data.executed_action || "unknown"}.`,
      data: {
        executed_action: result.data.executed_action || null,
        error_category:
          result.data.recovery?.error_category || result.data.parsed_error?.error_category || null,
        destination_slot: result.data.executed_params?.destination_slot || null,
        recovery_well: result.data.executed_params?.well || null,
      },
    });
    return result;
  },

  async runtime_watch_poll(args) {
    const result = await runtimeWatchPoll(args, {
      readSnapshot: async stepArgs =>
        collectRunExecutionSnapshot({
          robotIp: stepArgs.robot_ip,
          runId: stepArgs.run_id,
          pageLength: stepArgs.page_length ?? 20,
        }),
      readGuidance: async stepArgs =>
        readRunFailureGuidance(
          stepArgs,
          stepArgs.run_id,
          stepArgs.session_id || stepArgs.run_id,
        ),
      executeRecovery: executeProtocolRecovery,
    });
    const alerts = ["completed", "needs_user", "hard_stop", "unreachable"].includes(result.status)
      ? readAlerts(args.run_id, {
          limit: 5,
          includeAcked: false,
          watchDir: args.watch_dir || null,
        })
      : [];
    const payload = {
      ...(result.data || {}),
      status: result.status,
      alerts,
    };

    if (result.status !== "running") {
      recordToolResultLog({
        toolName: "runtime_watch_poll",
        eventKind: "runtime_watch",
        args,
        result: {
          data: payload,
          runId: args.run_id,
          sessionId: args.session_id || args.run_id,
        },
        fallbackSessionId: args.session_id || args.run_id,
        summary: `Runtime watch returned ${result.status}.`,
        data: {
          status: result.status,
          reason: payload.reason || null,
          alert_count: alerts.length,
        },
      });
    }

    return {
      data: payload,
      runId: args.run_id,
      sessionId: args.session_id || args.run_id,
    };
  },

  async runtime_watch_loop(args) {
    const zeroLlmWhenNoError =
      args.zero_llm_when_no_error === true || process.env.OPENTRONS_ZERO_LLM_WHEN_NO_ERROR === "1";
    const result = await runtimeWatchLoop(
      {
        ...args,
        zero_llm_when_no_error: zeroLlmWhenNoError,
      },
      {
      readSnapshot: async stepArgs =>
        collectRunExecutionSnapshot({
          robotIp: stepArgs.robot_ip,
          runId: stepArgs.run_id,
          pageLength: stepArgs.page_length ?? 20,
        }),
      readGuidance: async stepArgs =>
        readRunFailureGuidance(
          stepArgs,
          stepArgs.run_id,
          stepArgs.session_id || stepArgs.run_id,
        ),
      executeRecovery: executeProtocolRecovery,
      },
    );

    recordToolResultLog({
      toolName: "runtime_watch_loop",
      eventKind: "runtime_watch_loop",
      args,
      result,
      fallbackSessionId: args.session_id || args.run_id,
      fallbackStatus: result.status,
      summary: `Runtime watch loop ended ${result.status} after ${result.turns_completed} turn(s).`,
      data: {
        goal_id: result.goal_id,
        status: result.status,
        goal_status: result.goal_status,
        turns_completed: result.turns_completed,
        final_status: result.final_status,
        final_reason: result.final_reason,
        outbox_delivery: result.outbox_delivery || null,
        no_robot_motion: result.no_robot_motion,
      },
    });

    return {
      data: result,
      runId: args.run_id,
      sessionId: args.session_id || args.run_id,
    };
  },

  async runtime_get_alerts(args) {
    const alertRunId = args.run_id || args.session_id;
    if (!alertRunId) {
      throw new Error("runtime_get_alerts requires run_id or session_id.");
    }
    return {
      data: {
        status: "ok",
        latest: readLatest(alertRunId, { watchDir: args.watch_dir || null }),
        alerts: readAlerts(alertRunId, {
          limit: args.limit ?? 20,
          includeAcked: args.include_acked === true,
          watchDir: args.watch_dir || null,
        }),
      },
      runId: args.run_id || null,
      sessionId: args.session_id || alertRunId,
    };
  },

  async runtime_ack_alert(args) {
    const alert = ackAlert(args.run_id, args.alert_id, {
      watchDir: args.watch_dir || null,
      note: args.note || null,
      selection: args.selection ?? null,
    });
    return {
      data: {
        status: "acked",
        alert,
      },
      runId: args.run_id,
      sessionId: args.session_id || args.run_id,
    };
  },

  async runtime_get_outbox(args) {
    const sessionId = args.session_id || args.run_id || DEFAULT_SESSION_ID;
    return {
      data: {
        status: "ok",
        paths: runtimeOutboxPaths({
          sessionId,
          outboxDir: args.outbox_dir || null,
          hostAdapterDir: args.host_adapter_dir || null,
        }),
        events: readRuntimeOutbox({
          sessionId,
          runId: args.run_id || null,
          limit: args.limit ?? 20,
          includeAcked: args.include_acked === true,
          includeDelivered: args.include_delivered !== false,
          outboxDir: args.outbox_dir || null,
        }),
      },
      runId: args.run_id || null,
      sessionId,
    };
  },

  async runtime_ack_outbox(args) {
    const sessionId = args.session_id || DEFAULT_SESSION_ID;
    const event = ackRuntimeOutboxEvent({
      sessionId,
      outboxId: args.outbox_id,
      note: args.note || null,
      selection: args.selection ?? null,
      outboxDir: args.outbox_dir || null,
    });
    return {
      data: {
        status: "acked",
        event,
      },
      runId: event.run_id || null,
      sessionId,
    };
  },

  async runtime_deliver_outbox(args) {
    const sessionId = args.session_id || args.run_id || DEFAULT_SESSION_ID;
    const delivery = await deliverRuntimeOutbox({
      sessionId,
      runId: args.run_id || null,
      adapters: args.adapters || [],
      limit: args.limit ?? 20,
      includeDelivered: args.include_delivered === true,
      outboxDir: args.outbox_dir || null,
      hostAdapterDir: args.host_adapter_dir || null,
      webhookUrl: args.webhook_url || null,
    });
    return {
      data: {
        ...delivery,
        paths: runtimeOutboxPaths({
          sessionId,
          outboxDir: args.outbox_dir || null,
          hostAdapterDir: args.host_adapter_dir || null,
        }),
      },
      runId: args.run_id || null,
      sessionId,
    };
  },

  async recover_tip_pickup(args) {
    const result = await executeProtocolRecovery(args, {
      expectedAction: "retry_pick_up_tip_with_next_candidate",
    });
    const wrappedResult = {
      ...result,
      data: {
        recovered_well: result.data.executed_params?.well || null,
        recovered_tiprack_slot: result.data.executed_params?.tiprack_slot || null,
        ...result.data,
      },
    };
    recordToolResultLog({
      toolName: "recover_tip_pickup",
      eventKind: "protocol_recovery",
      args,
      result: wrappedResult,
      fallbackSessionId: args.session_id || args.run_id,
      summary: `Tip recovery retried well ${wrappedResult.data.recovered_well || "unknown"}.`,
      data: {
        executed_action: wrappedResult.data.executed_action || null,
        recovery_well: wrappedResult.data.recovered_well || null,
        tiprack_slot: wrappedResult.data.recovered_tiprack_slot || null,
      },
    });
    return wrappedResult;
  },

  async get_runs(args) {
    const runs = await requestRobotJson("GET", args.robot_ip, "/runs");
    return {
      data: {
        runs,
      },
    };
  },

  async run_history(args) {
    return readRunHistory(args);
  },

  async experiment_history(args) {
    const entries = readResultLogEntries(args);
    return {
      data: {
        entries,
        summary: summarizeResultLogEntries(entries),
        filters: {
          session_id: args.session_id || null,
          run_id: args.run_id || null,
          tool_name: args.tool_name || null,
          event_kind: args.event_kind || null,
          status: args.status || null,
          limit: Math.max(1, Math.min(Number(args.limit || 20), 200)),
        },
      },
    };
  },

  async restart_review(args) {
    return executeRestartReview(args);
  },

  async safe_next_action(args) {
    const base = await executeRestartReview(args);
    return {
      ...base,
      data: {
        ...base.data,
        safe_next_action: buildSafeNextAction(base.data),
      },
    };
  },

  async runtime_recovery_monitor(args) {
    const monitor = await runRuntimeRecoveryMonitor(args, {
      runtimeRecoverySelfTest: async () => buildRuntimeRecoverySelfTestResult(),
      healthCheck: monitorArgs => TOOL_HANDLERS.health_check(monitorArgs),
      readRobotStatus,
      readModuleStatus,
      readRunHistory,
      readRunFailureGuidance,
      safeNextAction: monitorArgs => TOOL_HANDLERS.safe_next_action(monitorArgs),
      liveLiquidRecoveryGate: monitorArgs => TOOL_HANDLERS.live_liquid_recovery_gate(monitorArgs),
      runtimeWatchPoll: monitorArgs => TOOL_HANDLERS.runtime_watch_poll(monitorArgs),
    });
    if (args.publish_notifications !== false) {
      monitor.alert_publication = publishMonitorNotifications({
        monitor,
        watchDir: args.watch_dir || null,
        outboxDir: args.outbox_dir || null,
        includeInfo: args.include_info_notifications === true,
      });
      if (Array.isArray(args.notify_adapters) && args.notify_adapters.length > 0) {
        monitor.outbox_delivery = await deliverRuntimeOutbox({
          sessionId: monitor.session_id,
          runId: monitor.run_id || null,
          adapters: args.notify_adapters,
          limit: args.notify_limit ?? 20,
          outboxDir: args.outbox_dir || null,
          hostAdapterDir: args.host_adapter_dir || null,
          webhookUrl: args.webhook_url || null,
        });
      }
    }
    const result = {
      data: monitor,
      sessionId: monitor.session_id,
      runId: monitor.run_id,
      stateRevision: 0,
    };

    if (args.record_result_log !== false) {
      const logEntry = recordToolResultLog({
        toolName: "runtime_recovery_monitor",
        eventKind: "runtime_monitor",
        args,
        result,
        fallbackSessionId: monitor.session_id,
        fallbackStatus: monitor.status,
        summary: monitor.summary_zh,
        data: {
          monitor_id: monitor.monitor_id,
          status: monitor.status,
          self_fix_mode: monitor.self_fix_mode,
          allow_l4_execution: monitor.allow_l4_execution,
          operator_opt_in: monitor.operator_opt_in,
          requires_attention: monitor.requires_attention,
          attention_count: monitor.attention_count,
          recommended_next_tools: monitor.recommended_next_tools,
          notifications: monitor.notifications,
          alert_publication: monitor.alert_publication || null,
          outbox_delivery: monitor.outbox_delivery || null,
          acceptance: monitor.acceptance,
          no_robot_motion: monitor.no_robot_motion,
        },
      });
      result.data.result_log_entry_id = logEntry?.entry_id || null;
      result.data.result_log_entry = logEntry || null;
    }

    return result;
  },

  async doctor_local_runtime(args) {
    return {
      data: await runDoctorTool(args),
    };
  },

  async simulate_protocol(args) {
    const gate = evaluateVirtualLabStateGate(args);
    if (gate) {
      return gate;
    }
    return {
      data: await runSimulationTool(args),
    };
  },

  async parse_simulation_output(args) {
    return {
      data: parseSimulationLog(args),
    };
  },

  async preflight_run_setup(args) {
    return runPreflightRunSetup(args);
  },

  async health_check(args) {
    const report = buildHealthCheck(args);
    const serversEntrypoint = path.join(PLUGIN_ROOT, "servers", "opentrons-mcp", "index.js");
    report.mcp_server.entrypoint = fs.existsSync(serversEntrypoint) ? serversEntrypoint : __filename;
    report.mcp_server.required_runtime_tools = buildToolAvailabilitySummary();
    if (args.robot_ip) {
      report.robot = await checkRobotHealth(args.robot_ip);
    }
    return { data: report };
  },

  async runtime_recovery_self_test() {
    return buildRuntimeRecoverySelfTestResult();
  },

  async live_liquid_recovery_gate(args) {
    const [robotStatusResult, moduleStatusResult] = await Promise.all([
      readRobotStatus(args),
      readModuleStatus(args),
    ]);
    const selfTestResult = buildRuntimeRecoverySelfTestResult();
    const sessionId = resolveSessionId(args, robotStatusResult);
    const sessionState = readSessionState(sessionId);
    const sourceRequirementResolution = resolveLiquidGateRequiredSources({
      sourcePlan: args.source_plan || null,
      requiredSources: args.required_sources || [],
    });
    const { requiredSources, invalidSourcePlan } = sourceRequirementResolution;
    const recoverySteps = Array.isArray(args.recovery_steps)
      ? args.recovery_steps
      : Array.isArray(args.virtual_lab_steps)
        ? args.virtual_lab_steps
        : null;
    const errorStepIndex = args.error_step_index ?? args.errorStepIndex ?? null;
    const hasSubstitutionContext = Boolean(
      args.failed_source_key ||
        args.failed_slot_name ||
        args.failed_well_name ||
        (Array.isArray(recoverySteps) && recoverySteps.length > 0),
    );
    const substitutionPlan = hasSubstitutionContext
      ? buildLiquidSourceSubstitutionPlan({
          sessionState,
          failedSourceKey: args.failed_source_key,
          failedSlotName: args.failed_slot_name,
          failedWellName: args.failed_well_name,
          preferredSourceKey: args.preferred_source_key,
        })
      : null;
    const suffixEvaluation = hasSubstitutionContext
      ? evaluateLiveLiquidGateSuffix({
          sessionState,
          recoverySteps,
          errorStepIndex,
          substitutionPlan,
        })
      : null;
    const gate = buildLiveLiquidRecoveryGateResult({
      robotIp: args.robot_ip,
      selfTestResult,
      robotStatusResult,
      moduleStatusResult,
      sessionState,
      requiredSources,
      sourcePlan: args.source_plan || null,
      invalidSourcePlan,
      sessionId,
      allowObservedMismatchReprobe: args.allow_observed_mismatch_reprobe === true,
      suffixEvaluation,
    });
    const result = {
      data: gate,
      hardwareSnapshot: {
        ...robotStatusResult.hardwareSnapshot,
        ...moduleStatusResult.hardwareSnapshot,
      },
      stateRevision: sessionState.state_revision,
      sessionId,
    };

    recordToolResultLog({
      toolName: "live_liquid_recovery_gate",
      eventKind: "live_readiness",
      args,
      result,
      fallbackSessionId: sessionId,
      fallbackStatus: gate.status || "completed",
      summary: gate.ok_for_live_liquid_rerun
        ? "Live liquid recovery gate passed."
        : `Live liquid recovery gate blocked: ${gate.failed_checks.join(", ") || gate.status}.`,
      data: {
        ok_for_live_liquid_rerun: gate.ok_for_live_liquid_rerun,
        source_plan: gate.source_plan,
        failed_checks: gate.failed_checks,
        warning_checks: gate.warning_checks,
        recommended_next_action: gate.recommended_next_action,
        allowed_next_tools: gate.allowed_next_tools,
        human_required: gate.human_required,
        resolution_plan: gate.resolution_plan,
        operator_request: gate.operator_request,
        next_steps: gate.next_steps,
        self_test_coverage:
          gate.checks.find(check => check.name === "loaded_runtime_recovery_self_test")?.coverage || null,
        source_map_requirements:
          gate.checks.find(check => check.name === "source_map_requirements")?.required_sources || [],
        source_identity_metadata:
          gate.checks.find(check => check.name === "source_identity_metadata") || null,
        blocked_by: gate.blocked_by || null,
        pending_probe_wells: gate.pending_probe_wells || [],
        suffix_sufficient: gate.suffix_sufficient,
        final_auto_resume_eligible: gate.final_auto_resume_eligible,
        suffix_violations: gate.suffix_violations,
      },
    });

    return result;
  },

  async live_readiness_check(args) {
    return executeLiveReadinessCheck(args);
  },
};

class OpentronsLabMCP {
  constructor() {
    this.server = new Server(
      {
        name: "opentrons-lab-mcp",
        version: "0.1.0",
      },
      {
        capabilities: {
          tools: {},
        },
      },
    );

    this.setupTools();
  }

  setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: TOOL_DEFINITIONS,
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async request => {
      const { name, arguments: args = {} } = request.params;
      const handler = TOOL_HANDLERS[name];

      if (!handler) {
        return errorResponse(name, new Error(`Unknown tool: ${name}`));
      }

      try {
        const result = await handler(args);
        return successResponse(result);
      } catch (error) {
        return errorResponse(name, error, error?.toolContext || {});
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Opentrons Lab MCP server running on stdio");
  }
}

const server = new OpentronsLabMCP();
export { OpentronsLabMCP, TOOL_DEFINITIONS, TOOL_HANDLERS };

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  server.run().catch(error => {
    console.error(error);
    process.exit(1);
  });
}
