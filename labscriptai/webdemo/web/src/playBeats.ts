import { labwareLabel, planStepDisplay } from "./display";
import type { PlanStepLike } from "./artifacts";

export type DeckSlot = "tips" | "plate" | "reservoir";

export interface PlayBeat {
  kind: DeckSlot | "mix";
  slot: DeckSlot;
  label: string;
}

function asStep(step: unknown): PlanStepLike {
  return step && typeof step === "object" ? (step as PlanStepLike) : {};
}

function primitive(step: PlanStepLike): string {
  return String(step.primitive_type ?? step.type ?? "")
    .toUpperCase()
    .replace(/-/g, "_");
}

function slotFromRef(ref: string, fallback: DeckSlot): DeckSlot {
  const lower = ref.toLowerCase();
  if (/tip|diti/.test(lower)) return "tips";
  if (/reservoir|trough|troughs/.test(lower)) return "reservoir";
  if (/plate|well|dest/.test(lower)) return "plate";
  return fallback;
}

export function playBeatsFromSteps(steps: unknown[]): PlayBeat[] {
  const beats: PlayBeat[] = [];
  for (const raw of steps) {
    const s = asStep(raw);
    const prim = primitive(s);
    const label = planStepDisplay(s);
    if (!label) continue;
    if (prim === "PICK_TIPS" || prim === "DROP_TIPS") {
      beats.push({ kind: "tips", slot: "tips", label });
    } else if (prim === "ASPIRATE") {
      const ref = `${s.source ?? ""} ${s.location ?? ""}`;
      const slot = slotFromRef(ref, "reservoir");
      beats.push({ kind: slot, slot, label });
    } else if (prim === "DISPENSE") {
      const ref = `${s.destination ?? ""} ${s.location ?? ""}`;
      const slot = slotFromRef(ref, "plate");
      beats.push({ kind: slot, slot, label });
    } else if (prim === "MIX") {
      const ref = `${s.location ?? ""} ${s.destination ?? ""}`;
      const slot = slotFromRef(ref, "plate");
      beats.push({ kind: "mix", slot, label });
    }
  }
  return beats;
}

export function playBeatsFromAnalyze(analyze: Record<string, unknown> | null): PlayBeat[] {
  if (!analyze || !Array.isArray(analyze.commands)) return [];
  const beats: PlayBeat[] = [];
  for (const cmd of analyze.commands) {
    if (!cmd || typeof cmd !== "object") continue;
    const type = String((cmd as { commandType?: unknown }).commandType ?? "");
    const lower = type.toLowerCase();
    if (lower.includes("pickup") || lower === "pickuptip") {
      beats.push({ kind: "tips", slot: "tips", label: "Pick tips" });
    } else if (lower.includes("droptip")) {
      beats.push({ kind: "tips", slot: "tips", label: "Drop tips" });
    } else if (lower.includes("aspirate")) {
      beats.push({ kind: "reservoir", slot: "reservoir", label: "Aspirate" });
    } else if (lower.includes("dispense")) {
      beats.push({ kind: "plate", slot: "plate", label: "Dispense" });
    } else if (lower.includes("mix")) {
      beats.push({ kind: "mix", slot: "plate", label: "Mix" });
    }
  }
  return beats;
}

export function deckSlots(deck: Record<string, string>): Record<DeckSlot, { slot: string; name: string }> {
  const out: Record<DeckSlot, { slot: string; name: string }> = {
    tips: { slot: "", name: "Tips" },
    plate: { slot: "", name: "Plate" },
    reservoir: { slot: "", name: "Reservoir" },
  };
  for (const [id, labware] of Object.entries(deck)) {
    const lower = labware.toLowerCase();
    const label = labwareLabel(labware) || labware;
    if (!out.tips.slot && /tip|diti/.test(lower)) out.tips = { slot: id, name: label };
    else if (!out.reservoir.slot && /reservoir|trough/.test(lower)) out.reservoir = { slot: id, name: label };
    else if (!out.plate.slot && /plate|well/.test(lower) && !/tip|diti|reservoir/.test(lower)) {
      out.plate = { slot: id, name: label };
    }
  }
  return out;
}
