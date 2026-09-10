import { randomUUID } from "node:crypto";
import type { ChecksResult } from "./gate.ts";

export type Phase =
  | "need_goal"
  | "need_doc"
  | "need_robot"
  | "need_hw_slots"
  | "ready";

export type RobotModel = "OT-2" | "Flex" | "Hamilton" | "Tecan";
export type PlanBackend = "serializing" | "hamilton" | "ot2" | "tecan_evo" | "auto";

export interface HardwareState {
  leftPipette?: string;
  rightPipette?: string;
  useGripper?: boolean;
  apiVersion?: string;
  deck: Record<string, string>;
}

export interface SessionState {
  id: string;
  phase: Phase;
  goal?: string;
  /** `"none"` or pasted/uploaded SOP draft. Undefined = not collected yet. */
  doc?: string;
  robot?: RobotModel;
  hardware: HardwareState;
  sop?: string;
  code?: string;
  plan?: Record<string, unknown>;
  analyze?: Record<string, unknown>;
  lastChecks?: ChecksResult;
  /** Auto-patches used this user turn. Reset at the start of each chat turn. */
  patchesUsed?: number;
  messages: unknown[];
}

const sessions = new Map<string, SessionState>();

export function createSession(): SessionState {
  const session: SessionState = {
    id: randomUUID(),
    phase: "need_goal",
    hardware: { deck: {} },
    messages: [],
  };
  sessions.set(session.id, session);
  return session;
}

export function getSession(id: string): SessionState | undefined {
  return sessions.get(id);
}

export function enoughHardware(session: SessionState): boolean {
  const left = session.hardware.leftPipette;
  const right = session.hardware.rightPipette;
  const hasPipette = [left, right].some((p) => p && p !== "None");
  const values = Object.values(session.hardware.deck);
  const hasTip = values.some((v) => /tip\s*rack|tiprack|diti/i.test(v));
  const hasPlate = values.some((v) => /plate|reservoir|tube/i.test(v));
  return Boolean(session.robot && hasPipette && hasTip && hasPlate);
}

export function computePhase(session: SessionState): Phase {
  if (!session.goal?.trim()) return "need_goal";
  if (session.doc === undefined) return "need_doc";
  if (!session.robot) return "need_robot";
  if (!enoughHardware(session)) return "need_hw_slots";
  return "ready";
}

export function refreshPhase(session: SessionState): Phase {
  session.phase = computePhase(session);
  return session.phase;
}

export function missingList(session: SessionState): string[] {
  const missing: string[] = [];
  if (!session.goal?.trim()) missing.push("goal");
  if (session.doc === undefined) missing.push("doc");
  if (!session.robot) missing.push("robot");
  const left = session.hardware.leftPipette;
  const right = session.hardware.rightPipette;
  if (![left, right].some((p) => p && p !== "None")) {
    missing.push("pipette (left or right)");
  }
  const values = Object.values(session.hardware.deck);
  if (!values.some((v) => /tip\s*rack|tiprack|diti/i.test(v))) missing.push("tips/tiprack slot");
  if (!values.some((v) => /plate|reservoir|tube/i.test(v))) {
    missing.push("plate or reservoir slot");
  }
  return missing;
}

export function applyForm(
  session: SessionState,
  input: { goal: string; doc?: string; robot?: RobotModel }
): SessionState {
  session.goal = input.goal.trim();
  const doc = (input.doc ?? "").trim();
  session.doc = doc ? doc : "none";
  session.sop = session.doc !== "none" ? session.doc : undefined;
  if (isRobotModel(input.robot)) {
    session.robot = input.robot;
    if (!session.hardware.apiVersion && (input.robot === "OT-2" || input.robot === "Flex")) {
      session.hardware.apiVersion = input.robot === "OT-2" ? "2.15" : "2.22";
    }
  }
  refreshPhase(session);
  return session;
}

