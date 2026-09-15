import { randomUUID } from "node:crypto";
import type { ChecksResult, LogicPassResult } from "./gate.ts";
import {
  DEVICE_REGISTRY,
  HARDWARE_PRESETS,
  PRESET_ROBOT,
  ROBOT_PRESET,
  deviceFor,
  type HardwarePresetId,
  type PlanBackend,
  type RobotModel,
} from "./devices.ts";

export type { HardwarePresetId, PlanBackend, RobotModel };
export { DEVICE_REGISTRY, HARDWARE_PRESETS, deviceFor, deviceForId, usesFluentCompile, usesHamiltonCompile, hamiltonFamily } from "./devices.ts";
export type { DeviceProfile } from "./devices.ts";

export type Phase =
  | "need_goal"
  | "need_doc"
  | "need_robot"
  | "need_hw_slots"
  | "ready";

export interface HardwareState {
  leftPipette?: string;
  rightPipette?: string;
  useGripper?: boolean;
  apiVersion?: string;
  deck: Record<string, string>;
}

export interface SessionArtifacts {
  worklistGwl?: string;
  scriptXml?: string;
  hamiltonScript?: string;
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
  artifacts?: SessionArtifacts;
  lastChecks?: ChecksResult;
  /** Sticky within one protocol/device: true after checks have passed at least once. */
  hasPassedChecks?: boolean;
  /** Auto-patches used this user turn. Reset at the start of each chat turn. */
  patchesUsed?: number;
  /** True when deck/pipettes came from a standard preset, not a custom layout. */
  deckAssumed?: boolean;
  codeService?: "up" | "down";
  messages: unknown[];
  /** Append-only turn/step/tool facts for the Trajectory pane. */
  events?: import("./events.ts").AgentEvent[];
  /** messages.length when ask_user first recorded a goal/notes volume conflict. */
  conflictAskedAt?: number;
  /** True after a later chat turn (non-empty user text) while a conflict is open. */
  conflictUserReplied?: boolean;
  /** True after a later user turn confirmed a volume via ask_user. */
  draftConflictResolved?: boolean;
}

const sessions = new Map<string, SessionState>();

