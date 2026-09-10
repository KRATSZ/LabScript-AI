import { isPlanCodegen, isPythonCodegen } from "./devices";
import type { RobotModel, SessionSnapshot } from "./types";

export type DownloadKind = "sop" | "python" | "plan" | "gwl";

export const DOWNLOAD_LABELS: Record<DownloadKind, string> = {
  sop: "SOP",
  python: "Python",
  plan: "Step JSON",
  gwl: ".gwl worklist",
};

export interface PlanStepLike {
  step_id?: string;
  id?: string;
  primitive_type?: string;
  type?: string;
  source?: string;
  destination?: string;
  location?: string;
  volume_ul?: number;
}

function asStep(step: unknown): PlanStepLike {
  return step && typeof step === "object" ? (step as PlanStepLike) : {};
}

export function planStepLine(step: unknown): string {
  const s = asStep(step);
  const id = String(s.step_id ?? s.id ?? "?");
  const prim = String(s.primitive_type ?? s.type ?? "?")
    .toUpperCase()
    .replace(/-/g, "_");
  const vol = s.volume_ul != null && Number.isFinite(Number(s.volume_ul)) ? `${s.volume_ul}µL` : "";
  const source = typeof s.source === "string" && s.source.trim() ? s.source : "";
  const dest = typeof s.destination === "string" && s.destination.trim() ? s.destination : "";
  const loc = typeof s.location === "string" && s.location.trim() ? s.location : "";
  let route = "";
  if (source && dest) route = `${source}→${dest}`;
  else if (source) route = source;
  else if (dest) route = dest;
  else if (loc) route = loc;
  return [id, prim, vol, route].filter(Boolean).join(" ");
}

export function planSteps(plan: Record<string, unknown> | null): unknown[] {
  if (!plan || !Array.isArray(plan.steps)) return [];
  return plan.steps;
}

export function downloadSuffix(status?: string): string {
  if (status === "fail") return " (checks failed)";
  if (status === "unevaluable") return " (cannot verify)";
  return "";
}

export function downloadHint(kind: DownloadKind, robot?: RobotModel | null): string {
  if (kind === "sop") return "Human-readable protocol write-up";
  if (kind === "python") return "Run with opentrons_simulate or upload to OT App";
  if (kind === "gwl") return "Import into FluentControl via Load Worklist";
  if (robot === "Hamilton") return "Step table for STAR (runnable script later)";
  if (robot === "Tecan") return "Step table alongside the Fluent worklist";
  return "Step table as JSON";
}

type DownloadSource = Pick<SessionSnapshot, "sop" | "code" | "plan" | "artifacts"> & {
  robot?: SessionSnapshot["robot"];
};

export function downloadable(session: DownloadSource): DownloadKind[] {
  const robot = session.robot ?? null;
  const pythonDevice = isPythonCodegen(robot);
  const planDevice = isPlanCodegen(robot);
  const allowPython = !robot || pythonDevice;
  const allowPlan = !robot || planDevice || (pythonDevice && !session.code?.trim());
  const allowGwl = !robot || robot === "Tecan";

  const out: DownloadKind[] = [];
  if (session.sop?.trim()) out.push("sop");
  if (allowPython && session.code?.trim()) out.push("python");
  if (allowPlan && session.plan && typeof session.plan === "object") out.push("plan");
  if (allowGwl && session.artifacts?.worklistGwl?.trim()) out.push("gwl");
  return out;
}

export function downloadText(filename: string, text: string, mime = "text/plain"): void {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