export const HARDWARE_PRESETS = {
  ot2_p300_standard3: {
    leftPipette: "p300_single_gen2",
    rightPipette: "None",
    apiVersion: "2.15",
    deck: {
      "1": "opentrons_96_tiprack_300ul",
      "2": "nest_96_wellplate_200ul_flat",
      "3": "nest_12_reservoir_15ml",
    },
  },
  flex_1000_standard3: {
    leftPipette: "flex_1channel_1000",
    rightPipette: "None",
    apiVersion: "2.22",
    deck: {
      A1: "opentrons_flex_96_tiprack_1000ul",
      D2: "nest_96_wellplate_200ul_flat",
      C1: "nest_12_reservoir_15ml",
      A3: "trash_bin",
    },
  },
  hamilton_star_standard: {
    leftPipette: "star_1000",
    rightPipette: "None",
    apiVersion: "",
    deck: {
      "1": "hamilton_96_tiprack_300ul",
      "2": "corning_96_wellplate_360ul_flat",
      "3": "nest_12_reservoir_15ml",
    },
  },
  tecan_evo_standard: {
    leftPipette: "liha_1000",
    rightPipette: "None",
    apiVersion: "",
    deck: {
      "1": "tecan_diti_200ul_tiprack",
      "2": "tecan_96_wellplate",
      "3": "nest_12_reservoir_15ml",
    },
  },
} as const;

export type HardwarePresetId = keyof typeof HARDWARE_PRESETS;

const PRESET_ROBOT: Record<HardwarePresetId, RobotModel> = {
  ot2_p300_standard3: "OT-2",
  flex_1000_standard3: "Flex",
  hamilton_star_standard: "Hamilton",
  tecan_evo_standard: "Tecan",
};

export function isRobotModel(value: string | undefined): value is RobotModel {
  return value === "OT-2" || value === "Flex" || value === "Hamilton" || value === "Tecan";
}

export function planBackendFor(robot: RobotModel | undefined): PlanBackend {
  if (robot === "Hamilton") return "hamilton";
  if (robot === "Tecan") return "tecan_evo";
  if (robot === "OT-2" || robot === "Flex") return "serializing";
  return "auto";
}

export function presetMismatchWarning(
  robot: RobotModel | undefined,
  preset: HardwarePresetId | undefined
): string | undefined {
  if (!preset || !robot) return undefined;
  const expected = PRESET_ROBOT[preset];
  if (expected && robot !== expected) {
    return `preset ${preset} is for ${expected}; session robot is ${robot}`;
  }
  return undefined;
}

export function applyPreset(session: SessionState, id: HardwarePresetId): SessionState {
  const preset = HARDWARE_PRESETS[id];
  session.robot = PRESET_ROBOT[id];
  session.hardware.leftPipette = preset.leftPipette;
  session.hardware.rightPipette = preset.rightPipette;
  session.hardware.apiVersion = preset.apiVersion;
  session.hardware.deck = { ...preset.deck };
  refreshPhase(session);
  return session;
}

export interface AskUserInput {
  goal?: string;
  doc?: string;
  robot?: RobotModel;
  preset?: HardwarePresetId;
  left_pipette?: string;
  right_pipette?: string;
  use_gripper?: boolean;
  api_version?: string;
  deck?: Array<{ slot: string; labware: string }>;
}

function hardwareTouched(input: AskUserInput): boolean {
  return Boolean(
    input.preset ||
      input.robot ||
      typeof input.left_pipette === "string" ||
      typeof input.right_pipette === "string" ||
      Array.isArray(input.deck)
  );
}

