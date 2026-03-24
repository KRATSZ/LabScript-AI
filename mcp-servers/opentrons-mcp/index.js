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
  buildCaptureImageParams,
  buildCameraControlBody,
  buildCameraImageSettings,
  buildCameraImageSettingsBody,
  buildCameraStatusSnapshot,
  buildPreviewArtifactName,
  contentTypeToExtension,
} from "./lib/vision.js";
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
const DEFAULT_CAMERA_ARTIFACT_DIR = path.resolve(__dirname, "../../artifacts/camera-captures");

const TOOL_DEFINITIONS = [
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
        tiprack_slots: {
          type: "array",
          items: { type: "string" },
        },
      },
      required: ["file_path"],
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
    name: "get_run_status",
    description: "Compatibility alias for run_history.",
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

    return {
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

    return {
      data: buildRunProtocolResult({
        protocol: uploaded,
        created_run: createdRun,
        play_action: playAction,
        final_run_history: snapshot.runHistoryResult.data,
        parsed_error: failureGuidance?.parsedError || null,
        recovery: failureGuidance?.recovery || null,
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

    return {
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

  async get_run_status(args) {
    return readRunHistory(args);
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
        return errorResponse(name, error);
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
