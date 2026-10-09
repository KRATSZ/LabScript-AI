import { labwareLabel } from "./display";
import { actionStepCount, replayStepsFor, type ReplayStep } from "./replaySteps";
import type { SessionSnapshot } from "./types";

export interface Consumable {
  name: string;
  role: string;
  slot?: string;
}

export interface ProtocolSummaryModel {
  title: string;
  consumables: Consumable[];
  stepCount: number;
  actionCount: number;
  pipettes: string[];
  approx: string;
}

function roleFor(labware: string): string {
  const n = labware.toLowerCase();
  if (/tip\s*rack|tiprack|diti/.test(n)) return "tips";
  if (/pcr/.test(n)) return "PCR plate";
  if (/reservoir|trough/.test(n)) return "reservoir";
  if (/trash/.test(n)) return "trash";
  if (/plate|tube/.test(n)) return "plate";
  if (/thermocycler/.test(n)) return "thermocycler";
  return "labware";
}

function slotKey(slot?: string): string {
  return (slot || "").trim().toLowerCase();
}

function nameQuality(name: string): number {
  if (/µl|ul|μl|well|pcr|diti|reservoir|trough/i.test(name) && !/^(tips|plate|labware)$/i.test(name)) {
    return 2;
  }
  if (/^(tips|plate|labware|reservoir)$/i.test(name)) return 0;
  return 1;
}

function pushUnique(list: Consumable[], item: Consumable): void {
  const sk = slotKey(item.slot);
  if (sk) {
    const existing = list.find((entry) => slotKey(entry.slot) === sk);
    if (existing) {
      if (nameQuality(item.name) > nameQuality(existing.name)) existing.name = item.name;
      if (item.role && (existing.role === "labware" || nameQuality(item.role) > nameQuality(existing.role))) {
        existing.role = item.role;
      }
      return;
    }
  }
  const nameKey = item.name.trim().toLowerCase();
  const existing = list.find((entry) => entry.name.trim().toLowerCase() === nameKey);
  if (existing) {
    if (!existing.slot && item.slot) existing.slot = item.slot;
    return;
  }
  list.push(item);
}

function fromDeck(deck: Record<string, string> | undefined): Consumable[] {
  const out: Consumable[] = [];
  for (const [slot, labware] of Object.entries(deck ?? {})) {
    if (!labware?.trim()) continue;
    pushUnique(out, {
      name: labwareLabel(labware) || labware,
      role: roleFor(labware),
      slot,
    });
  }
  return out;
}

function fromAnalyze(analyze: Record<string, unknown> | null | undefined): Consumable[] {
  const out: Consumable[] = [];
  const labware = Array.isArray(analyze?.labware) ? analyze.labware : [];
  for (const item of labware) {
    if (!item || typeof item !== "object") continue;
    const rec = item as Record<string, unknown>;
    const load = String(rec.loadName ?? rec.load_name ?? rec.displayName ?? "").trim();
    if (!load) continue;
    const slot = rec.location && typeof rec.location === "object"
      ? String((rec.location as { slot?: unknown }).slot ?? "")
      : String(rec.slot ?? "");
    pushUnique(out, { name: labwareLabel(load) || load, role: roleFor(load), slot: slot || undefined });
  }
  const modules = Array.isArray(analyze?.modules) ? analyze.modules : [];
  for (const item of modules) {
    if (!item || typeof item !== "object") continue;
    const rec = item as Record<string, unknown>;
    const model = String(rec.model ?? rec.moduleType ?? rec.module_type ?? "module").trim();
    pushUnique(out, { name: labwareLabel(model) || model, role: roleFor(model) });
  }
  return out;
}

function fromPlan(plan: Record<string, unknown> | null | undefined): Consumable[] {
  const out: Consumable[] = [];
  const resources = Array.isArray(plan?.resources) ? plan.resources : [];
  for (const item of resources) {
    if (!item || typeof item !== "object") continue;
    const rec = item as Record<string, unknown>;
    const id = String(rec.id ?? rec.name ?? "").trim();
    const type = String(rec.type ?? "").trim();
    const slot = rec.slot != null ? String(rec.slot) : undefined;
    const name = labwareLabel(id) || id || type;
    if (!name) continue;
    pushUnique(out, { name, role: roleFor(`${type} ${id}`), slot });
  }
  return out;
}

function pipetteList(session: Pick<SessionSnapshot, "hardware" | "analyze">): string[] {
  const named = [session.hardware?.leftPipette, session.hardware?.rightPipette]
    .filter((name): name is string => Boolean(name && name !== "None"));
  if (named.length) return named;
  const pipettes = Array.isArray(session.analyze?.pipettes) ? session.analyze.pipettes : [];
  return pipettes
    .map((item) => {
      if (!item || typeof item !== "object") return "";
      return String((item as { pipetteName?: unknown; name?: unknown }).pipetteName ?? (item as { name?: unknown }).name ?? "");
    })
    .filter(Boolean);
}

export function protocolSummary(session: SessionSnapshot | null | undefined): ProtocolSummaryModel | null {
  if (!session) return null;
  const steps: ReplayStep[] = replayStepsFor(session);
  const deck = session.hardware?.deck ?? {};
  const confirmedSlots = new Set(Object.keys(deck).map((slot) => slotKey(slot)).filter(Boolean));
  const unique: Consumable[] = [];
  for (const item of fromDeck(deck)) pushUnique(unique, item);
  const extras = [...fromAnalyze(session.analyze), ...fromPlan(session.plan)];
  for (const item of extras) {
    if (confirmedSlots.size && item.slot && !confirmedSlots.has(slotKey(item.slot))) continue;
    pushUnique(unique, item);
  }
  const actionCount = actionStepCount(steps);
  const stepCount = steps.length;
  if (!unique.length && !stepCount && !session.sop?.trim()) return null;
  const approx = actionCount
    ? `~${actionCount} liquid-handling step${actionCount === 1 ? "" : "s"}`
    : stepCount
      ? `~${stepCount} step${stepCount === 1 ? "" : "s"}`
      : "Steps not listed yet";
  return {
    title: session.goal?.trim() || "Protocol",
    consumables: unique,
    stepCount,
    actionCount,
    pipettes: pipetteList(session),
    approx,
  };
}
