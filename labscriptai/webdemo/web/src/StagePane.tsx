import { watchUnavailableCopy } from "./analysis";
import { planStepLine, planSteps } from "./artifacts";
import { isPlanCodegen, robotSupportsWatch } from "./devices";
import { IssuesPanel } from "./IssuesPanel";
import { Pipeline } from "./Pipeline.tsx";
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
    return <p className="hint">Assumed deck appears after a device is chosen.</p>;
  }
  return (
    <div className="deck-strip" data-testid="deck-strip">
      <div className="plan-heading">Assumed deck</div>
      {slots.map(([slot, labware]) => (
        <p key={slot} className="file">
          {slot}: {labware}
        </p>
      ))}
      {session.deck_assumed ? <p className="hint">Standard layout — not a live robot.</p> : null}
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
  return (
    <div className="stage-pane" data-testid="stage-pane">
      <Pipeline session={session} runningTool={runningTool} busy={busy} />
      <DeckStrip session={session} />
      {watchReady ? (
        <div className="watch-cta">
          <p className="hint">OT Watch is software animation from 8010 analyze — not a live deck.</p>
          <button type="button" className="primary" onClick={onWatch}>
            Watch animation
          </button>
        </div>
      ) : watchGap ? (
        <p className="hint" data-testid="watch-unavailable">
          {watchGap}
        </p>
      ) : null}
      {steps.length ? (
        <div className="plan-block">
          <div className="plan-heading">Plan IR (step list)</div>
          <div className="plan-steps">
            {steps.slice(0, 20).map((step, index) => (
              <p key={index} className="file">
                {planStepLine(step)}
              </p>
            ))}
          </div>
        </div>
      ) : (
        <p className="hint">
          {isPlanCodegen(session.robot)
            ? "Plan IR and sim status show here after emit_plan / run_checks."
            : "Python Watch uses this pane when checks pass. Otherwise the step table appears."}
        </p>
      )}
      <IssuesPanel checks={session.checks} />
    </div>
  );
}
