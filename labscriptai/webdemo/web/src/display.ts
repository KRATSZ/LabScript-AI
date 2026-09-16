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

/** Strip schema leftovers the model sometimes echoes into chat. */
export function sanitizeAssistantText(text: string): string {
  let out = text;
  for (const re of LEAK_PATTERNS) {
    re.lastIndex = 0;
    out = out.replace(re, "");
  }
  return out
    .replace(/\b(\d+(?:\.\d+)?)\s*L\s*(?:vs\.?|versus|or)\s*\1\s*(?:µL|uL)\b/gi, "$1 µL")
    .replace(/\b(\d+(?:\.\d+)?)\s*(?:µL|uL)\s*(?:vs\.?|versus|or)\s*\1\s*L\b/gi, "$1 µL")
    .replace(/\(\s*microliters?\s*,?\s*not liters?\s*\)/gi, "")
    .replace(/\bmicroliters?\s*,?\s*not liters?\b/gi, "")
    .replace(/\bassumed deck\b/gi, "standard deck")
    .replace(/\banalyze pass\b/gi, "checks passed")
    .replace(/\bsim clean,?\s*logic pass(?:,?\s*review matches your ask)?/gi, "the run matches what you asked")
    .replace(/\breview matches your ask\b/gi, "it matches what you asked")
    .replace(/\b15\s*mL reservoir\b/gi, "12-well reservoir")
    .replace(/\bBuilding the SOP now\.?\s*/gi, "")
    .replace(/\bWriting the SOP now\.?\s*/gi, "")
    .replace(/\bWriting it up now\.?\s*/gi, "")
    .replace(/\bDeck confirmed\.?\s*/gi, "")
    .replace(/\bConfirm volume, wells, mix, and the standard deck[^.]*\.?/gi, "")
    .replace(/\bnothing is written yet\.?/gi, "")
    .replace(/\s*Want me to tweak anything[^?\n]*\??/gi, "")
    .replace(/\s*Say the word if you want it swapped\.?/gi, "")
    .replace(/\s*Want me to open(?: the)?(?: run)? animation\??/gi, "")
    .replace(/\s*Watch animation is up\.?/gi, "")
    .replace(/\s*Nothing runs on hardware from here\.?/gi, "")
    .replace(/([.!?])([A-Z])/g, "$1 $2")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/[ \t]{2,}/g, " ")
    .replace(/[ \t]+([,.;])/g, "$1")
    .replace(/\n{2,}/g, "\n\n")
    .trim();
}

/** Header run line: robot once, no deck recap. */
export function headerGoalPreview(label: string, goal: string): string {
  let text = goal.replace(/\s+/g, " ").trim();
  const names = [label, "Tecan Fluent", "Hamilton STAR", "Hamilton Vantage", "OT-2", "Flex", "Tecan", "Hamilton"]
    .filter((name) => name.trim())
    .sort((a, b) => b.length - a.length);
  for (const name of names) {
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const re = new RegExp(`^${escaped}(?:\\s*[.:,—–-]\\s*|\\s+)`, "i");
    if (re.test(text)) {
      text = text.replace(re, "");
      break;
    }
  }
  text = text.replace(/\bStandard deck\b[\s\S]*/i, "").trim();
  const first = text.split(/(?<=[.!?])\s+/)[0] || text;
  text = first.replace(/[.\s]+$/g, "").trim();
  for (const name of names) {
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    text = text.replace(new RegExp(`\\s+on(?:\\s+the)?\\s+${escaped}$`, "i"), "").trim();
  }
  if (!text) text = goal.replace(/\s+/g, " ").trim();
  if (text.length > 88) return `${text.slice(0, 85).trim()}…`;
  return text;
}
