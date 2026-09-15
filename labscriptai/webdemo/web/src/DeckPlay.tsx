import { useEffect, useMemo, useState } from "react";
import { deckSlots, playBeatsFromAnalyze, playBeatsFromSteps, type DeckSlot } from "./playBeats";

const SLOT_ORDER: DeckSlot[] = ["tips", "plate", "reservoir"];
const BEAT_MS = 1100;

function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function DeckPlay({
  steps,
  analyze,
  deck,
  playing,
}: {
  steps: unknown[];
  analyze?: Record<string, unknown> | null;
  deck: Record<string, string>;
  playing: boolean;
}) {
  const beats = useMemo(() => {
    const fromPlan = playBeatsFromSteps(steps);
    return fromPlan.length ? fromPlan : playBeatsFromAnalyze(analyze ?? null);
  }, [steps, analyze]);
  const slots = useMemo(() => deckSlots(deck), [deck]);
  const [index, setIndex] = useState(0);
  const reduced = prefersReducedMotion();

  useEffect(() => {
    setIndex(0);
  }, [beats]);

  useEffect(() => {
    if (!playing || reduced || beats.length < 2) return;
    const timer = window.setInterval(() => {
      setIndex((cur) => (cur + 1) % beats.length);
    }, BEAT_MS);
    return () => window.clearInterval(timer);
  }, [playing, reduced, beats.length]);

  if (!beats.length) return null;
  const beat = beats[Math.min(index, beats.length - 1)];
  const pipetteAt = SLOT_ORDER.indexOf(beat.slot);

  return (
    <div className="deck-play" data-testid="deck-play" aria-live="polite">
      <div className="plan-heading">Run preview</div>
      <p className="hint">Software sketch of the transfer — not a live deck.</p>
      <div className="deck-play-stage">
        <div
          className={`deck-play-pipette${beat.kind === "mix" ? " mix" : ""}`}
          style={{ ["--pipette-at" as string]: String(pipetteAt) }}
          aria-hidden
        />
        <div className="deck-play-slots">
          {SLOT_ORDER.map((id) => (
            <div
              key={id}
              className={`deck-play-slot${beat.slot === id ? " active" : ""}`}
              data-slot={id}
            >
              <strong>{slots[id].name}</strong>
              <span>{slots[id].slot ? `Slot ${slots[id].slot}` : "—"}</span>
            </div>
          ))}
        </div>
      </div>
      <p className="deck-play-caption">{beat.label}</p>
    </div>
  );
}
