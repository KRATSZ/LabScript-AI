import {
  deckLabware,
  deckSketchAxes,
  deckSketchRows,
  hamiltonStarSketch,
  hamiltonVantageSketch,
  usesStarSketch,
  usesVantageSketch,
} from "./deckSketch";
import { labwareLabel } from "./display";
import type { SessionSnapshot } from "./types";

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

export function DeckSketch({ session }: { session: SessionSnapshot }) {
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