export function applyAskUser(session: SessionState, input: AskUserInput): SessionState {
  if (input.preset && input.preset in HARDWARE_PRESETS) {
    applyPreset(session, input.preset);
  }
  if (typeof input.goal === "string" && input.goal.trim()) {
    session.goal = input.goal.trim();
  }
  if (typeof input.doc === "string") {
    const doc = input.doc.trim();
    session.doc = doc ? doc : "none";
    if (session.doc !== "none" && !session.sop?.trim()) {
      session.sop = session.doc;
    }
  } else if (hardwareTouched(input) && session.doc === undefined) {
    session.doc = "none";
  }
  if (isRobotModel(input.robot)) {
    session.robot = input.robot;
    if (!session.hardware.apiVersion && (input.robot === "OT-2" || input.robot === "Flex")) {
      session.hardware.apiVersion = input.robot === "OT-2" ? "2.15" : "2.22";
    }
  }
  if (typeof input.left_pipette === "string") {
    session.hardware.leftPipette = input.left_pipette.trim() || "None";
  }
  if (typeof input.right_pipette === "string") {
    session.hardware.rightPipette = input.right_pipette.trim() || "None";
  }
  if (typeof input.use_gripper === "boolean") {
    session.hardware.useGripper = input.use_gripper;
  }
  if (typeof input.api_version === "string" && input.api_version.trim()) {
    session.hardware.apiVersion = input.api_version.trim();
  }
  if (Array.isArray(input.deck)) {
    for (const item of input.deck) {
      if (!item?.slot || !item?.labware) continue;
      session.hardware.deck[String(item.slot).trim()] = String(item.labware).trim();
    }
  }
  refreshPhase(session);
  return session;
}

export function canRunPipeline(session: SessionState): boolean {
  return computePhase(session) === "ready";
}

export function canGenerateSop(session: SessionState): boolean {
  return canRunPipeline(session);
}

export function isOpentrons(session: Pick<SessionState, "robot">): boolean {
  return session.robot === "OT-2" || session.robot === "Flex";
}

export function checksRoute(
  session: Pick<SessionState, "robot" | "code" | "plan">
): "opentrons" | "plan" | "blocked" {
  if (isOpentrons(session)) {
    return session.code?.trim() ? "opentrons" : "blocked";
  }
  if (session.plan && typeof session.plan === "object") return "plan";
  if (session.code?.trim()) return "opentrons";
  return "blocked";
}

export function canGenerateCode(session: SessionState): boolean {
  return canRunPipeline(session) && Boolean(session.sop?.trim()) && isOpentrons(session);
}

export function canEmitPlan(session: SessionState): boolean {
  return canRunPipeline(session) && Boolean(session.sop?.trim()) && !isOpentrons(session);
}

export function shouldReuseSop(session: SessionState, force?: boolean): boolean {
  return Boolean(session.sop?.trim()) && force !== true;
}

export function shouldCallCompactSop(session: SessionState, force?: boolean): boolean {
  return canGenerateSop(session) && !shouldReuseSop(session, force);
}

export const SOP_CHAR_CAP = 1200;

export function capSop(text: string, max = SOP_CHAR_CAP): string {
  const trimmed = text.trim();
  return trimmed.length <= max ? trimmed : trimmed.slice(0, max);
}

export function formatHardwareConfig(session: SessionState): string {
  const robot = session.robot ?? "unset";
  const api =
    session.hardware.apiVersion ??
    (session.robot === "OT-2" ? "2.15" : session.robot === "Flex" ? "2.22" : "unset");
  const deckEntries = Object.entries(session.hardware.deck);
  const deck = deckEntries.length
    ? deckEntries.map(([slot, labware]) => `  ${slot}: ${labware}`).join("\n")
    : "  (No labware configured)";
  return [
    `Robot Model: ${robot}`,
    `API Version: ${api}`,
    `Left Pipette: ${session.hardware.leftPipette || "None"}`,
    `Right Pipette: ${session.hardware.rightPipette || "None"}`,
    `Use Gripper: ${session.hardware.useGripper ?? false}`,
    `Plan backend: ${planBackendFor(session.robot)}`,
    "Deck Layout:",
    deck,
  ].join("\n");
}

export function snapshot(session: SessionState) {
  const checks = session.lastChecks;
  return {
    id: session.id,
    phase: session.phase,
    missing: missingList(session),
    goal: session.goal ?? "",
    doc: session.doc ?? "",
    robot: session.robot ?? null,
    hardware: session.hardware,
    hardware_config: formatHardwareConfig(session),
    sop: session.sop ?? "",
    code: session.code ?? "",
    plan: session.plan ?? null,
    analyze: session.analyze ?? null,
    checks: checks ?? null,
    fab: { lit: Boolean(checks?.fab.lit) },
  };
}
