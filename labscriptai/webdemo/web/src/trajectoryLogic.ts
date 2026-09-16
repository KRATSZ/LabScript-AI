import { PIPELINE_HINTS } from "./pipelineLogic";
import type { AgentEvent } from "./types";

export type ActivityStatus = "run" | "ok" | "fail";

export interface ActivityStep {
  key: string;
  turn: number;
  name: string;
  label: string;
  status: ActivityStatus;
  durationMs: number | null;
}

const DONE_LABELS: Record<string, string> = {
  ask_user: "Asked you to confirm",
  generate_sop: "Wrote the protocol",
  generate_code: "Wrote the script",
  emit_plan: "Laid out the steps",
  run_checks: "Checked bench constraints",
  open_animation: "Opened the preview",
};

function titleTool(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (ch) => ch.toUpperCase());
}

export function activityLabel(name: string, status: ActivityStatus): string {
  if (status === "run") return PIPELINE_HINTS[name] || `${titleTool(name)}…`;
  return DONE_LABELS[name] || titleTool(name);
}

export function formatDuration(ms: number | null): string {
  if (ms == null || !Number.isFinite(ms) || ms < 80) return "";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

export function activityStatusWord(status: ActivityStatus): string {
  if (status === "ok") return "Passed";
  if (status === "fail") return "Failed";
  return "Running";
}

/** Fold raw tool/call + tool/result into one lab row per step. Skip developer kinds. */
export function activitySteps(events: AgentEvent[], runningTool: string | null = null): ActivityStep[] {
  const steps: ActivityStep[] = [];
  let turn = 0;
  for (const event of events) {
    if (event.kind === "turn/start") {
      turn += 1;
      continue;
    }
    if (event.kind === "tool/call" && event.name) {
      steps.push({
        key: `${event.seq}-${event.name}`,
        turn: turn || 1,
        name: event.name,
        label: activityLabel(event.name, "run"),
        status: "run",
        durationMs: null,
      });
      continue;
    }
    if (event.kind === "tool/result" && event.name) {
      const open = [...steps].reverse().find((step) => step.name === event.name && step.status === "run");
      const ok = event.name === "ask_user" ? true : event.detail?.ok !== false;
      const duration = typeof event.detail?.duration_ms === "number" ? event.detail.duration_ms : null;
      const status: ActivityStatus = ok ? "ok" : "fail";
      if (open) {
        open.status = status;
        open.durationMs = duration;
        open.label = activityLabel(event.name, status);
      } else {
        steps.push({
          key: `${event.seq}-${event.name}`,
          turn: turn || 1,
          name: event.name,
          label: activityLabel(event.name, status),
          status,
          durationMs: duration,
        });
      }
    }
  }
  if (runningTool && !steps.some((step) => step.name === runningTool && step.status === "run")) {
    steps.push({
      key: `running-${runningTool}`,
      turn: turn || 1,
      name: runningTool,
      label: activityLabel(runningTool, "run"),
      status: "run",
      durationMs: null,
    });
  }
  return steps;
}

export function activitySummary(steps: ActivityStep[]): string {
  if (!steps.length) return "";
  const failed = steps.filter((step) => step.status === "fail").length;
  const running = steps.filter((step) => step.status === "run").length;
  const passed = steps.filter((step) => step.status === "ok").length;
  const bits = [`${steps.length} step${steps.length === 1 ? "" : "s"}`];
  if (running) bits.push(`${running} running`);
  else if (failed) bits.push(`${failed} failed`);
  else if (passed === steps.length) bits.push("all passed");
  else bits.push(`${passed} passed`);
  return bits.join(" · ");
}

export function eventDetailText(event: AgentEvent): string {
  const detail = event.detail;
  if (!detail) return "";
  const bits: string[] = [];
  if (typeof detail.duration_ms === "number") bits.push(`${detail.duration_ms} ms`);
  if (detail.ok === true) bits.push("ok");
  if (detail.ok === false) bits.push("not ok");
  return bits.join(" · ");
}

export function eventClock(t: number): string {
  if (!Number.isFinite(t) || t <= 0) return "";
  const date = new Date(t);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
