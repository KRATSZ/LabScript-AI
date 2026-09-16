import { downloadable } from "./artifacts";
import { activitySteps } from "./trajectoryLogic";
import type { AgentEvent, SessionSnapshot } from "./types";

export type StageTab = "stage" | "artifacts" | "trajectory";

export function tabCount(
  tab: StageTab,
  session: SessionSnapshot | null,
  events: AgentEvent[]
): number | null {
  if (tab === "artifacts") return session ? downloadable(session).length : 0;
  if (tab === "trajectory") return activitySteps(events, null).length;
  return null;
}

export function tabVisible(
  tab: StageTab,
  session: SessionSnapshot | null,
  events: AgentEvent[]
): boolean {
  if (tab === "stage") return true;
  if (!session) return false;
  const files = tabCount("artifacts", session, events) ?? 0;
  if (tab === "artifacts") return files > 0;
  if (tab === "trajectory") return true;
  return false;
}
