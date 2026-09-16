import { PIPELINE_HINTS } from "./pipelineLogic";
import type { AgentEvent, ChatMessage } from "./types";

export type ActivityStatus = "run" | "ok" | "fail";

export const THINK_STEP = "_think";

export interface ActivityLive {
  thinking?: boolean;
  thoughtTurns?: number[];
  thoughtNotes?: Record<number, string>;
  thinkingNote?: string;
}

export interface ActivityStep {
  key: string;
  turn: number;
  name: string;
  label: string;
  status: ActivityStatus;
  durationMs: number | null;
  note?: string;
}

const DONE_LABELS: Record<string, string> = {
  ask_user: "Asked you to confirm",
  generate_sop: "Wrote the protocol",
  generate_code: "Wrote the script",
  emit_plan: "Laid out the steps",
  run_checks: "Checked bench constraints",
  open_animation: "Deck is on Stage",
  [THINK_STEP]: "Thought it through",
};

function foldDeckIntoChecks(steps: ActivityStep[], status: ActivityStatus): boolean {
  const checks = [...steps].reverse().find((step) => step.name === "run_checks");
  if (!checks) return false;
  if (status === "ok" || checks.status === "ok") checks.label = "Checked the bench — deck is up";
  else checks.label = "Checking the bench — deck next…";
  return true;
}

function titleTool(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (ch) => ch.toUpperCase());
}

export function activityLabel(name: string, status: ActivityStatus): string {
  if (name === THINK_STEP) return status === "run" ? "Thinking it through…" : "Thought it through";
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
  return "Still going";
}

const TOOLISH =
  /\b(ask_user|generate_sop|generate_code|emit_plan|run_checks|open_animation|tool call|tool\/call)\b/i;
const LAB_SIGNAL =
  /\b(µL|ul|volume|volumes|well|wells|mix|deck|slot|slots|tips?|plate|reservoir|confirm(?:ed|s)?|sample|transfer|pipette|standard deck)\b/i;

function isHomeworkThought(sentence: string): boolean {
  const text = sentence.trim();
  if (!text) return true;
  if (TOOLISH.test(text)) return true;
  if (!LAB_SIGNAL.test(text)) return true;
  return (
    /compact.{0,48}\bsop\b/i.test(text) ||
    /\bsop\b.{0,40}(markdown|english|compact)/i.test(text) ||
    /liquid-handling sop/i.test(text) ||
    /comply constraints/i.test(text) ||
    /follow constraints/i.test(text) ||
    /^need (comply|write|follow|compact|infer)\b/i.test(text) ||
    /need write compact/i.test(text) ||
    /no phase/i.test(text) ||
    /phase\s*\/\s*action\s*\/\s*tool/i.test(text) ||
    /action\s*\/\s*tool/i.test(text) ||
    /nam(?:e|ing)(?:\s+the)?\s+three slots/i.test(text) ||
    /in one sentence/i.test(text) ||
    /one[- ]sentence/i.test(text) ||
    /user (said|message)/i.test(text) ||
    /^need to give\b/i.test(text) ||
    /must include/i.test(text) ||
    /#\s*objective/i.test(text) ||
    /no essay/i.test(text) ||
    /english markdown/i.test(text) ||
    /\bmarkdown\b/i.test(text) ||
    /400-800/i.test(text) ||
    /output only/i.test(text) ||
    /instruction says/i.test(text) ||
    /at most one/i.test(text) ||
    /do not write/i.test(text) ||
    /do not ask/i.test(text) ||
    /then stop/i.test(text) ||
    /the tool returned/i.test(text) ||
    /\bthe tool\b/i.test(text) ||
    /user's last message/i.test(text) ||
    /p300_single/i.test(text) ||
    /\bapi\s*2\.\d+/i.test(text) ||
    /\bgripper\b/i.test(text) ||
    /^no\b[\s.…]*$/i.test(text)
  );
}

/** Short Harness-like excerpt: lab sentences only. Hide if only homework remains. */
export function labThinkNote(text: string | undefined | null): string {
  if (!text) return "";
  const clipped = text.replace(/\s+/g, " ").trim();
  if (!clipped || clipped.startsWith("{") || clipped.startsWith("[")) return "";
  const sentences = clipped.split(/(?<=[.!?])\s+|;\s+/).filter(Boolean);
  const lab = sentences.filter((sentence) => !isHomeworkThought(sentence));
  const joined = lab
    .join(" ")
    .replace(/\b(ask_user|generate_sop|generate_code|emit_plan|run_checks|open_animation|tool call|tool\/call)\b/gi, "")
    .replace(/\btipracks?\b/gi, "tip rack")
    .replace(/\s{2,}/g, " ")
    .replace(/^[,;:\s]+/, "")
    .replace(/[.,;:\s]+$/, "")
    .trim();
  if (!joined) return "";
  if (joined.length <= 160) return joined;
  return `${joined.slice(0, 159).replace(/\s+\S*$/, "")}…`;
}

