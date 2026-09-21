import { planStepDisplay } from "./display";
import { planSteps, type PlanStepLike } from "./artifacts";

export interface ReplayStep {
  id: string;
  index: number;
  kind: string;
  label: string;
  detail: string;
  setup?: boolean;
}

const SETUP_COMMANDS = new Set([
  "loadlabware",
  "loadpipette",
  "loadmodule",
  "loadliquid",
  "loadtrashbin",
  "loadwastechute",
  "home",
  "comment",
  "delay",
  "waitforresume",
]);

const COMMAND_LABELS: Record<string, string> = {
  pickuptip: "Pick up tip",
  droptip: "Drop tip",
  droptipinplace: "Drop tip",
  aspirate: "Aspirate",
  dispense: "Dispense",
  blowout: "Blow out",
  touchtip: "Touch tip",
  mix: "Mix",
  moveToWell: "Move to well",
  movetowell: "Move to well",
  movetocoordinates: "Move",
  movetoliquid: "Move to liquid",
  airgap: "Air gap",
  waitforduration: "Wait",
  waitforresume: "Pause",
  delay: "Wait",
  thermocyclerrunprofile: "Thermocycler profile",
  thermocyclersetblocktemperature: "Set block temperature",
  thermocyclersetlidtemperature: "Set lid temperature",
  thermocyclercloselid: "Close thermocycler lid",
  thermocycleropenlid: "Open thermocycler lid",
  loadlabware: "Load labware",
  loadpipette: "Load pipette",
  loadmodule: "Load module",
  loadliquid: "Load liquid",
  home: "Home",
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function commandKind(cmd: Record<string, unknown>): string {
  return String(cmd.commandType ?? cmd.command_type ?? cmd.type ?? "")
    .trim()
    .replace(/-/g, "");
}

function kindKey(kind: string): string {
  return kind.toLowerCase().replace(/_/g, "");
}

function paramText(params: Record<string, unknown>): string {
  const well = String(params.wellName ?? params.well ?? "").trim();
  const labware = String(params.labwareName ?? params.displayName ?? "").trim();
  const volume = params.volume != null && Number.isFinite(Number(params.volume)) ? `${params.volume} µL` : "";
  const bits = [volume, labware, well].filter(Boolean);
  return bits.join(" · ");
}

function commandLabel(kind: string): string {
  const key = kindKey(kind);
  if (COMMAND_LABELS[key]) return COMMAND_LABELS[key];
  if (COMMAND_LABELS[kind]) return COMMAND_LABELS[kind];
  return kind
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/_/g, " ")
    .replace(/^\w/, (ch) => ch.toUpperCase());
}

export function analyzeReplaySteps(analyze: Record<string, unknown> | null | undefined): ReplayStep[] {
  if (!analyze || !Array.isArray(analyze.commands)) return [];
  const out: ReplayStep[] = [];
  for (const raw of analyze.commands) {
    const cmd = asRecord(raw);
    const kind = commandKind(cmd);
    if (!kind) continue;
    const params = asRecord(cmd.params);
    const key = kindKey(kind);
    const setup = SETUP_COMMANDS.has(key);
    const id = String(cmd.id ?? cmd.key ?? `cmd-${out.length + 1}`);
    const detail = paramText(params);
    out.push({
      id,
      index: out.length,
      kind,
      label: commandLabel(kind),
      detail,
      setup,
    });
  }
  return out;
}

export function planReplaySteps(plan: Record<string, unknown> | null | undefined): ReplayStep[] {
  return planSteps(plan ?? null).map((step, index) => {
    const rec = (step && typeof step === "object" ? step : {}) as PlanStepLike;
    const kind = String(rec.primitive_type ?? rec.type ?? "step");
    const id = String(rec.step_id ?? rec.id ?? `step-${index + 1}`);
    const label = planStepDisplay(step);
    const detailBits = [rec.source, rec.destination, rec.location]
      .filter((part) => typeof part === "string" && part.trim())
      .map((part) => String(part));
    return {
      id,
      index,
      kind,
      label,
      detail: detailBits.join(" → "),
      setup: false,
    };
  });
}

export function replayStepsFor(session: {
  analyze?: Record<string, unknown> | null;
  plan?: Record<string, unknown> | null;
}): ReplayStep[] {
  const fromAnalyze = analyzeReplaySteps(session.analyze);
  if (fromAnalyze.length) return fromAnalyze;
  return planReplaySteps(session.plan);
}

export function clampStepIndex(index: number, total: number): number {
  if (total <= 0) return 0;
  if (!Number.isFinite(index)) return 0;
  return Math.max(0, Math.min(total - 1, Math.round(index)));
}

export function actionStepCount(steps: ReplayStep[]): number {
  return steps.filter((step) => !step.setup).length || steps.length;
}
