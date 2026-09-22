import { watchUnavailableCopy } from "./analysis";
import { planSteps } from "./artifacts";
import { labwareLabel, planStepDisplay } from "./display";
import { deckLabware, deckSketchAxes, deckSketchRows, hamiltonStarSketch, hamiltonVantageSketch, usesStarSketch, usesVantageSketch } from "./deckSketch";
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

function DeckCell({ label, labware }: { label: string; labware: string }) {
  const filled = Boolean(labware);
  return (
    <div className={filled ? "deck-cell filled" : "deck-cell empty"}>
      <span className="deck-cell-slot">{label}</span>
      {filled ? <span className="deck-cell-labware">{labwareLabel(labware) || labware}</span> : null}
    </div>
  );
}

function StarDeckSketch({ session }: { session: SessionSnapshot }) {
  const carriers = hamiltonStarSketch(session.hardware?.deck ?? {});
  return (
    <div className="star-sketch" data-testid="deck-strip" data-origin-slot="tip-0">
      {carriers.map((carrier) => (
        <div key={carrier.id} className="star-carrier">
          <div className="star-carrier-head">
            <span>{carrier.title}</span>
            <span className="star-carrier-rails">rails {carrier.rails}</span>
          </div>
          <div
            className="star-carrier-sites"
            style={{ gridTemplateColumns: `repeat(${carrier.sites.length}, minmax(0, 1fr))` }}
          >
            {carrier.sites.map((site) => (
              <DeckCell key={site.id} label={site.label} labware={site.labware} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function VantageDeckSketch({ session }: { session: SessionSnapshot }) {
  const sketch = hamiltonVantageSketch(session.hardware?.deck ?? {});
  return (
    <div className="vantage-sketch" data-testid="deck-strip" data-origin-slot="tips">
      <div className="vantage-sketch-head">
        <span>Vantage {sketch.size}</span>
        <span className="vantage-sketch-rails">{sketch.rails} rails</span>
      </div>
      <div className="vantage-railbed">
        {sketch.items.map((item) => (
          <DeckCell key={item.id} label={item.label} labware={item.labware} />
        ))}
      </div>
    </div>
  );
}

function DeckSketch({ session }: { session: SessionSnapshot }) {
  if (usesStarSketch(session.robot)) return <StarDeckSketch session={session} />;
  if (usesVantageSketch(session.robot)) return <VantageDeckSketch session={session} />;
  const deck = session.hardware?.deck ?? {};
  const rows = deckSketchRows(session.robot, deck);
  const axes = deckSketchAxes(session.robot);
  const origin = rows[0]?.[0] ?? "";
  return (
    <div
      className={axes ? "deck-sketch has-axes" : "deck-sketch"}
      data-testid="deck-strip"
      data-origin-slot={origin}
    >
      {axes ? (
        <div className="deck-axis-rows" aria-hidden="true" data-testid="flex-axis-rows">
          {axes.rows.map((label) => (
            <span key={label} className="deck-axis-tick">
              {label}
            </span>
          ))}
        </div>
      ) : null}
      <div className="deck-sketch-grid">
        {rows.map((row) => (
          <div
            key={row.join("-")}
            className="deck-sketch-row"
            style={{ gridTemplateColumns: `repeat(${row.length}, minmax(0, 1fr))` }}
          >
            {row.map((slot) => (
              <DeckCell
                key={slot}
                label={slot === "trash" ? "Trash" : slot}
                labware={deckLabware(deck, slot)}
              />
            ))}
          </div>
        ))}
        {axes ? (
          <div className="deck-axis-cols" aria-hidden="true" data-testid="flex-axis-cols">
            {axes.cols.map((label) => (
              <span key={label} className="deck-axis-tick">
                {label}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
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
  const previewDown =
    session.code_service === "down" && isPlanCodegen(session.robot)
      ? "Preview service down. The bench preview stays off until that service is up."
      : null;
  const plrReady =
    isPlanCodegen(session.robot) &&
    session.checks?.status === "pass" &&
    Boolean(session.plan && typeof session.plan === "object") &&
    session.code_service !== "down";
  const hasDeck = watchReady || plrReady;
  const waitHint = waitGapCopy(watchGap, previewDown);
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
        <PlrDeckReplay
          plan={session.plan}
          robot={session.robot}
          previewUp={session.code_service !== "down"}
          session={session}
        />
      ) : (
        <div className="stage-wait">
          <div className="stage-wait-copy">
            <h2>{t("Standard deck")}</h2>
            <p>
              {isPlanCodegen(session.robot) && session.code_service === "down"
                ? t("The bench preview stays off while the preview service is down.")
                : isPlanCodegen(session.robot)
                  ? t("The bench preview fills this pane after checks pass.")
                  : t("The deck preview fills this pane after checks pass.")}
            </p>
          </div>
          <DeckSketch session={session} />
          <Pipeline session={session} runningTool={runningTool} busy={busy} compact />
          {waitHint ? (
            <p className="hint" data-testid="watch-unavailable">
              {waitHint}
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
          <IssuesPanel checks={session.checks} />
        </div>
      )}
    </div>
  );
}

function waitGapCopy(watchGap: string | null, previewDown: string | null): string | null {
  return watchGap || previewDown;
}
