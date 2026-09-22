import { randomUUID } from "node:crypto";
import type { ChecksResult, LogicPassResult } from "./gate.ts";
import {
  DEVICE_REGISTRY,
  HARDWARE_PRESETS,
  PCR_PLATE_OT,
  PRESET_ROBOT,
  ROBOT_PRESET,
  deviceFor,
  type HardwarePresetId,
  type PlanBackend,
  type RobotModel,
} from "./devices.ts";

export type { HardwarePresetId, PlanBackend, RobotModel };
export { DEVICE_REGISTRY, HARDWARE_PRESETS, PCR_PLATE_OT, deviceFor, deviceForId, usesFluentCompile, usesHamiltonCompile, hamiltonFamily } from "./devices.ts";
export type { DeviceProfile } from "./devices.ts";

export type Phase =
  | "need_goal"
  | "need_doc"
  | "need_robot"
  | "need_hw_slots"
  | "ready";

export type UiLang = "en" | "zh";

export function parseUiLang(value: unknown): UiLang {
  const raw = String(value ?? "").trim().toLowerCase();
  if (raw === "zh" || raw === "zh-cn" || raw === "zh-hans" || raw === "chinese" || raw === "中文") {
    return "zh";
  }
  return "en";
}

export function goalMentionsPcr(...texts: Array<string | undefined>): boolean {
  return texts.some((text) => /\bpcr\b|聚合酶链式|热循环|扩增仪|上机pcr/i.test(text || ""));
}

function plateSlotFor(robot: RobotModel | undefined): string | undefined {
  if (robot === "OT-2" || robot === "Hamilton" || robot === "Vantage" || robot === "Tecan") return "2";
  if (robot === "Flex") return "D2";
  return undefined;
}

/** PCR mix uses a PCR plate on OT-2/Flex without treating it as extra labware. */
export function applyPcrFriendlyDeck(session: SessionState): void {
  if (!session.robot || !session.deckAssumed) return;
  if (!goalMentionsPcr(session.goal, session.doc === "none" ? "" : session.doc)) return;
  const slot = plateSlotFor(session.robot);
  if (!slot) return;
  const current = session.hardware.deck[slot];
  if (!current || !/wellplate|plate/i.test(current) || /pcr/i.test(current)) return;
  if (session.robot === "OT-2" || session.robot === "Flex") {
    session.hardware.deck[slot] = PCR_PLATE_OT;
  }
}

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
  /** The later user message that answered the volume question. */
  conflictReplyText?: string;
  /** True after a later user turn confirmed a volume via ask_user. */
  draftConflictResolved?: boolean;
  /** True after the user answers the first clarifying round (not the start-form goal). */
  intakeDone?: boolean;
  /** Chat + SOP language. Default English. */
  language?: UiLang;
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

const VOL_UNIT = "µl|ul|μl|microlit(?:er|re)s?|ml|millilit(?:er|re)s?|微升|毫升";
const CN_NUMERAL = "零〇一二两三四五六七八九十百千万兩壹";
const NUMBER_WORD =
  "zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand";
const ONES: Record<string, number> = {
  zero: 0,
  one: 1,
  two: 2,
  three: 3,
  four: 4,
  five: 5,
  six: 6,
  seven: 7,
  eight: 8,
  nine: 9,
  ten: 10,
  eleven: 11,
  twelve: 12,
  thirteen: 13,
  fourteen: 14,
  fifteen: 15,
  sixteen: 16,
  seventeen: 17,
  eighteen: 18,
  nineteen: 19,
};
const TENS: Record<string, number> = {
  twenty: 20,
  thirty: 30,
  forty: 40,
  fifty: 50,
  sixty: 60,
  seventy: 70,
  eighty: 80,
  ninety: 90,
};
/** Tip / PCR-well / reservoir *capacity* in notes is not a transfer-volume fight. */
const CAPACITY_CTX =
  /hold|holds|capacity|max(?:imum)?|already|contains|start(?:s|ing)?|initial|tip[\s_-]*rack|\btips?\b|枪头|diti|reservoir|储液槽|trough|trash|废液|\d+-well|well[\s_-]*plate|wellplate|pcr|_[\d.]+ul_|孔\s*pcr|孔板/i;
