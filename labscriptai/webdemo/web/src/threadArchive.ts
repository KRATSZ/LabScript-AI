import type { AgentEvent, ChatMessage, SessionSnapshot } from "./types";

export interface ArchivedThread {
  id: string;
  title: string;
  robot: string;
  goal: string;
  savedAt: number;
  messages: ChatMessage[];
  events: AgentEvent[];
  session: SessionSnapshot;
}

export const THREAD_KEY = "labscriptai.threads";
export const MAX_THREADS = 12;
export const THREAD_RETENTION =
  "Stored only in this browser. At most 12 runs. Removed when site data is cleared.";

export function threadTitle(goal: string, robot: string): string {
  const g = goal.replace(/\s+/g, " ").trim() || "Untitled run";
  const short = g.length > 42 ? `${g.slice(0, 41)}…` : g;
  return robot ? `${robot} · ${short}` : short;
}

export function loadThreads(): ArchivedThread[] {
  try {
    const raw = localStorage.getItem(THREAD_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is ArchivedThread => Boolean(item && typeof item === "object" && (item as ArchivedThread).id));
  } catch {
    return [];
  }
}

export function saveThreads(threads: ArchivedThread[]): void {
  try {
    localStorage.setItem(THREAD_KEY, JSON.stringify(threads.slice(0, MAX_THREADS)));
  } catch {
    /* ignore */
  }
}

function asThread(
  session: SessionSnapshot,
  messages: ChatMessage[],
  events: AgentEvent[]
): ArchivedThread {
  return {
    id: session.id,
    title: threadTitle(session.goal, session.device_label || session.robot || ""),
    robot: session.device_label || session.robot || "",
    goal: session.goal,
    savedAt: Date.now(),
    messages,
    events,
    session,
  };
}

export function archiveThread(
  existing: ArchivedThread[],
  session: SessionSnapshot | null,
  messages: ChatMessage[],
  events: AgentEvent[]
): ArchivedThread[] {
  if (!session?.id || !messages.length) return existing;
  const rest = existing.filter((item) => item.id !== session.id);
  const out = [asThread(session, messages, events), ...rest].slice(0, MAX_THREADS);
  saveThreads(out);
  return out;
}

/** Write a finished run (checks present) so refresh keeps it. */
export function persistFinished(
  existing: ArchivedThread[],
  session: SessionSnapshot | null,
  messages: ChatMessage[],
  events: AgentEvent[]
): ArchivedThread[] {
  if (!session?.id || !messages.length || !session.checks) return existing;
  return archiveThread(existing, session, messages, events);
}

/** Current run sits at the top of the rail. Finished runs are also in storage. */
export function railThreads(
  existing: ArchivedThread[],
  session: SessionSnapshot | null,
  messages: ChatMessage[],
  events: AgentEvent[]
): ArchivedThread[] {
  if (!session?.id) return existing;
  if (existing.some((item) => item.id === session.id)) return existing;
  return [asThread(session, messages, events), ...existing].slice(0, MAX_THREADS);
}
