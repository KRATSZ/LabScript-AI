import { lazy, Suspense } from "react";
import { watchUnavailableCopy } from "./analysis";
import { planSteps } from "./artifacts";
import { DeckPlay } from "./DeckPlay";
import { labwareLabel, planStepDisplay } from "./display";
import { isPlanCodegen, robotSupportsWatch } from "./devices";
import { IssuesPanel } from "./IssuesPanel";
import { Pipeline } from "./Pipeline.tsx";
import type { SessionSnapshot } from "./types";

const WatchPlayer = lazy(() => import("./WatchPlayer"));

interface Props {
  session: SessionSnapshot;
  runningTool: string | null;
  busy: boolean;
  canWatch: boolean;
  onWatch: () => void;
}

function DeckStrip({ session }: { session: SessionSnapshot }) {
  const slots = Object.entries(session.hardware?.deck ?? {});
  if (!slots.length) {
    return <p className="hint">Assumed deck appears after a device is chosen.</p>;
  }
  return (
    <div className="deck-strip" data-testid="deck-strip">
      <div className="plan-heading">Assumed deck</div>
      {slots.map(([slot, labware]) => (
        <p key={slot} className="file">
          {slot}: {labwareLabel(labware) || labware}
        </p>
      ))}
      {session.deck_assumed ? <p className="hint">Standard layout — software preview, not a live robot.</p> : null}
      {session.device_note ? <p className="hint">{session.device_note}</p> : null}
    </div>
  );
}

export function StagePane({ session, runningTool, busy, canWatch, onWatch }: Props) {
  const steps = isPlanCodegen(session.robot) || !session.code?.trim() ? planSteps(session.plan) : [];
  const watchReady = canWatch && robotSupportsWatch(session.robot);
  const checksPass = session.checks?.status === "pass";
  const watchGap = watchUnavailableCopy(
    session.robot,
    session.code_service,
    session.checks?.status,
    session.analyze ?? null
  );
  return (
    <div className="stage-pane" data-testid="stage-pane">
      <Pipeline session={session} runningTool={runningTool} busy={busy} />
      <DeckStrip session={session} />
      {watchReady ? (
        <div className="watch-cta">
          <p className="hint">Watch is a software preview of the run — not the live deck.</p>
          <div className="watch-inline" data-testid="watch-inline">
            <Suspense fallback={<p className="file">Opening preview…</p>}>
              <WatchPlayer analyze={session.analyze ?? null} robot={session.robot} />
            </Suspense>
          </div>
          <button type="button" className="primary" onClick={onWatch}>
            Watch the protocol
          </button>
        </div>
      ) : (
        <>
          {watchGap ? (
            <p className="hint" data-testid="watch-unavailable">
              {watchGap}
            </p>
          ) : null}
          {checksPass ? (
            <DeckPlay
              steps={steps}
              analyze={session.analyze ?? null}
              deck={session.hardware?.deck ?? {}}
              playing
            />
          ) : null}
        </>
      )}
      {steps.length ? (
        <div className="plan-block">
          <div className="plan-heading">Transfer steps</div>
          <div className="plan-steps">
            {steps.slice(0, 20).map((step, index) => (
              <p key={index} className="file">
                {planStepDisplay(step)}
              </p>
            ))}
          </div>
        </div>
      ) : watchReady ? null : (
        <p className="hint">
          {isPlanCodegen(session.robot)
            ? "Steps and check results show here after the protocol is written."
            : "When checks pass, Watch uses this pane. Otherwise the step list appears."}
        </p>
      )}
      <IssuesPanel checks={session.checks} />
    </div>
  );
}