export function createSession(): SessionState {
  const session: SessionState = {
    id: randomUUID(),
    phase: "need_goal",
    hardware: { deck: {} },
    messages: [],
    events: [],
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

export function inferRobotFromText(text: string): RobotModel | undefined {
  const src = text.toLowerCase();
  const found = DEVICE_REGISTRY.filter((d) => d.aliases.some((re) => re.test(src)));
  return found.length === 1 ? found[0].legacyRobot : undefined;
}

const UL_AMOUNT = /(\d+(?:\.\d+)?)\s*(?:µl|ul|μl|microlit(?:er|re)s?)\b/gi;
const TRANSFER_UL =
  /\b(?:transfer(?:red|s|ing)?|aspirate[ds]?|dispense[ds]?)\s+(\d+(?:\.\d+)?)\s*(?:µl|ul|μl|microlit(?:er|re)s?)\b/gi;
const REAL_UL =
  /\b(?:real(?:ly)?|actual(?:ly)?)\b[\s\S]{0,48}?(\d+(?:\.\d+)?)\s*(?:µl|ul|μl|microlit(?:er|re)s?)\b/i;
const CAPACITY_CTX =
  /\b(hold|holds|capacity|max(?:imum)?|already|contains|start(?:s|ing)?|initial|tiprack|diti|reservoir|\d+-well|well plate)\b/;

function ulAmounts(text: string): number[] {
  return [...(text || "").matchAll(UL_AMOUNT)].map((match) => Number(match[1]));
}

function contextAt(text: string, index: number, span = 40): string {
  return text.slice(Math.max(0, index - span), Math.min(text.length, index + span)).toLowerCase();
}

/** Goal vs notes transfer-volume fight. Capacity / initial-fill numbers are not a fight. */
export function goalNotesVolumeConflict(goal = "", doc = ""): string | null {
  const notes = doc.trim();
  if (!notes || notes === "none") return null;
  const goalVols = [...new Set(ulAmounts(goal))];
  if (!goalVols.length) return null;
  const ignoreGoal = goalVols.some((vol) =>
    new RegExp(`\\bignore(?:\\s+the)?\\s+${vol}\\b`, "i").test(notes)
  );
  const competing: number[] = [];
  const real = notes.match(REAL_UL);
  if (real && !goalVols.includes(Number(real[1]))) competing.push(Number(real[1]));
  for (const match of notes.matchAll(TRANSFER_UL)) {
    const vol = Number(match[1]);
    if (!goalVols.includes(vol)) competing.push(vol);
  }
  for (const match of notes.matchAll(UL_AMOUNT)) {
    const vol = Number(match[1]);
    if (goalVols.includes(vol)) continue;
    const ctx = contextAt(notes, match.index ?? 0);
    if (CAPACITY_CTX.test(ctx)) continue;
    if (/\b(?:do not|don't|not)\s+clamp\b/.test(ctx)) continue;
    competing.push(vol);
  }
  const extra = [...new Set(competing)];
  if (!ignoreGoal && extra.length === 0) return null;
  return `goal ${goalVols.join("/")} µL vs notes ${extra.length ? extra.join("/") : "override"} µL`;
}

export function unresolvedGoalNotesConflict(session: SessionState): string | null {
  if (session.draftConflictResolved) return null;
  return goalNotesVolumeConflict(session.goal ?? "", session.doc ?? "");
}

/** First ask_user during a conflict: record the question, do not take a side. */
export function beginGoalNotesConflictAsk(session: SessionState): string | null {
  const conflict = unresolvedGoalNotesConflict(session);
  if (!conflict || session.conflictAskedAt != null) return conflict;
  session.conflictAskedAt = Array.isArray(session.messages) ? session.messages.length : 0;
  session.conflictUserReplied = false;
  session.draftConflictResolved = false;
  session.sop = undefined;
  session.code = undefined;
  session.plan = undefined;
  session.artifacts = undefined;
  session.lastChecks = undefined;
  session.hasPassedChecks = undefined;
  return conflict;
}

export function canResolveGoalNotesConflict(session: SessionState): boolean {
  return Boolean(session.conflictUserReplied) && !session.draftConflictResolved;
}

/** A later user chat turn — not the start form, not a same-turn follow-up. */
export function markConflictUserReply(session: SessionState, userText: string): void {
  if (!userText.trim()) return;
  if (session.draftConflictResolved) return;
  if (session.conflictAskedAt == null && !unresolvedGoalNotesConflict(session)) return;
  session.conflictUserReplied = true;
}

export function resolveGoalNotesConflict(session: SessionState): void {
  session.draftConflictResolved = true;
  session.conflictUserReplied = true;
  session.sop = undefined;
  session.code = undefined;
  session.plan = undefined;
  session.analyze = undefined;
  session.artifacts = undefined;
  session.lastChecks = undefined;
  session.hasPassedChecks = undefined;
}

/** Goal (+ intern notes) for SOP authoring. After a volume pick, notes are dropped. */
export function authoringGoal(session: SessionState): string {
  const goal = session.goal ?? "";
  if (session.draftConflictResolved) return goal;
  if (session.doc && session.doc !== "none") {
    return `${goal}\n\nExisting SOP draft:\n${session.doc}`;
  }
  return goal;
}

/** llmreview intent: chosen volume + generated SOP, never stale conflicting notes. */
export function reviewIntent(session: SessionState): string {
  if (!session.draftConflictResolved) return authoringGoal(session);
  const goal = (session.goal ?? "").trim();
  const sop = session.sop?.trim();
  const parts = [
    "User confirmed this volume. Intern notes were a conflicting draft — review against the chosen goal and generated SOP only.",
    "liha_1000 is the LiHa pipette. Assumed Tecan tips are 200 µL DiTi.",
    goal,
  ];
  if (sop) parts.push(`Generated SOP:\n${sop}`);
  return parts.filter(Boolean).join("\n\n");
}

export function missingList(session: SessionState): string[] {
  const missing: string[] = [];
  if (!session.goal?.trim()) missing.push("goal");
  if (session.doc === undefined) missing.push("doc");
  if (!session.robot) {
    missing.push("robot");
    return missing;
  }
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
  const conflict = unresolvedGoalNotesConflict(session);
  if (conflict) {
    missing.push(`ask_user — ${conflict}; wait for the user to pick one volume`);
  }
  return missing;
}

function pipetteUnset(value: string | undefined): boolean {
  return !value || value === "None";
}

export function assumeStandardDeck(session: SessionState): void {
  if (!session.robot) return;
  if (Object.keys(session.hardware.deck).length > 0) return;
  const id = ROBOT_PRESET[session.robot];
  const preset = HARDWARE_PRESETS[id];
  session.hardware.deck = { ...preset.deck };
  if (pipetteUnset(session.hardware.leftPipette) && pipetteUnset(session.hardware.rightPipette)) {
    session.hardware.leftPipette = preset.leftPipette;
    session.hardware.rightPipette = preset.rightPipette;
    session.hardware.apiVersion = preset.apiVersion;
  }
  session.deckAssumed = true;
}

export function applyForm(
  session: SessionState,
  input: { goal: string; doc?: string; robot?: string }
): SessionState {
  const explicit = input.robot != null && String(input.robot).trim() !== "";
  const selectedRobot = explicit
    ? deviceFor(String(input.robot).trim())?.legacyRobot
    : undefined;
  if (explicit && !selectedRobot) throw new Error("invalid robot");
  session.goal = input.goal.trim();
  const doc = (input.doc ?? "").trim();
  session.doc = doc ? doc : "none";
  session.sop = undefined;
  session.conflictAskedAt = undefined;
  session.conflictUserReplied = undefined;
  session.draftConflictResolved = undefined;
  if (selectedRobot) {
    session.robot = selectedRobot;
  } else {
    const inferred = inferRobotFromText(session.goal);
    if (inferred) session.robot = inferred;
  }
  if (session.robot) {
    const device = deviceFor(session.robot);
    if (!session.hardware.apiVersion && device?.codegen === "opentrons_python") {
      session.hardware.apiVersion = device.hardwarePreset.apiVersion;
    }
  }
  assumeStandardDeck(session);
  refreshPhase(session);
  return session;
}

export function isRobotModel(value: string | undefined): value is RobotModel {
  return Boolean(value && DEVICE_REGISTRY.some((d) => d.legacyRobot === value));
}

export function planBackendFor(robot: RobotModel | undefined): PlanBackend {
  return deviceFor(robot)?.planBackend ?? "auto";
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
  const next = PRESET_ROBOT[id];
  const switching = Boolean(session.robot && session.robot !== next);
  const preset = HARDWARE_PRESETS[id];
  session.robot = next;
  session.hardware.leftPipette = preset.leftPipette;
  session.hardware.rightPipette = preset.rightPipette;
  session.hardware.apiVersion = preset.apiVersion;
  session.hardware.deck = { ...preset.deck };
  session.deckAssumed = true;
  if (switching) {
    session.sop = undefined;
    session.code = undefined;
    session.plan = undefined;
    session.analyze = undefined;
    session.artifacts = undefined;
    session.lastChecks = undefined;
    session.hasPassedChecks = undefined;
    session.conflictAskedAt = undefined;
    session.conflictUserReplied = undefined;
    session.draftConflictResolved = undefined;
  }
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

function hasExplicitDeck(input: AskUserInput): boolean {
  return Array.isArray(input.deck) && input.deck.length > 0;
}

function resetForRobotSwitch(session: SessionState, robot: RobotModel): void {
  session.hardware.deck = {};
  session.hardware.leftPipette = undefined;
  session.hardware.rightPipette = undefined;
  session.hardware.useGripper = undefined;
  session.hardware.apiVersion = deviceFor(robot)?.hardwarePreset.apiVersion ?? "";
  session.deckAssumed = undefined;
  session.sop = undefined;
  session.code = undefined;
  session.plan = undefined;
  session.analyze = undefined;
  session.artifacts = undefined;
  session.lastChecks = undefined;
  session.hasPassedChecks = undefined;
  session.conflictAskedAt = undefined;
  session.conflictUserReplied = undefined;
  session.draftConflictResolved = undefined;
}

export function applyAskUser(session: SessionState, input: AskUserInput): SessionState {
  const previousRobot = session.robot;
  const explicitDeck = hasExplicitDeck(input);
  if (input.preset && input.preset in HARDWARE_PRESETS) {
    applyPreset(session, input.preset);
  }
  if (typeof input.goal === "string" && input.goal.trim()) {
    session.goal = input.goal.trim();
  }
  const named = isRobotModel(input.robot)
    ? input.robot
    : !session.robot
      ? inferRobotFromText(session.goal ?? "")
      : undefined;
  if (typeof input.doc === "string") {
    const doc = input.doc.trim();
    session.doc = doc ? doc : "none";
  } else if ((hardwareTouched(input) || Boolean(named)) && session.doc === undefined) {
    session.doc = "none";
  }
  if (named) {
    const from = session.robot ?? previousRobot;
    const switching = Boolean(from && from !== named);
    session.robot = named;
    if (switching) {
      resetForRobotSwitch(session, named);
    } else if (!session.hardware.apiVersion) {
      const device = deviceFor(named);
      if (device?.codegen === "opentrons_python") {
        session.hardware.apiVersion = device.hardwarePreset.apiVersion;
      }
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
  if (explicitDeck) {
    for (const item of input.deck!) {
      if (!item?.slot || !item?.labware) continue;
      session.hardware.deck[String(item.slot).trim()] = String(item.labware).trim();
    }
    session.deckAssumed = false;
  } else {
    assumeStandardDeck(session);
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
  return deviceFor(session.robot)?.codegen === "opentrons_python";
}

export function checksRoute(
  session: Pick<SessionState, "robot" | "code" | "plan">
): "opentrons" | "plan" | "blocked" {
  if (isOpentrons(session) && session.code?.trim()) return "opentrons";
  if (session.plan && typeof session.plan === "object") return "plan";
  return "blocked";
}

export function canGenerateCode(session: SessionState): boolean {
  return (
    canRunPipeline(session) &&
    Boolean(session.sop?.trim()) &&
    isOpentrons(session) &&
    !unresolvedGoalNotesConflict(session)
  );
}

export function canEmitPlan(session: SessionState): boolean {
  return canRunPipeline(session) && Boolean(session.sop?.trim()) && !unresolvedGoalNotesConflict(session);
}

export function shouldReuseSop(session: SessionState, force?: boolean): boolean {
  return Boolean(session.sop?.trim()) && force !== true;
}

export function shouldCallCompactSop(session: SessionState, force?: boolean): boolean {
  return canGenerateSop(session) && !shouldReuseSop(session, force) && !unresolvedGoalNotesConflict(session);
}

export const SOP_CHAR_CAP = 1200;

export function capSop(text: string, max = SOP_CHAR_CAP): string {
  const trimmed = text.trim();
  return trimmed.length <= max ? trimmed : trimmed.slice(0, max);
}

export function formatHardwareConfig(session: SessionState): string {
  const robot = session.robot ?? "unset";
  const device = deviceFor(session.robot);
  const api =
    session.hardware.apiVersion ??
    (device?.codegen === "opentrons_python" ? device.hardwarePreset.apiVersion : "unset");
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
    artifacts: session.artifacts ?? null,
    checks: checks ?? null,
    fab: { lit: Boolean(checks?.fab.lit) },
    deck_assumed: Boolean(session.deckAssumed),
    code_service: session.codeService ?? "down",
    events: session.events ?? [],
    device_id: deviceFor(session.robot)?.id ?? null,
  };
}

/** Bare well after an optional resource prefix, e.g. TIPS:A1 → A1. */
const TIP_POSITION_PREFIX = /^([A-Za-z][A-Za-z0-9_]*):([A-Ha-h][0-9]{1,2})$/;

/** Step-field aliases applied before Plan IR validate. resources[].type is not aliased. */
export const PLAN_STEP_ALIASES: Record<string, string> = {
  type: "primitive_type",
  well: "location",
  vol: "volume_ul",
  volume: "volume_ul",
  tiprack: "tip_rack",
  dest: "destination",
  dst: "destination",
  src: "source",
};

function flattenLocation(value: unknown): { value: unknown; note?: string } {
  if (value == null || typeof value !== "object" || Array.isArray(value)) {
    return { value };
  }
  const rec = value as Record<string, unknown>;
  const resource = String(rec.labware ?? rec.resource ?? rec.plate ?? "").trim();
  const well = String(rec.well ?? rec.location ?? rec.position ?? "").trim();
  if (resource && well) {
    const loc = well.includes(":") ? well : `${resource}:${well}`;
    return { value: loc, note: `You wrote a location object, normalized to ${loc}` };
  }
  return { value };
}

/** Alias step fields, flatten location objects, then strip tip_positions prefixes. */
export function normalizePlanInput(plan: Record<string, unknown>): {
  plan: Record<string, unknown>;
  notes: string[];
} {
  if (!Array.isArray(plan.steps)) return { plan, notes: [] };
  const notes: string[] = [];
  const steps = plan.steps.map((step) => {
    if (!step || typeof step !== "object" || Array.isArray(step)) return step;
    const rec = { ...(step as Record<string, unknown>) };
    for (const [alias, canonical] of Object.entries(PLAN_STEP_ALIASES)) {
      if (!Object.prototype.hasOwnProperty.call(rec, alias)) continue;
      const empty = rec[canonical] == null || rec[canonical] === "";
      if (empty) {
        rec[canonical] = rec[alias];
        notes.push(`You wrote ${alias}, normalized to ${canonical}`);
      }
      delete rec[alias];
    }
    for (const field of ["source", "destination", "location"] as const) {
      if (rec[field] == null) continue;
      const flat = flattenLocation(rec[field]);
      rec[field] = flat.value;
      if (flat.note) notes.push(flat.note);
    }
    if (!Array.isArray(rec.tip_positions)) return rec;
    rec.tip_positions = rec.tip_positions.map((item) => {
      const wrote = String(item).trim();
      const match = wrote.match(TIP_POSITION_PREFIX);
      if (!match) return typeof item === "string" ? item : wrote;
      const well = match[2].toUpperCase();
      notes.push(`You wrote ${wrote}, normalized to ${well}`);
      return well;
    });
    return rec;
  });
  return { plan: { ...plan, steps }, notes: [...new Set(notes)] };
}

export const normalizePlanTipPositions = normalizePlanInput;

/** Point the model at a fix. Schema messages are already English; append the usual traps. */
export function explainPlanErrors(errors: string[]): string[] {
  return errors.map((err) => {
    const text = err.trim();
    if (!text) return text;
    const lower = text.toLowerCase();
    if (lower.includes("tip_positions") && !/TIPS:/i.test(text)) {
      return `${text} Use bare well names like "A1", not "TIPS:A1".`;
    }
    if (lower.includes("dependencies must be a list")) {
      return `${text} Use a JSON array; [] is valid when there are no dependencies.`;
    }
    if (lower.includes("pick_tips") && lower.includes("tip")) {
      return `${text} Set tip_rack to the tiprack id in resources[] (example: "tips") and tip_positions to ["A1"].`;
    }
    if (lower.includes("must look like")) {
      return `${text} source/destination/location must be a string like plate:A1, not {well:"A1"}. Only tip_positions are bare wells.`;
    }
    if (lower.includes("needs volume_ul") || (lower.includes("volume_ul") && !lower.includes("max_volume"))) {
      return `${text} Write "volume_ul": 50, not vol or volume.`;
    }
    if (lower.includes("unsupported primitive") || lower.includes("(missing)")) {
      return `${text} Write "primitive_type" (not "type"): ASPIRATE, DISPENSE, MIX, PICK_TIPS, DROP_TIPS, or WAIT.`;
    }
    if (lower.includes("needs source") || lower.includes("needs destination") || lower.includes("needs location")) {
      return `${text} Use a string like plate:A1, not {well:"A1"}.`;
    }
    return text;
  });
}

const WELL_TOKEN = /^([A-H])(\d{1,2})$/i;

function expandWellRange(start: string, end: string): string[] {
  const parse = (well: string) => {
    const match = well.toUpperCase().match(WELL_TOKEN);
    if (!match) return null;
    return { row: match[1].charCodeAt(0), col: Number(match[2]) };
  };
  const from = parse(start);
  const to = parse(end);
  if (!from || !to) {
    return [...new Set([start.toUpperCase(), end.toUpperCase()])];
  }
  const rowLo = Math.min(from.row, to.row);
  const rowHi = Math.max(from.row, to.row);
  const colLo = Math.min(from.col, to.col);
  const colHi = Math.max(from.col, to.col);
  const out: string[] = [];
  for (let row = rowLo; row <= rowHi; row += 1) {
    for (let col = colLo; col <= colHi; col += 1) {
      out.push(`${String.fromCharCode(row)}${col}`);
    }
  }
  return out;
}

function bareWell(raw: string): string {
  const text = raw.trim();
  const idx = text.lastIndexOf(":");
  return (idx >= 0 ? text.slice(idx + 1) : text).trim().toUpperCase();
}

/** Unique tip wells named in goal/notes, e.g. TIPS:A1 through TIPS:H1. */
export function requestedTipWells(intent: string): string[] {
  const found = new Set<string>();
  const text = intent ?? "";
  const rangeRe = /TIPS:([A-H]\d{1,2})\s*(?:through|to|-|–|—)\s*TIPS:([A-H]\d{1,2})/gi;
  for (const match of text.matchAll(rangeRe)) {
    for (const well of expandWellRange(match[1], match[2])) found.add(well);
  }
  const wellRe = /TIPS:([A-H]\d{1,2})/gi;
  for (const match of text.matchAll(wellRe)) {
    found.add(match[1].toUpperCase());
  }
  return [...found];
}

export function planPickTipWells(plan: Record<string, unknown>): string[] {
  const steps = Array.isArray(plan.steps) ? plan.steps : [];
  const wells = new Set<string>();
  for (const step of steps) {
    if (!step || typeof step !== "object") continue;
    const rec = step as Record<string, unknown>;
    const kind = String(rec.primitive_type ?? rec.type ?? "").toUpperCase().replace("-", "_");
    if (kind !== "PICK_TIPS") continue;
    const pos = rec.tip_positions;
    const list = Array.isArray(pos) ? pos : pos != null ? [pos] : [];
    for (const item of list) {
      const well = bareWell(String(item ?? ""));
      if (well) wells.add(well);
    }
  }
  return [...wells];
}

export function applyTipCountOverlay(
  logicpass: LogicPassResult,
  plan: Record<string, unknown>,
  userIntent: string
): LogicPassResult {
  const requested = requestedTipWells(userIntent);
  if (requested.length <= 1) return logicpass;
  const have = new Set(planPickTipWells(plan));
  const missing = requested.filter((well) => !have.has(well));
  if (missing.length === 0) return logicpass;
  const haveLabel = [...have].join(", ") || "none";
  const issue = {
    code: "LP-TIP-COUNT",
    detail_text: `requested tip wells ${requested.join(", ")} but plan PICK_TIPS only has ${haveLabel}`,
    step_id: "pick_tips",
  };
  return {
    outcome: "fail",
    logic_pass: false,
    final_pass_v2: false,
    issues: [...(logicpass.issues ?? []), issue],
    coverage: logicpass.coverage,
    reason: logicpass.outcome === "fail" ? logicpass.reason : "LP-TIP-COUNT",
  };
}
