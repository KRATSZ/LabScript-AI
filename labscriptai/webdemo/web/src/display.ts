import type { PlanStepLike } from "./artifacts";

const LABWARE_LABELS: Record<string, string> = {
  opentrons_96_tiprack_300ul: "300 µL tips",
  opentrons_flex_96_tiprack_1000ul: "1000 µL tips",
  nest_96_wellplate_200ul_flat: "96-well plate",
  nest_12_reservoir_15ml: "12-well reservoir",
  tecan_diti_200ul_tiprack: "200 µL DiTi tips",
  tecan_96_wellplate: "96-well plate",
  hamilton_96_tiprack_300ul: "300 µL tips",
  corning_96_wellplate_360ul_flat: "96-well plate",
  trash_bin: "trash",
};

const PRIM_LABELS: Record<string, string> = {
  PICK_TIPS: "Pick tips",
  DROP_TIPS: "Drop tips",
  ASPIRATE: "Aspirate",
  DISPENSE: "Dispense",
  MIX: "Mix",
};

const LEAK_PATTERNS: RegExp[] = [
  /\bassumed_deck\s*=\s*(true|false)\b/gi,
  /\bnext_tool\s*=\s*\w+/gi,
  /\bcode_service\s*=\s*(up|down)\b/gi,
  /\bsop_chars\s*=\s*\d+/gi,
  /\bgenerate_sop\b/gi,
  /\bemit_plan\b/gi,
  /\bgenerate_code\b/gi,
  /\brun_checks\b/gi,
  /\bopen_animation\b/gi,
  /\bask_user\b/gi,
  /\bvirtual_deck\b/gi,
  /\bplr_sim\b/gi,
  /\bpyfluent_compile\b/gi,
  /\bhardware_config\b/gi,
];

type Fold = [RegExp, string];

const PHRASE_FOLDS: Fold[] = [
  [/\b(\d+(?:\.\d+)?)\s*L\s*(?:vs\.?|versus|or)\s*\1\s*(?:µL|uL)\b/gi, "$1 µL"],
  [/\b(\d+(?:\.\d+)?)\s*(?:µL|uL)\s*(?:vs\.?|versus|or)\s*\1\s*L\b/gi, "$1 µL"],
  [/\(\s*microliters?\s*,?\s*not liters?\s*\)/gi, ""],
  [/\bmicroliters?\s*,?\s*not liters?\b/gi, ""],
  [/\bassumed deck\b/gi, "standard deck"],
  [/\banalyze pass\b/gi, "checks passed"],
  [/\bsim clean,?\s*logic pass(?:,?\s*review matches your ask)?/gi, "the run matches what you asked"],
  [/\breview matches your ask\b/gi, "it matches what you asked"],
  [/\b15\s*mL reservoir\b/gi, "12-well reservoir"],
  [/\bBuilding the SOP now\.?:?\s*/gi, ""],
  [/\bWriting the SOP now\.?:?\s*/gi, ""],
  [/\bWriting it up now\.?:?\s*/gi, ""],
  [/\bDeck confirmed\.?:?\s*/gi, ""],
  [/\bConfirm volume, wells, mix, and the standard deck[^.]*\.?/gi, ""],
  [/\bnothing is written yet\.?/gi, ""],
  [/\s*Want me to tweak anything[^?\n]*\??/gi, ""],
  [/\s*Want anything (?:changed|tweaked)\??/gi, ""],
  [/\s*Say the word if you want it swapped\.?/gi, ""],
  [/\s*Want me to open(?: the)?(?: run)? animation\??/gi, ""],
  [
    /\bWatch(?:\/animation)?(?: animation)? is (?:up|ready|open)(?: too)?(?: if you want to see the run)?(?: for this run(?: too)?)?\.?:?\s*/gi,
    "The deck is on Stage. ",
  ],
  [/\bno watch(?:\/animation)? (?:for|on) \w+\.?/gi, ""],
  [/\s+and the deck animation are ready/gi, " is ready"],
  [/\bthe deck animation are ready\b/gi, "the deck is ready"],
  [
    /\s+and (?:the )?(?:on-screen )?deck (?:is|are) ready to download/gi,
    " is ready to download. The deck is on Stage",
  ],
  [/\b(?:the )?(?:on-screen )?deck (?:is|are) ready to download/gi, "The deck is on Stage"],
  [/(?:The deck is on Stage\.\s*){2,}/g, "The deck is on Stage. "],
  [/\s*Nothing runs on hardware from here\.?/gi, ""],
  [/\bFluentControl\.gwl\b/gi, "Fluent worklist"],
  [/\bFluentControl\b/gi, "Fluent"],
  [/\bPython(?:\.py|\s*\(\.py\))\s*protocol\b/gi, "Python file"],
  [/Python\.py/gi, "Python file"],
  [/Python\s*\(\.py\)/gi, "Python file"],
  [/\bPython script\s*\(\.py\)/gi, "Python file"],
  [/\bscript\s*\(\.py\)/gi, "file"],
  [/\bplus a steps\b/gi, "plus steps"],
  [/\bDeliverables are ready to download:\s*/gi, "Ready: "],
  [/\bwriting the SOP\b/gi, "writing the protocol"],
  [/\bthe SOP\b/gi, "the protocol"],
  [/\bStep JSON\b/gi, "steps"],
  [/\bPyLabRobot\b/gi, ""],
  [/\bFreedom EVO\b/gi, ""],
  [/\bResourceHolder\b/gi, ""],
  [/\bWorkcell Tree\b/gi, ""],
  [/\bPLR\b/g, ""],
  [/\btipracks?\b/gi, "tip rack"],
  [/\.gwl\b/gi, " worklist"],
];

