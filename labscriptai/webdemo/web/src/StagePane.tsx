import { watchUnavailableCopy } from "./analysis";
import { planSteps } from "./artifacts";
import { planStepDisplay } from "./display";
import { DeckSketch } from "./DeckSketchView";
import { isPlanCodegen, robotSupportsWatch } from "./devices";
import { DemoReplay } from "./DemoReplay";
import { IssuesPanel } from "./IssuesPanel";
import { OtDeckReplay } from "./OtDeckReplay";
import { Pipeline } from "./Pipeline.tsx";
import { PlrDeckReplay } from "./PlrDeckReplay";
import { ProtocolSummaryCard } from "./SummaryCard";
import { useLang } from "./LangContext";
import type { SessionSnapshot } from "./types";

interface Props {
  session: SessionSnapshot;
  runningTool: string | null;
  busy: boolean;
  canWatch: boolean;
  onWatch: () => void;
}

export function StagePane({ session, runningTool, busy, canWatch }: Props) {
  const { t } = useLang();
  const steps = isPlanCodegen(session.robot) || !session.code?.trim() ? planSteps(session.plan) : [];
  const watchReady = canWatch && robotSupportsWatch(session.robot);
  const watchGap = watchUnavailableCopy(
    session.robot,
    session.code_service,
    session.checks?.status,
    session.analyze ?? null
  );
  const plrReady =
    isPlanCodegen(session.robot) &&
    session.checks?.status === "pass" &&
    Boolean(session.plan && typeof session.plan === "object");
  const hasDeck = watchReady || plrReady;
  return (
    <div className={hasDeck ? "stage-pane has-deck" : "stage-pane"} data-testid="stage-pane">
      {watchReady ? (
        <DemoReplay session={session}>
          <OtDeckReplay
            analyze={session.analyze}
            robot={session.robot}
            protocolName={session.goal}
            appType="desktop"
          />
        </DemoReplay>
      ) : plrReady ? (
        <PlrDeckReplay plan={session.plan} robot={session.robot} session={session} />
      ) : (
        <div className="stage-wait">
          <div className="stage-wait-copy">
            <h2>{t("Standard deck")}</h2>
            <p>
              {isPlanCodegen(session.robot)
                ? t("The bench preview fills this pane after checks pass.")
                : t("The deck preview fills this pane after checks pass.")}
            </p>
          </div>
          <DeckSketch session={session} />
          <Pipeline session={session} runningTool={runningTool} busy={busy} compact />
          {watchGap ? (
            <p className="hint" data-testid="watch-unavailable">
              {watchGap}
            </p>
          ) : null}
          <ProtocolSummaryCard session={session} />
          {steps.length ? (
            <div className="plan-block">
              <div className="plan-heading">{t("Transfer steps")}</div>
              <div className="plan-steps">
                {steps.slice(0, 20).map((step, index) => (
                  <p key={index} className="file">
                    {planStepDisplay(step)}
                  </p>
                ))}
              </div>
            </div>
          ) : null}
          <IssuesPanel checks={session.checks} session={session} />
        </div>
      )}
    </div>
  );
}
