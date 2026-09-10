import type { SessionSnapshot } from "./types";

export type DownloadKind = "sop" | "python" | "plan";

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

export function downloadable(
  session: Pick<SessionSnapshot, "sop" | "code" | "plan">
): DownloadKind[] {
  const out: DownloadKind[] = [];
  if (session.sop?.trim()) out.push("sop");
  if (session.code?.trim()) out.push("python");
  if (session.plan && typeof session.plan === "object") out.push("plan");
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