/** One thought row per user turn that streamed reasoning. */
export function thoughtTurnsFromChat(messages: ChatMessage[]): number[] {
  return Object.keys(thoughtNotesFromChat(messages)).map(Number);
}

/** Raw thinking text keyed by 1-based user turn — kept after the turn ends. */
export function thoughtNotesFromChat(messages: ChatMessage[]): Record<number, string> {
  let turn = 0;
  const notes: Record<number, string> = {};
  for (const msg of messages) {
    if (msg.role === "user") turn += 1;
    else if (msg.thinking && turn > 0) notes[turn] = msg.thinking;
  }
  return notes;
}

function currentTurn(events: AgentEvent[], steps: ActivityStep[], live: ActivityLive): number {
  const fromEvents = events.filter((event) => event.kind === "turn/start").length;
  const fromSteps = steps.reduce((max, step) => Math.max(max, step.turn), 0);
  const fromThought = live.thoughtTurns?.reduce((max, turn) => Math.max(max, turn), 0) ?? 0;
  return Math.max(fromEvents, fromSteps, fromThought, live.thinking ? 1 : 0);
}

function insertThinkRows(steps: ActivityStep[], events: AgentEvent[], live: ActivityLive): ActivityStep[] {
  const thought = [...new Set(live.thoughtTurns || [])].filter((turn) => turn > 0);
  if (!thought.length && !live.thinking) return steps;
  const turnNow = currentTurn(events, steps, live) || 1;
  const turns = new Set(thought);
  if (live.thinking) turns.add(turnNow);
  const thinkRows: ActivityStep[] = [...turns]
    .sort((a, b) => a - b)
    .map((turn) => {
      const liveThis = Boolean(live.thinking) && turn === turnNow;
      const raw = live.thoughtNotes?.[turn] || (liveThis ? live.thinkingNote : "");
      return {
        key: `think-${turn}`,
        turn,
        name: THINK_STEP,
        label: activityLabel(THINK_STEP, liveThis ? "run" : "ok"),
        status: liveThis ? "run" : "ok",
        durationMs: null,
        note: labThinkNote(raw) || undefined,
      };
    });
  const byTurn = new Map<number, ActivityStep[]>();
  for (const row of [...thinkRows, ...steps]) {
    const list = byTurn.get(row.turn) || [];
    list.push(row);
    byTurn.set(row.turn, list);
  }
  const out: ActivityStep[] = [];
  for (const turn of [...byTurn.keys()].sort((a, b) => a - b)) {
    const rows = byTurn.get(turn) || [];
    out.push(...rows.filter((row) => row.name === THINK_STEP), ...rows.filter((row) => row.name !== THINK_STEP));
  }
  return out;
}

/** Fold raw tool/call + tool/result into one lab row per step. Skip developer kinds. */
export function activitySteps(
  events: AgentEvent[],
  runningTool: string | null = null,
  live: ActivityLive = {}
): ActivityStep[] {
  const steps: ActivityStep[] = [];
  let turn = 0;
  for (const event of events) {
    if (event.kind === "turn/start") {
      turn += 1;
      continue;
    }
    if (event.kind === "tool/call" && event.name) {
      if (event.name === "open_animation" && foldDeckIntoChecks(steps, "run")) continue;
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
      if (event.name === "open_animation" && !open && foldDeckIntoChecks(steps, status)) continue;
      if (open) {
        open.status = status;
        open.durationMs = duration;
        open.label = activityLabel(event.name, status);
        if (event.name === "open_animation") foldDeckIntoChecks(steps, status);
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
  if (runningTool === "open_animation" && foldDeckIntoChecks(steps, "run")) {
    return insertThinkRows(steps, events, live);
  }
  if (runningTool && runningTool !== THINK_STEP && !steps.some((step) => step.name === runningTool && step.status === "run")) {
    steps.push({
      key: `running-${runningTool}`,
      turn: turn || 1,
      name: runningTool,
      label: activityLabel(runningTool, "run"),
      status: "run",
      durationMs: null,
    });
  }
  return insertThinkRows(steps, events, live);
}

export function activitySummary(steps: ActivityStep[]): string {
  if (!steps.length) return "";
  const failed = steps.filter((step) => step.status === "fail").length;
  const running = steps.filter((step) => step.status === "run").length;
  const passed = steps.filter((step) => step.status === "ok").length;
  const bits = [`${steps.length} step${steps.length === 1 ? "" : "s"}`];
  if (running) bits.push(`${running} still going`);
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
