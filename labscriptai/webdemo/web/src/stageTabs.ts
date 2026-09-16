import { downloadable } from "./artifacts";
import type { AgentEvent, SessionSnapshot } from "./types";

export type StageTab = "stage" | "artifacts" | "trajectory";

export function tabCount(
  tab: StageTab,
  session: SessionSnapshot | null,
  events: AgentEvent[]
): number | null {
  if (tab === "artifacts") return session ? downloadable(session).length : 0;
  if (tab === "trajectory") return events.length;
  return null;
}

export function tabVisible(
  tab: StageTab,
  session: SessionSnapshot | null,
  events: AgentEvent[]
): boolean {
  if (tab === "stage") return true;
  const files = tabCount("artifacts", session, events) ?? 0;
  if (tab === "artifacts") return files > 0;
  // Internal event log stays off chrome — Files is the scientist-facing sidecar.
  if (tab === "trajectory") return false;
  return false;
}
