import { clampStepIndex } from "./replaySteps";

/** Thumb inset used by @opentrons/components TimelineScrubber TrackSlider. */
const TRACK_INSET_PX = 6;

export function visualizerPlayPercent(index: number, total: number): number {
  if (total <= 1) return 0;
  return (clampStepIndex(index, total) / (total - 1)) * 100;
}

export function visualizerIndexFromPercent(percent: number, total: number): number {
  if (total <= 1) return 0;
  const pct = Math.min(100, Math.max(0, Number(percent)));
  if (!Number.isFinite(pct)) return 0;
  return clampStepIndex((pct / 100) * (total - 1), total);
}

export function findVisualizerTrack(root: HTMLElement | null): HTMLElement | null {
  if (!root) return null;
  const embed =
    root.querySelector<HTMLElement>(".ot-deck-embed") ??
    (root.classList.contains("ot-deck-embed") ? root : null);
  if (!embed) return null;
  return embed.querySelector<HTMLElement>('[class*="track_container"]');
}

export function readTrackPercent(track: HTMLElement | null): number | null {
  if (!track) return null;
  const bar = track.querySelector<HTMLElement>('[class*="track_progress"]');
  if (!bar) return null;
  const raw = (bar.style.width || "").trim();
  const match = raw.match(/^([\d.]+)\s*%$/);
  if (!match) return null;
  const pct = Number(match[1]);
  return Number.isFinite(pct) ? pct : null;
}

export function clientXForTrackPercent(track: HTMLElement, percent: number): number {
  const rect = track.getBoundingClientRect();
  const usable = Math.max(rect.width - TRACK_INSET_PX * 2, 0);
  const pct = Math.min(100, Math.max(0, percent));
  return rect.x + TRACK_INSET_PX + (pct / 100) * usable;
}

export function seekVisualizerTrack(track: HTMLElement, percent: number): void {
  const rect = track.getBoundingClientRect();
  if (rect.width <= 0) return;
  const x = clientXForTrackPercent(track, percent);
  const y = rect.top + rect.height / 2;
  const opts: MouseEventInit = {
    bubbles: true,
    cancelable: true,
    button: 0,
    buttons: 1,
    clientX: x,
    clientY: y,
    view: window,
  };
  track.dispatchEvent(new MouseEvent("mousedown", opts));
  window.dispatchEvent(new MouseEvent("mouseup", opts));
}
