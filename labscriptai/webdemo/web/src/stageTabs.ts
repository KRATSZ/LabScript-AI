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