const STAR_SLOT_FOLDS: Fold[] = [
  [/\bin slot 1\b/gi, "on the tip carrier"],
  [/\bin slot 2\b/gi, "on the plate carrier"],
  [/\bin slot 3\b/gi, "in the reagents trough"],
];

const TIDY_FOLDS: Fold[] = [
  [/\bworklist\s+worklist\b/gi, "worklist"],
  [/\(\s*\)/g, ""],
  [/^[:\s—–-]+/, ""],
  [/^(?=\d[\d.]*\s*µL\s+tips\b)/i, "Standard deck — "],
  [/([.!?])([A-Z])/g, "$1 $2"],
  [/[ \t]+\n/g, "\n"],
  [/\n{3,}/g, "\n\n"],
  [/[ \t]{2,}/g, " "],
  [/[ \t]+([,.;])/g, "$1"],
  [/\n{2,}/g, "\n\n"],
];

function applyFolds(text: string, folds: Fold[]): string {
  let out = text;
  for (const [re, to] of folds) {
    re.lastIndex = 0;
    out = out.replace(re, to);
  }
  return out;
}

function asStep(step: unknown): PlanStepLike {
  return step && typeof step === "object" ? (step as PlanStepLike) : {};
}

function titleCase(raw: string): string {
  return raw
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\b\w/g, (ch) => ch.toUpperCase());
}

