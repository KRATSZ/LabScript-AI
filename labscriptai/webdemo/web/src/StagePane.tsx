import { watchUnavailableCopy } from "./analysis";
import { planSteps } from "./artifacts";
import { labwareLabel, planStepDisplay } from "./display";
import { deckLabware, deckSketchRows } from "./deckSketch";
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

function DeckSketch({ session }: { session: SessionSnapshot }) {
  const deck = session.hardware?.deck ?? {};
  const rows = deckSketchRows(session.robot, deck);
  return (
    <div className="deck-sketch" data-testid="deck-strip">
      {rows.map((row) => (
        <div
          key={row.join("-")}
          className="deck-sketch-row"
          style={{ gridTemplateColumns: `repeat(${row.length}, minmax(0, 1fr))` }}
        >
          {row.map((slot) => {
            const labware = deckLabware(deck, slot);
            const filled = Boolean(labware);
            return (
              <div key={slot} className={filled ? "deck-cell filled" : "deck-cell empty"}>
                <span className="deck-cell-slot">{slot === "trash" ? "Trash" : slot}</span>
                {filled ? <span className="deck-cell-labware">{labwareLabel(labware) || labware}</span> : null}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

export function StagePane({ session, runningTool, busy, canWatch }: Props) {
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
        <OtDeckReplay
          analyze={session.analyze}
          robot={session.robot}
          protocolName={session.goal}
          appType="desktop"
        />
      ) : plrReady ? (
        <PlrDeckReplay plan={session.plan} robot={session.robot} />
      ) : (
        <div className="stage-wait">
          <div className="stage-wait-copy">
            <h2>Standard deck</h2>
            <p>
              {isPlanCodegen(session.robot)
                ? "The bench preview fills this pane after checks pass."
                : "The deck preview fills this pane after checks pass."}
            </p>
          </div>
          <DeckSketch session={session} />
          <Pipeline session={session} runningTool={runningTool} busy={busy} compact />
          {watchGap ? (
            <p className="hint" data-testid="watch-unavailable">
              {watchGap}
            </p>
          ) : null}
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
          ) : null}
          <IssuesPanel checks={session.checks} />
        </div>
      )}
    </div>
  );
}
