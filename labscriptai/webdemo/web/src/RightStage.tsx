import { useEffect, useState } from "react";
import { ArtifactsPane } from "./ArtifactsPane";
import { StagePane } from "./StagePane";
import { tabCount, tabVisible, type StageTab } from "./stageTabs";
import { TrajectoryPane } from "./TrajectoryPane";
import { useLang } from "./LangContext";
import type { ActivityLive } from "./trajectoryLogic";
import type { AgentEvent, SessionSnapshot } from "./types";

export type { StageTab };
export { tabCount, tabVisible };

const TABS: Array<{ id: StageTab; label: string }> = [
  { id: "stage", label: "Stage" },
  { id: "trajectory", label: "Activity" },
  { id: "artifacts", label: "Files" },
];

interface Props {
  session: SessionSnapshot | null;
  events: AgentEvent[];
  runningTool: string | null;
  busy: boolean;
  canWatch: boolean;
  onWatch: () => void;
  live?: ActivityLive;
}

export function RightStage({ session, events, runningTool, busy, canWatch, onWatch, live = {} }: Props) {
  const { t } = useLang();
  const [tab, setTab] = useState<StageTab>("stage");
  const visible = TABS.filter((item) => tabVisible(item.id, session, events));
  const filesOpen = tabVisible("artifacts", session, events);
  const logOpen = tabVisible("trajectory", session, events);
  useEffect(() => {
    setTab("stage");
  }, [session?.id]);
  useEffect(() => {
    if (tab === "artifacts" && !filesOpen) setTab("stage");
    if (tab === "trajectory" && !logOpen) setTab("stage");
  }, [tab, filesOpen, logOpen]);
  return (
    <section
      className={tab === "trajectory" ? "stage-column activity-open" : "stage-column"}
      data-testid="stage-column"
    >
      {session && visible.length > 1 ? (
        <div className="stage-tabs" role="tablist" aria-label={t("Right stage")}>
          {visible.map((item) => {
            const count = tabCount(item.id, session, events, live);
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
                {t(item.label)}
                {count != null && count > 0 ? (
                  <span className="stage-tab-count" data-testid={`tab-count-${item.id}`}>
                    {count}
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      ) : null}
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
            <div className="stage-empty" data-testid="stage-empty">
              <p className="stage-empty-emoji" aria-hidden="true">
                🧫
              </p>
              <h2>{t("Deck")}</h2>
              <p>{t("The bench shows here.")}</p>
            </div>
          )
        ) : null}
        {tab === "artifacts" ? <ArtifactsPane session={session} /> : null}
        {tab === "trajectory" ? (
          <TrajectoryPane events={events} runningTool={runningTool} live={live} session={session} />
        ) : null}
      </div>
    </section>
  );
}