/** Scientist-facing labware name. Schema ids stay in downloads and the model prompt. */
export function labwareLabel(id: string): string {
  const key = id.trim();
  if (!key) return "";
  const mapped = LABWARE_LABELS[key] ?? LABWARE_LABELS[key.toLowerCase()];
  if (mapped) return mapped;
  if (!key.includes("_") && key.length < 24) return key;
  return key
    .replace(/_/g, " ")
    .replace(/\b(\d+)\s*ul\b/gi, "$1 µL")
    .replace(/\b(opentrons|nest|tecan|hamilton|corning)\b/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}

function friendlyRef(ref: string): string {
  const trimmed = ref.trim();
  const split = trimmed.match(/^([^:]+):(.+)$/);
  if (!split) return labwareLabel(trimmed) || trimmed;
  return `${labwareLabel(split[1]) || split[1]} ${split[2]}`;
}

function primitiveLabel(step: PlanStepLike): string {
  const prim = String(step.primitive_type ?? step.type ?? "")
    .toUpperCase()
    .replace(/-/g, "_");
  if (!prim || prim === "?") return "";
  return PRIM_LABELS[prim] ?? titleCase(prim);
}

/** Stage/Artifacts line: Pick tips — A1, not PICK_TIPS. */
export function planStepDisplay(step: unknown): string {
  const s = asStep(step);
  const verb = primitiveLabel(s);
  const vol = s.volume_ul != null && Number.isFinite(Number(s.volume_ul)) ? `${s.volume_ul} µL` : "";
  const source = typeof s.source === "string" && s.source.trim() ? friendlyRef(s.source) : "";
  const dest = typeof s.destination === "string" && s.destination.trim() ? friendlyRef(s.destination) : "";
  const loc = typeof s.location === "string" && s.location.trim() ? friendlyRef(s.location) : "";
  const rack = typeof s.tip_rack === "string" && s.tip_rack.trim() ? labwareLabel(s.tip_rack) || s.tip_rack : "";
  const tipList = Array.isArray(s.tip_positions)
    ? s.tip_positions.filter((well) => typeof well === "string" && well.trim())
    : typeof s.tip_positions === "string" && s.tip_positions.trim()
      ? [s.tip_positions.trim()]
      : [];
  const tips = tipList.join(", ");
  let route = "";
  if (source && dest) route = `${source} → ${dest}`;
  else if (source) route = source;
  else if (dest) route = dest;
  else if (loc) route = loc;
  else if (tips) route = rack ? `${rack} ${tips}` : tips;
  return [verb, vol, route].filter(Boolean).join(" — ");
}

function escapeRe(name: string): string {
  return name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function robotNames(label: string): string[] {
  return [label, "Tecan Fluent", "Hamilton STAR", "Hamilton Vantage", "OT-2", "Flex", "Tecan", "Hamilton"]
    .filter((name) => name.trim())
    .sort((a, b) => b.length - a.length);
}

/** Strip schema leftovers the model sometimes echoes into chat. */
export function sanitizeAssistantText(text: string, robot?: string | null): string {
  let out = applyFolds(text, LEAK_PATTERNS.map((re) => [re, ""] as Fold));
  out = applyFolds(out, PHRASE_FOLDS);
  if (robot === "Hamilton" || robot === "Vantage") out = applyFolds(out, STAR_SLOT_FOLDS);
  return applyFolds(out, TIDY_FOLDS).trim();
}

/** Header run line: robot once, no deck recap. */
export function headerGoalPreview(label: string, goal: string): string {
  let text = goal.replace(/\s+/g, " ").trim();
  const names = robotNames(label);
  for (const name of names) {
    const re = new RegExp(`^${escapeRe(name)}(?:\\s*[.:,—–-]\\s*|\\s+)`, "i");
    if (re.test(text)) {
      text = text.replace(re, "");
      break;
    }
  }
  text = text.replace(/\bStandard deck\b[\s\S]*/i, "").trim();
  text = (text.split(/(?<=[.!?])\s+/)[0] || text).replace(/[.;:\s]+$/g, "").trim();
  text = text.replace(/\bplate well\b/gi, "well");
  for (const name of names) {
    const escaped = escapeRe(name);
    text = text.replace(new RegExp(`\\s*\\(\\s*${escaped}\\s*\\)`, "i"), "").trim();
    text = text.replace(new RegExp(`\\s+on(?:\\s+the|\\s+an?)?\\s+${escaped}\\b`, "i"), "").trim();
    text = text.replace(new RegExp(`\\s+using(?:\\s+the|\\s+an?)?\\s+${escaped}\\b`, "i"), "").trim();
    text = text.replace(new RegExp(`\\s+with(?:\\s+the|\\s+an?)?\\s+${escaped}\\b`, "i"), "").trim();
    text = text.replace(new RegExp(`[,;]\\s*(?:the\\s+|a\\s+)?${escaped}\\b`, "gi"), "").trim();
  }
  text = applyFolds(text, [
    [/\s+on(?:\s+the|\s+a)?\s+\d+-well plate\b/gi, ""],
    [/,?\s*(?:one|\d+)\s+samples?\b/gi, ""],
    [/,?\s*no mix\b/gi, ""],
    [/,?\s*OT-2\s+p300(?:\s+single)?\b/gi, ""],
    [/,?\s*(?:using|with) the(?:\s+[\w-]+)*$/i, ""],
    [/,?\s+(?:with|using|on)\s+(?:the|an?)\s*$/i, ""],
  ]).trim();
  for (const name of names) {
    text = text.replace(new RegExp(`\\s*\\(\\s*${escapeRe(name)}\\s*\\)`, "i"), "").trim();
    text = text.replace(new RegExp(`\\s*\\(\\s*${escapeRe(name)}[^)]*$`, "i"), "").trim();
  }
  text = text.replace(/\s*\(\s*\)/g, "").trim();
  text = text.replace(/[.,;:\s]+$/g, "").replace(/\s{2,}/g, " ").trim();
  if (!text) text = goal.replace(/\s+/g, " ").trim();
  if (text.length > 72) return `${text.slice(0, 69).trim()}…`;
  return text;
}

/** True only for a real notes draft — not empty, "none", or a placeholder. */
export function hasAttachedNotes(doc: string | null | undefined): boolean {
  const text = (doc ?? "").trim();
  if (!text) return false;
  if (/^(none|n\/a|na|null|undefined|-)$/i.test(text)) return false;
  return true;
}
