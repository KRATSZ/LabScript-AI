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
  buildHeaterShakerCommand,
  buildHomeCommand,
  buildLoadLabwareCommand,
  buildLoadModuleCommand,
  buildLoadPipetteCommand,
  buildMoveLabwareCommand,
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
import { parseSimulationLog, runDoctorTool, runSimulationTool } from "./lib/simulation.js";
import { buildProbeWellsProtocol, extractProbeResultsFromCommands } from "./lib/probe.js";
import {
  DEFAULT_SESSION_ID,
  ensureTiprackState,
  mutateSessionState,
  readSessionState,
  setCleanupState,
  setPipetteState,
  uniqueSessionStrings,
} from "./lib/state.js";
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
import { buildHealthCheck, checkRobotHealth } from "./lib/health-check.js";
import { runVisionCheck } from "./lib/vision-check.js";
import { buildErrorTaxonomy, buildTaxonomyIssue } from "./lib/error-taxonomy.js";
import { buildLiveReadinessReport } from "./lib/live-readiness.js";
import {
  buildDeckPhotoAnalysisPrompt,
  buildImageDataUrl,
  buildSiliconFlowChatBody,
  callSiliconFlowChatCompletion,
  extractAssistantText,
  parseAssistantJson,
  resolveSiliconFlowApiKey,
} from "./lib/siliconflow.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** Prefer plugin `artifacts/camera-captures`; otherwise use in-repo `vision/data/camera-captures`, then legacy sibling fallback. */
function resolveCameraArtifactRoot() {
  const repoRoot = path.resolve(__dirname, "../..");
  const preferred = path.join(repoRoot, "artifacts", "camera-captures");
  const visionFallback = path.join(repoRoot, "vision", "data", "camera-captures");
  const legacyFallback = path.resolve(repoRoot, "..", "labagentyolo", "data", "camera-captures");
  try {
    if (fs.existsSync(preferred)) {
      return preferred;
    }
  } catch {
    // ignore
  }
  try {
    if (fs.existsSync(visionFallback)) {
      return visionFallback;
    }
  } catch {
    // ignore
  }
  try {
    if (fs.existsSync(legacyFallback)) {
      return legacyFallback;
    }
  } catch {
    // ignore
  }
  return preferred;
}

const DEFAULT_CAMERA_ARTIFACT_DIR = resolveCameraArtifactRoot();
const DEFAULT_VISION_ANNOTATED_DIR = path.resolve(DEFAULT_CAMERA_ARTIFACT_DIR, "vision-annotated");
const DEFAULT_PROBE_PROTOCOL_DIR = path.resolve(__dirname, "../artifacts/probe-protocols");

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
        tiprack_slots: {
          type: "array",
          items: { type: "string" },
        },
      },
    },
  },
  {
    name: "create_run_context",
    description: "Create either a protocol run context or a maintenance-run context before enqueueing commands.",
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
      "Upload a protocol, create a run, optionally play it, then poll until the run reaches a terminal or intervention-required state.",
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
    description: "Create a run for a protocol already on the robot.",
    inputSchema: {
      type: "object",
      properties: {
        robot_ip: { type: "string", description: "Robot IP or full base URL" },
        protocol_id: { type: "string", description: "Uploaded protocol ID" },
        run_time_parameters: { type: "object" },
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
        destination_slot: { type: "string" },
        allow_low_confidence_destination: { type: "boolean", default: false },
        module_wait_timeout_ms: { type: "integer", default: 120000 },
        module_poll_interval_ms: { type: "integer", default: 1000 },
        timeout_ms: { type: "integer", default: 120000 },
        poll_interval_ms: { type: "integer", default: 500 },
        page_length: { type: "integer", default: 20 },
        idempotency_key: {
          type: "string",
          description: "Optional idempotency key prefix for fixit commands.",
        },
      },
      required: ["run_id"],
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
    description: "Run local opentrons.simulate against a protocol file and return structured logs.",
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

function resolveSessionId(args, robotStatusResult) {
  return (
    args.session_id ||
    robotStatusResult?.data?.health_summary?.robot_serial ||
    DEFAULT_SESSION_ID
  );
}

function recordResultLog(entry) {
  try {
    appendResultLogEntry(entry);
  } catch {
    // Result logging must never break the main MCP flow.
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
  recordResultLog({
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
} = {}) {
  const resumeAction = await requestRobotJson("POST", args.robot_ip, `/runs/${args.run_id}/actions`, {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      data: {
        actionType: "resume-from-recovery",
      },
    }),
  });

  await pollRunToTerminal({
    robotIp: args.robot_ip,
    runId: args.run_id,
    timeoutMs: args.timeout_ms ?? 120000,
    pollIntervalMs: args.poll_interval_ms ?? 500,
  });

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

async function executeProtocolRecovery(args, { expectedAction = null } = {}) {
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
          key: args.idempotency_key ? `${args.idempotency_key}:pickUpTip` : null,
          params: {
            pipetteId,
            labwareId,
            wellName: nextWell,
          },
        }),
        timeoutMs: args.timeout_ms ?? 120000,
        pollIntervalMs: args.poll_interval_ms ?? 500,
      });

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
    let stateAfterSuggestion = sessionState;
    if ((args.error_category || classification.error_category) === "TIP_PHYSICALLY_MISSING") {
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
    const recoverySuggestion = buildRecoverySuggestion({
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
    });
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
    const request = buildCreateRunContextRequest({
      contextType: args.context_type,
      protocolId: args.protocol_id,
      runTimeParameters: args.run_time_parameters,
      labwareOffsets: args.labware_offsets,
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

      const createdRun = await requestRobotJson("POST", args.robot_ip, "/runs", {
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data: {
            protocolId,
            ...(args.run_time_parameters
              ? { runTimeParameterValues: args.run_time_parameters }
              : {}),
          },
        }),
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
    const result = {
      data: {
        mode: args.mode || "detect_presence",
        generated_protocol_path: outputPath,
        wells,
        execute_on_robot: true,
        simulation,
        parsed_simulation_output: parsedSimulationOutput,
        run_protocol: runResult.data,
        probe_results: probeResults,
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
        probe_result_count: probeResults.length,
        final_status: runResult.data?.final_status || null,
      },
    });
    return result;
  },

  async create_run(args) {
    const run = await requestRobotJson("POST", args.robot_ip, "/runs", {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        data: {
          protocolId: args.protocol_id,
          ...(args.run_time_parameters
            ? { runTimeParameterValues: args.run_time_parameters }
            : {}),
        },
      }),
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

  async doctor_local_runtime(args) {
    return {
      data: await runDoctorTool(args),
    };
  },

  async simulate_protocol(args) {
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
    if (args.robot_ip) {
      report.robot = await checkRobotHealth(args.robot_ip);
    }
    return { data: report };
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
