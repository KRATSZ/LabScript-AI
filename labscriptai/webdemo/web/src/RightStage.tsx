import { useEffect, useState } from "react";
import { ArtifactsPane } from "./ArtifactsPane";
import { StagePane } from "./StagePane";
import { tabCount, type StageTab } from "./stageTabs";
import { TrajectoryPane } from "./TrajectoryPane";
import type { AgentEvent, SessionSnapshot } from "./types";

export type { StageTab };
export { tabCount };

const TABS: Array<{ id: StageTab; label: string }> = [
  { id: "stage", label: "Stage" },
  { id: "artifacts", label: "Artifacts" },
  { id: "trajectory", label: "Trajectory" },
];

interface Props {
  session: SessionSnapshot | null;
  events: AgentEvent[];
  runningTool: string | null;
  busy: boolean;
  canWatch: boolean;
  onWatch: () => void;
}

export function RightStage({ session, events, runningTool, busy, canWatch, onWatch }: Props) {
  const [tab, setTab] = useState<StageTab>("stage");
  useEffect(() => {
    setTab("stage");
  }, [session?.id]);
  return (
    <section className="stage-column" data-testid="stage-column">
      <div className="stage-tabs" role="tablist" aria-label="Right stage">
        {TABS.map((item) => {
          const count = tabCount(item.id, session, events);
          return (
            <button
              key={item.id}
              type="button"
              role="tab"
              id={`tab-${item.id}`}
              data-testid={`tab-${item.id}`}
              aria-selected={tab === item.id}
              className={tab === item.id ? "stage-tab selected" : "stage-tab"}
              onClick={() => setTab(item.id)}
            >
              {item.label}
              {count != null ? (
                <span className="stage-tab-count" data-testid={`tab-count-${item.id}`}>
                  {count}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
      <div className="stage-body" role="tabpanel" aria-labelledby={`tab-${tab}`}>
        {tab === "stage" ? (
          session ? (
            <StagePane
              session={session}
              runningTool={runningTool}
              busy={busy}
              canWatch={canWatch}
              onWatch={onWatch}
            />
          ) : (
            <p className="hint">Pick a device on the left. Stage shows steps, assumed deck, and OT Watch.</p>
          )
        ) : null}
        {tab === "artifacts" ? <ArtifactsPane session={session} /> : null}
        {tab === "trajectory" ? <TrajectoryPane events={events} /> : null}
      </div>
    </section>
  );
}