const TRANSFER_LEAD = `\\b(?:transfer(?:red|s|ing)?|aspirate[ds]?|dispense[ds]?)\\s+`;
const REAL_LEAD = `\\b(?:real(?:ly)?|actual(?:ly)?)\\b[\\s\\S]{0,48}?`;

function unitToUl(amount: number, unit: string): number {
  const n = unit.toLowerCase();
  const ul = n === "ml" || n.startsWith("millilit") || n === "毫升" ? amount * 1000 : amount;
  return Math.round(ul * 1000) / 1000;
}

function parseWordNumber(words: string): number | undefined {
  const tokens = words
    .toLowerCase()
    .replace(/-/g, " ")
    .split(/\s+/)
    .filter((token) => token && token !== "and");
  if (!tokens.length) return undefined;
  let total = 0;
  let current = 0;
  for (const token of tokens) {
    if (token in ONES) current += ONES[token];
    else if (token in TENS) current += TENS[token];
    else if (token === "hundred") current = (current || 1) * 100;
    else if (token === "thousand") {
      total += (current || 1) * 1000;
      current = 0;
    } else return undefined;
  }
  return total + current;
}

const CN_DIGIT: Record<string, number> = {
  零: 0, 〇: 0, 一: 1, 壹: 1, 二: 2, 两: 2, 兩: 2, 三: 3, 四: 4,
  五: 5, 六: 6, 七: 7, 八: 8, 九: 9,
};
const CN_UNIT: Record<string, number> = { 十: 10, 百: 100, 千: 1000, 万: 10000 };

function parseChineseNumber(text: string): number | undefined {
  if (!text) return undefined;
  let total = 0;
  let current = 0;
  let seen = false;
  for (const ch of text) {
    if (ch in CN_DIGIT) {
      current = CN_DIGIT[ch];
      seen = true;
      continue;
    }
    const unit = CN_UNIT[ch];
    if (unit == null) return undefined;
    total += (current || 1) * unit;
    current = 0;
    seen = true;
  }
  return seen ? total + current : undefined;
}

function volumeMentions(text: string, prefix = ""): { ul: number; index: number }[] {
  if (!text) return [];
  const found: { ul: number; index: number }[] = [];
  const numeric = new RegExp(`${prefix}(\\d+(?:\\.\\d+)?)\\s*(${VOL_UNIT})`, "gi");
  for (const match of text.matchAll(numeric)) {
    found.push({ ul: unitToUl(Number(match[1]), match[2]), index: match.index ?? 0 });
  }
  const wordBody = `((?:${NUMBER_WORD})(?:[\\s-]+(?:and|${NUMBER_WORD}))*)`;
  const words = new RegExp(`${prefix}\\b${wordBody}\\s*(${VOL_UNIT})`, "gi");
  for (const match of text.matchAll(words)) {
    const parsed = parseWordNumber(match[1]);
    if (parsed == null) continue;
    found.push({ ul: unitToUl(parsed, match[2]), index: match.index ?? 0 });
  }
  const chinese = new RegExp(`${prefix}([${CN_NUMERAL}]+)\\s*(${VOL_UNIT})`, "gi");
  for (const match of text.matchAll(chinese)) {
    const parsed = parseChineseNumber(match[1]);
    if (parsed == null) continue;
    found.push({ ul: unitToUl(parsed, match[2]), index: match.index ?? 0 });
  }
  return found;
}

function ulAmounts(text: string): number[] {
  return [...new Set(volumeMentions(text).map((item) => item.ul))];
}

function contextAt(text: string, index: number, span = 40): string {
  return text.slice(Math.max(0, index - span), Math.min(text.length, index + span)).toLowerCase();
}

