import { PIPELINE_HINTS } from "./pipelineLogic";
import type { AgentEvent, ChatMessage, SessionSnapshot } from "./types";

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
  file?: string;
  extra?: string;
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

/** Volume, wells, standard deck — body under every lab step so Activity is not label-only. */
export function activityLabRecap(session?: SessionSnapshot | null): string {
  const goal = (session?.goal || "").replace(/\s+/g, " ").trim();
  const vol = goal.match(/(\d+(?:\.\d+)?)\s*(?:µL|uL|ul)\b/i);
  const route = goal.match(/from\s+(?:well\s+)?([A-H]\d+)\s+to\s+(?:well\s+)?([A-H]\d+)/i);
  const bits: string[] = [];
  if (vol && route) bits.push(`${vol[1]} µL ${route[1]}→${route[2]}`);
  else if (vol) bits.push(`${vol[1]} µL`);
  else if (route) bits.push(`${route[1]}→${route[2]}`);
  bits.push("standard deck");
  return bits.join(", ");
}

/** Scientist-facing script name. Never `.gwl`, JSON, or a tool id. */
export function activityFileLabel(session?: SessionSnapshot | null, name?: string): string {
  if (!session) return "";
  const robot = session.robot;
  if (name === "generate_code" || session.code?.trim()) {
    if (robot === "OT-2" || robot === "Flex" || Boolean(session.code?.trim())) return "protocol.py";
  }
  if (name === "emit_plan" || session.plan || session.artifacts?.worklistGwl || session.artifacts?.hamiltonScript) {
    if (robot === "Tecan") return "Fluent worklist";
    if (robot === "Hamilton") return "star.py";
    if (robot === "Vantage") return "vantage.py";
  }
  return "";
}

function failReason(session?: SessionSnapshot | null): string {
  const line = session?.checks?.consequences?.find((item) => typeof item === "string" && item.trim());
  return typeof line === "string" ? line.trim() : "";
}

export function activityStepNote(
  name: string,
  status: ActivityStatus,
  session?: SessionSnapshot | null
): { note?: string; file?: string; extra?: string } {
  if (name === THINK_STEP) return {};
  const recap = activityLabRecap(session);
  const file = activityFileLabel(session, name) || undefined;
  if (name === "run_checks" || name === "open_animation") {
    if (status === "fail") {
      const reason = failReason(session);
      if (reason.length > 160) {
        return { note: `${reason.slice(0, 159).replace(/\s+\S*$/, "")}…`, extra: reason };
      }
      return { note: reason || recap };
    }
    if (status === "ok") return { note: "Deck is on Stage" };
    return { note: recap };
  }
  if (name === "generate_code" || name === "emit_plan") return { note: recap, file };
  return { note: recap };
}

function decorateLabSteps(steps: ActivityStep[], session?: SessionSnapshot | null): ActivityStep[] {
  return steps.map((step) => {
    if (step.name === THINK_STEP) return step;
    const bits = activityStepNote(step.name, step.status, session);
    return {
      ...step,
      note: step.note || bits.note,
      file: step.file || bits.file,
      extra: step.extra || bits.extra,
    };
  });
}

const TOOLISH =
  /\b(ask_user|generate_sop|generate_code|emit_plan|run_checks|open_animation|tool call|tool\/call)\b/i;

/** SOP outline / writing-spec. plate/slot in these clauses is not a lab fact. */
const SOP_OUTLINE =
  /\breagents\s*:|\bcould list\b|\bvolumes?\s*\?|\bwells?\s*\?|one short confirm|\bassume\s*:|need include|stop when|technician can run|no summary|repeated deck|\bbullets?\b|robot\/pipettes|numbered steps|\bfrom goal\b|#\s*objective|must include|compact.{0,48}\bsop\b|\bmarkdown\b|one[- ]sentence|nam(?:e|ing)(?:\s+the)?\s+three slots|no essay|if you guessed|instruction says|at most one|p300_single|\bapi\s*2\.\d+|the tool returned|\bthe tool\b|last message from user|user's last message|user (said|message)|do not (ask|write)|then stop|need from|output only|comply constraints|no phase|only if needed|vs reuse|(?:^|[.!?]\s+)(?:reagents|pipettes?|robot|objective|steps?|protocol|sop|materials|methods|notes|samples?)\s*:/i;

const LAB_FACT =
  /\bconfirm(?:ed|s)?\b|\d+\s*(?:µL|ul)\b|\bstandard deck\b|\bno mix\b|\bnew tip\b|\bslot\s*\d.{0,48}\b(?:tip|reservoir|plate|well)|\b(?:tip|reservoir|plate|well).{0,48}\bslot\s*\d/i;

function thoughtClauses(text: string): string[] {
  const marked = text
    .replace(/^first turn:\s*/i, "")
    .replace(/\s+[—–-]\s+/g, ". ")
    .replace(
      /(?=\b(?:Reagents:|Could list|Assume:|Need include|Need from|Stop when|No summary|no repeated|one short confirm))/gi,
      ". "
    );
  return marked
    .split(/(?<=[.!?])\s+|;\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function isOutline(sentence: string): boolean {
  const text = sentence.trim();
  if (!text) return false;
  if (SOP_OUTLINE.test(text) || TOOLISH.test(text)) return true;
  if (/^[A-Za-z][\w /]{0,24}:/.test(text)) return true;
  if (/\bcould\b/i.test(text)) return true;
  return false;
}

function isLabFact(sentence: string): boolean {
  const text = sentence.trim();
  if (!text || text.startsWith("{") || text.startsWith("[")) return false;
  if (isOutline(text)) return false;
  return LAB_FACT.test(text);
}

/** Short lab thought. Mixed SOP-outline + lab → hide the whole excerpt. */
export function labThinkNote(text: string | undefined | null): string {
  if (!text) return "";
  const clipped = text.replace(/\s+/g, " ").trim();
  if (!clipped || clipped.startsWith("{") || clipped.startsWith("[")) return "";
  if (SOP_OUTLINE.test(clipped)) return "";
  const clauses = thoughtClauses(clipped);
  if (!clauses.length || !clauses.every(isLabFact)) return "";
  const joined = clauses
    .join(" ")
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
  live: ActivityLive = {},
  session?: SessionSnapshot | null
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
    return decorateLabSteps(insertThinkRows(steps, events, live), session);
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
  return decorateLabSteps(insertThinkRows(steps, events, live), session);
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

/** Follow the newest row unless the scientist scrolled up (Harness-style). */
export function activityFollowsTail(
  el: { scrollHeight: number; scrollTop: number; clientHeight: number },
  slack = 48
): boolean {
  return el.scrollHeight - el.scrollTop - el.clientHeight <= slack;
}
