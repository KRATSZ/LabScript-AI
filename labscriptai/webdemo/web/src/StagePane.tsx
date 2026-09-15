import { watchUnavailableCopy } from "./analysis";
import { planSteps } from "./artifacts";
import { labwareLabel, planStepDisplay } from "./display";
import { isPlanCodegen, robotSupportsWatch } from "./devices";
import { IssuesPanel } from "./IssuesPanel";
import { OtDeckReplay } from "./OtDeckReplay";
import { Pipeline } from "./Pipeline.tsx";
import { PlrDeckReplay } from "./PlrDeckReplay";
import type { SessionSnapshot } from "./types";

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
    return <p className="hint">Standard deck appears after a device is chosen.</p>;
  }
  return (
    <div className="deck-strip" data-testid="deck-strip">
      <div className="plan-heading">Standard deck</div>
      {slots.map(([slot, labware]) => (
        <p key={slot} className="file">
          {slot}: {labwareLabel(labware) || labware}
        </p>
      ))}
      {session.deck_assumed ? <p className="hint">Software preview — not a live robot.</p> : null}
      {session.device_note ? <p className="hint">{session.device_note}</p> : null}
    </div>
  );
}

export function StagePane({ session, runningTool, busy, canWatch, onWatch }: Props) {
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
      <Pipeline session={session} runningTool={runningTool} busy={busy} compact={hasDeck} />
      {watchReady ? (
        <OtDeckReplay
          analyze={session.analyze}
          robot={session.robot}
          protocolName={session.goal}
          appType="desktop"
        />
      ) : plrReady ? (
        <PlrDeckReplay plan={session.plan} robot={session.robot} />
      ) : (
        <DeckStrip session={session} />
      )}
      {watchReady ? (
        <div className="watch-cta">
          <button type="button" className="ghost" onClick={onWatch}>
            Expand
          </button>
        </div>
      ) : watchGap ? (
        <p className="hint" data-testid="watch-unavailable">
          {watchGap}
        </p>
      ) : null}
      {!hasDeck && steps.length ? (
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
      ) : !hasDeck ? (
        <p className="hint">
          {isPlanCodegen(session.robot)
            ? "Steps show here after the protocol is written."
            : "The deck preview shows here after checks pass."}
        </p>
      ) : null}
      {!hasDeck ? <IssuesPanel checks={session.checks} /> : null}
    </div>
  );
}