function competingNoteVolumes(goal = "", notes = ""): { goalVols: number[]; extra: number[]; ignoreGoal: boolean } {
  const goalVols = [...new Set(ulAmounts(goal))];
  const ignoreGoal = goalVols.some((vol) =>
    new RegExp(`\\bignore(?:\\s+the)?\\s+${vol}\\b`, "i").test(notes)
  );
  const competing: number[] = [];
  for (const { ul } of [
    ...volumeMentions(notes, REAL_LEAD),
    ...volumeMentions(notes, TRANSFER_LEAD),
  ]) {
    if (!goalVols.includes(ul)) competing.push(ul);
  }
  for (const { ul, index } of volumeMentions(notes)) {
    if (goalVols.includes(ul)) continue;
    const ctx = contextAt(notes, index);
    if (CAPACITY_CTX.test(ctx)) continue;
    if (/\b(?:do not|don't|not)\s+clamp\b/.test(ctx)) continue;
    competing.push(ul);
  }
  return { goalVols, extra: [...new Set(competing)], ignoreGoal };
}

export function formatGoalNotesVolumeConflict(
  goalVols: number[],
  extra: number[],
  language: UiLang = "en"
): string {
  const notes = extra.length ? extra.join("/") : language === "zh" ? "覆盖" : "override";
  if (language === "zh") return `目标 ${goalVols.join("/")} µL，备注 ${notes} µL`;
  return `goal ${goalVols.join("/")} µL vs notes ${notes} µL`;
}

/** Goal vs notes transfer-volume fight. Capacity / initial-fill numbers are not a fight. */
export function goalNotesVolumeConflict(goal = "", doc = "", language: UiLang = "en"): string | null {
  const notes = doc.trim();
  if (!notes || notes === "none") return null;
  const { goalVols, extra, ignoreGoal } = competingNoteVolumes(goal, notes);
  if (!goalVols.length) return null;
  if (!ignoreGoal && extra.length === 0) return null;
  return formatGoalNotesVolumeConflict(goalVols, extra, language);
}

export function conflictChoiceVolumes(goal = "", doc = ""): number[] {
  if (!goalNotesVolumeConflict(goal, doc)) return [];
  const { goalVols, extra } = competingNoteVolumes(goal, (doc ?? "").trim());
  return [...new Set([...goalVols, ...extra])];
}

const REJECTED_VOLUME =
  /(?:(?:do\s+)?not|don't|dont|no|ignore|except|instead\s+of|rather\s+than|skip)\s+(?:use\s+|the\s+)?(\d+(?:\.\d+)?)/gi;

function allowedNumbersInText(text: string, allowed: number[]): number[] {
  const fromUl = ulAmounts(text).filter((vol) => allowed.includes(vol));
  const bare = [...text.matchAll(/\b(\d+(?:\.\d+)?)\b/g)]
    .map((match) => Number(match[1]))
    .filter((vol) => allowed.includes(vol));
  return [...new Set([...fromUl, ...bare])];
}

function rejectedVolumesInText(text: string, allowed: number[]): number[] {
  return [
    ...new Set(
      [...text.matchAll(REJECTED_VOLUME)]
        .map((match) => Number(match[1]))
        .filter((vol) => allowed.includes(vol))
    ),
  ];
}

/** Unique allowed volume the text picks. µL and unit-less numbers count; rejected volumes do not. */
export function chosenVolumeInText(
  text: string,
  allowed: number[],
  opts?: { leftover?: boolean }
): number | undefined {
  if (!text.trim() || !allowed.length) return undefined;
  const mentioned = allowedNumbersInText(text, allowed);
  const rejected = rejectedVolumesInText(text, allowed);
  const positive = mentioned.filter((vol) => !rejected.includes(vol));
  if (positive.length === 1) return positive[0];
  if (opts?.leftover !== false && rejected.length && positive.length === 0) {
    const leftover = allowed.filter((vol) => !rejected.includes(vol));
    if (leftover.length === 1) return leftover[0];
  }
  return undefined;
}

export function unresolvedGoalNotesConflict(session: SessionState): string | null {
  if (session.draftConflictResolved) return null;
  return goalNotesVolumeConflict(session.goal ?? "", session.doc ?? "", session.language ?? "en");
}

/** First ask_user during a conflict: record the question, do not take a side. */
export function beginGoalNotesConflictAsk(session: SessionState): string | null {
  const conflict = unresolvedGoalNotesConflict(session);
  if (!conflict || session.conflictAskedAt != null) return conflict;
  session.conflictAskedAt = Array.isArray(session.messages) ? session.messages.length : 0;
  session.conflictUserReplied = false;
  session.conflictReplyText = undefined;
  session.draftConflictResolved = false;
  session.sop = undefined;
  session.code = undefined;
  session.plan = undefined;
  session.artifacts = undefined;
  session.lastChecks = undefined;
  session.hasPassedChecks = undefined;
  return conflict;
}

export function canResolveGoalNotesConflict(session: SessionState, incomingGoal?: string): boolean {
  if (!session.conflictUserReplied || session.draftConflictResolved) return false;
  const goal = (incomingGoal ?? "").trim();
  if (!goal) return false;
  const allowed = conflictChoiceVolumes(session.goal ?? "", session.doc ?? "");
  if (!allowed.length) return false;
  const fromReply = chosenVolumeInText(session.conflictReplyText ?? "", allowed);
  if (fromReply == null) return false;
  const fromGoal = chosenVolumeInText(goal, allowed, { leftover: false });
  return fromGoal === fromReply;
}

/** A later user chat turn — not the start form, not a same-turn follow-up. */
export function markConflictUserReply(session: SessionState, userText: string): void {
  if (!userText.trim()) return;
  if (session.draftConflictResolved) return;
  if (session.conflictAskedAt == null && !unresolvedGoalNotesConflict(session)) return;
  session.conflictUserReplied = true;
  session.conflictReplyText = userText.trim();
}

/** Follow-up chat (not the empty first turn) unlocks SOP/plan generation. */
export function markIntakeReply(session: SessionState, userText: string): void {
  if (!userText.trim()) return;
  session.intakeDone = true;
}

export function intakeOpen(session: SessionState): boolean {
  return !session.intakeDone && !session.sop?.trim();
}

export function resolveGoalNotesConflict(session: SessionState): void {
  session.draftConflictResolved = true;
  session.conflictUserReplied = true;
  session.conflictReplyText = undefined;
  session.intakeDone = true;
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
  ];
  if (session.robot === "Tecan") {
    parts.push("fca_1000 is the FCA pipette (Fluent Channel Arm). Assumed Fluent tips are 200 µL DiTi.");
  }
  parts.push(goal);
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
  if (intakeOpen(session)) {
    missing.push("ask_user — confirm volume, wells, and assumed deck with the user first");
  }
  return missing;
}

function pipetteUnset(value: string | undefined): boolean {
  return !value || value === "None";
}

const DECK_SLOT_LABELS: Record<string, string> = {
  opentrons_96_tiprack_300ul: "300 µL tips",
  opentrons_flex_96_tiprack_1000ul: "1000 µL tips",
  nest_96_wellplate_200ul_flat: "96-well plate",
  nest_96_wellplate_100ul_pcr_full_skirt: "96-well PCR plate",
  opentrons_96_wellplate_200ul_pcr_full_skirt: "96-well PCR plate",
  nest_12_reservoir_15ml: "12-well reservoir",
  tecan_diti_200ul_tiprack: "200 µL DiTi tips",
  tecan_96_wellplate: "96-well plate",
  hamilton_96_tiprack_300ul: "300 µL tips",
  corning_96_wellplate_360ul_flat: "96-well plate",
};

const DECK_SLOT_LABELS_ZH: Record<string, string> = {
  opentrons_96_tiprack_300ul: "300 µL 枪头",
  opentrons_flex_96_tiprack_1000ul: "1000 µL 枪头",
  nest_96_wellplate_200ul_flat: "96 孔板",
  nest_96_wellplate_100ul_pcr_full_skirt: "96 孔 PCR 板",
  opentrons_96_wellplate_200ul_pcr_full_skirt: "96 孔 PCR 板",
  nest_12_reservoir_15ml: "12 孔储液槽",
  tecan_diti_200ul_tiprack: "200 µL DiTi 枪头",
  tecan_96_wellplate: "96 孔板",
  hamilton_96_tiprack_300ul: "300 µL 枪头",
  corning_96_wellplate_360ul_flat: "96 孔板",
};

function deckSlotLabel(labware: string): string {
  return DECK_SLOT_LABELS[labware] ?? DECK_SLOT_LABELS[labware.toLowerCase()] ?? labware.replace(/_/g, " ");
}

function deckSlotLabelZh(labware: string): string {
  return DECK_SLOT_LABELS_ZH[labware] ?? DECK_SLOT_LABELS_ZH[labware.toLowerCase()] ?? deckSlotLabel(labware);
}

function hamiltonDeckPhrase(deck: Record<string, string>): string {
  const tips = deckSlotLabel(deck["1"] || "hamilton_96_tiprack_300ul");
  const plate = deckSlotLabel(deck["2"] || "corning_96_wellplate_360ul_flat");
  const trough = deckSlotLabel(deck["3"] || "nest_12_reservoir_15ml");
  return `${tips} on the tip carrier (rails 1–6), ${plate} on the plate carrier (rails 8–13), ${trough} in the reagents trough (rail 15)`;
}

function vantageDeckPhrase(deck: Record<string, string>): string {
  const tips = deckSlotLabel(deck["1"] || "hamilton_96_tiprack_300ul");
  const plate = deckSlotLabel(deck["2"] || "corning_96_wellplate_360ul_flat");
  const trough = deckSlotLabel(deck["3"] || "nest_12_reservoir_15ml");
  return `${tips}, ${plate}, and ${trough} on the 1.3 m rails`;
}

function namedDeckPhrase(robot: RobotModel | undefined, deck: Record<string, string>): string {
  const slots = Object.entries(deck).sort((a, b) => a[0].localeCompare(b[0], undefined, { numeric: true }));
  if (!slots.length) return "tips, 96-well plate, 12-well reservoir";
  if (robot === "Hamilton") return hamiltonDeckPhrase(deck);
  if (robot === "Vantage") return vantageDeckPhrase(deck);
  if (robot === "Flex") {
    return slots.map(([slot, labware]) => `${deckSlotLabel(labware)} in ${slot}`).join(", ");
  }
  return slots.map(([slot, labware]) => `${deckSlotLabel(labware)} in slot ${slot}`).join(", ");
}

function namedDeckPhraseZh(robot: RobotModel | undefined, deck: Record<string, string>): string {
  const slots = Object.entries(deck).sort((a, b) => a[0].localeCompare(b[0], undefined, { numeric: true }));
  if (!slots.length) return "枪头、96 孔板、12 孔储液槽";
  if (robot === "Hamilton") {
    const tips = deckSlotLabelZh(deck["1"] || "hamilton_96_tiprack_300ul");
    const plate = deckSlotLabelZh(deck["2"] || "corning_96_wellplate_360ul_flat");
    const trough = deckSlotLabelZh(deck["3"] || "nest_12_reservoir_15ml");
    return `${tips}在吸头载架（导轨 1–6），${plate}在板载架（导轨 8–13），${trough}在试剂槽（导轨 15）`;
  }
  if (robot === "Vantage") {
    const tips = deckSlotLabelZh(deck["1"] || "hamilton_96_tiprack_300ul");
    const plate = deckSlotLabelZh(deck["2"] || "corning_96_wellplate_360ul_flat");
    const trough = deckSlotLabelZh(deck["3"] || "nest_12_reservoir_15ml");
    return `${tips}、${plate}、${trough}在 1.3 m 导轨上`;
  }
  if (robot === "Flex") {
    return slots.map(([slot, labware]) => `${deckSlotLabelZh(labware)}在 ${slot}`).join("，");
  }
  return slots.map(([slot, labware]) => `${deckSlotLabelZh(labware)}在 ${slot} 号槽`).join("，");
}

/** One-line first-turn confirm. Never “nothing is written yet.” */
export function intakeConfirmLine(session: SessionState): string {
  const label = deviceFor(session.robot)?.label ?? "this robot";
  if (session.language === "zh") {
    return `${label}，标准台面：${namedDeckPhraseZh(session.robot, session.hardware.deck)}。若相符请回复。`;
  }
  const deck = namedDeckPhrase(session.robot, session.hardware.deck);
  return `${label}, standard deck: ${deck}. Reply if that matches.`;
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
  applyPcrFriendlyDeck(session);
}

export function applyForm(
  session: SessionState,
  input: { goal: string; doc?: string; robot?: string; language?: string }
): SessionState {
  const explicit = input.robot != null && String(input.robot).trim() !== "";
  const selectedRobot = explicit
    ? parseRobot(String(input.robot).trim())
    : undefined;
  if (explicit && !selectedRobot) throw new Error("invalid robot");
  session.goal = input.goal.trim();
  const doc = (input.doc ?? "").trim();
  session.doc = doc ? doc : "none";
  session.sop = undefined;
  session.conflictAskedAt = undefined;
  session.conflictUserReplied = undefined;
  session.conflictReplyText = undefined;
  session.draftConflictResolved = undefined;
  session.intakeDone = undefined;
  if (input.language != null) session.language = parseUiLang(input.language);
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
  applyPcrFriendlyDeck(session);
  refreshPhase(session);
  return session;
}

export function parseRobot(value: string | undefined): RobotModel | undefined {
  return deviceFor(value)?.legacyRobot;
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
  applyPcrFriendlyDeck(session);
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
    session.conflictReplyText = undefined;
    session.draftConflictResolved = undefined;
  }
  refreshPhase(session);
  return session;
}

export interface AskUserInput {
  goal?: string;
  doc?: string;
  robot?: string;
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
  session.conflictReplyText = undefined;
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
  const named = parseRobot(input.robot) ?? (!session.robot ? inferRobotFromText(session.goal ?? "") : undefined);
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
    applyPcrFriendlyDeck(session);
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

export function setSessionLanguage(session: SessionState, language: unknown): UiLang {
  session.language = parseUiLang(language);
  return session.language;
}

export function capSop(text: string, max = SOP_CHAR_CAP): string {
  const trimmed = text.trim();
  return trimmed.length <= max ? trimmed : trimmed.slice(0, max);
}

export function formatHardwareConfig(session: SessionState): string {
  const device = deviceFor(session.robot);
  const robot = device?.label ?? session.robot ?? "unset";
  const api =
    session.hardware.apiVersion ??
    (device?.codegen === "opentrons_python" ? device.hardwarePreset.apiVersion : "unset");
  const deckEntries = Object.entries(session.hardware.deck);
  const deck = deckEntries.length
    ? deckEntries.map(([slot, labware]) => `  ${slot}: ${labware}`).join("\n")
    : "  (No labware configured)";
  const lines = [
    `Robot Model: ${robot}`,
    `API Version: ${api}`,
    `Left Pipette: ${session.hardware.leftPipette || "None"}`,
    `Right Pipette: ${session.hardware.rightPipette || "None"}`,
    `Use Gripper: ${session.hardware.useGripper ?? false}`,
    `Plan backend: ${planBackendFor(session.robot)}`,
  ];
  if (device?.id === "tecan_fluent") {
    lines.push(
      "PLR sim: PyLabRobot has no Fluent deck — virtual_deck/plr_sim reuse Freedom EVO 200 µL LiHa DiTi geometry. Compile is pyFluent FluentControl .gwl, not EVOware."
    );
  }
  if (goalMentionsPcr(session.goal, session.doc === "none" ? "" : session.doc)) {
    lines.push(
      "PCR: mix/setup is liquid handling on the sample plate (PCR plate is a standard-deck variant, 100 µL wells on OT-2/Flex). 8 samples = A1–H1 unless named. Do not refuse PCR. Thermocycler cycling is optional OT-2/Flex Python (load_module) only if the user asked to cycle temperatures — not required for mix prep. Hamilton/Tecan: liquid setup only. Stay within tip and well max volumes."
    );
  }
  lines.push("Deck Layout:", deck);
  return lines.join("\n");
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
    device_label: deviceFor(session.robot)?.label ?? null,
    device_note: deviceFor(session.robot)?.note ?? null,
    intake_done: Boolean(session.intakeDone),
    language: session.language ?? "en",
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
