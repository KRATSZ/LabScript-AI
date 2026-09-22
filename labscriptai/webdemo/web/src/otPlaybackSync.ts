import { clampStepIndex } from "./replaySteps";

/** Thumb inset used by @opentrons/components TimelineScrubber TrackSlider. */
const TRACK_INSET_PX = 6;

interface ReactFiber {
  memoizedProps?: Record<string, unknown> | null;
  pendingProps?: Record<string, unknown> | null;
  return?: ReactFiber | null;
}

interface VisualizerPlayback {
  setSelectedCommand?: (id: string | null) => void;
  handlePlayPause?: () => void;
  isPlaying?: boolean;
  onTrackChange?: (id: string, percent: number) => void;
  commands?: Array<{ id?: string }>;
}

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

export function findVisualizerEmbed(root: HTMLElement | null): HTMLElement | null {
  if (!root) return null;
  if (root.classList.contains("ot-deck-embed")) return root;
  return root.querySelector<HTMLElement>(".ot-deck-embed");
}

export function findVisualizerTrack(root: HTMLElement | null): HTMLElement | null {
  const embed = findVisualizerEmbed(root);
  if (!embed) return null;
  return embed.querySelector<HTMLElement>('[class*="track_container"]');
}

function fiberOf(node: object | null | undefined): ReactFiber | null {
  if (!node) return null;
  const key = Object.keys(node).find((name) => name.startsWith("__reactFiber$") || name.startsWith("__reactInternalInstance$"));
  if (!key) return null;
  const fiber = (node as Record<string, unknown>)[key];
  return fiber && typeof fiber === "object" ? (fiber as ReactFiber) : null;
}

function fiberProps(fiber: ReactFiber | null | undefined): Record<string, unknown> | null {
  if (!fiber) return null;
  const memo = fiber.memoizedProps;
  if (memo && typeof memo === "object") return memo;
  const pending = fiber.pendingProps;
  if (pending && typeof pending === "object") return pending;
  return null;
}

/** Walk React fibers from a DOM node to find ProtocolVisualization playback props. */
export function visualizerPlaybackFromNode(node: object | null | undefined): VisualizerPlayback | null {
  let fiber = fiberOf(node);
  const seen = new Set<ReactFiber>();
  const found: VisualizerPlayback = {};
  while (fiber && !seen.has(fiber)) {
    seen.add(fiber);
    const props = fiberProps(fiber);
    if (props) {
      if (typeof props.setSelectedCommand === "function" && !found.setSelectedCommand) {
        found.setSelectedCommand = props.setSelectedCommand as (id: string | null) => void;
      }
      if (typeof props.handlePlayPause === "function" && !found.handlePlayPause) {
        found.handlePlayPause = props.handlePlayPause as () => void;
      }
      if (typeof props.isPlaying === "boolean" && found.isPlaying == null) {
        found.isPlaying = props.isPlaying;
      }
      if (typeof props.onChange === "function" && !found.onTrackChange && props.track) {
        found.onTrackChange = props.onChange as (id: string, percent: number) => void;
      }
      if (Array.isArray(props.commands) && !found.commands) {
        found.commands = props.commands as Array<{ id?: string }>;
      }
    }
    fiber = fiber.return ?? null;
  }
  return found.setSelectedCommand || found.onTrackChange ? found : null;
}

export function findVisualizerPlayback(root: HTMLElement | null): VisualizerPlayback | null {
  const embed = findVisualizerEmbed(root);
  if (!embed) return null;
  const track = embed.querySelector<HTMLElement>('[class*="track_container"]');
  const controls = embed.querySelector<HTMLElement>('[class*="playbackcontrols"]');
  return visualizerPlaybackFromNode(track) ?? visualizerPlaybackFromNode(controls) ?? visualizerPlaybackFromNode(embed);
}

export function pauseVisualizer(root: HTMLElement | null): void {
  const playback = findVisualizerPlayback(root);
  if (playback?.isPlaying && playback.handlePlayPause) {
    playback.handlePlayPause();
    return;
  }
  const embed = findVisualizerEmbed(root);
  if (!embed) return;
  const pause = [...embed.querySelectorAll("button")].find((btn) => {
    const label = (btn.getAttribute("aria-label") || "").toLowerCase();
    return label === "pause" || label.includes("pause");
  });
  pause?.click();
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
    composed: true,
    button: 0,
    buttons: 1,
    clientX: x,
    clientY: y,
    view: window,
  };
  track.dispatchEvent(new MouseEvent("mousedown", opts));
  const up = { ...opts, buttons: 0 };
  track.dispatchEvent(new MouseEvent("mouseup", up));
  window.dispatchEvent(new MouseEvent("mouseup", up));
}

/**
 * Seek official Watch to a playable command.
 * ProtocolVisualization keeps the current command in React state (`setSelectedCommand`).
 * Faking TimelineScrubber mouse events does not reliably reach that setter.
 */
export function seekVisualizerPlayback(
  root: HTMLElement | null,
  opts: { commandId?: string; percent?: number }
): boolean {
  if (!root) return false;
  pauseVisualizer(root);
  const playback = findVisualizerPlayback(root);
  const commandId = opts.commandId?.trim();
  if (commandId && playback?.setSelectedCommand) {
    playback.setSelectedCommand(commandId);
    return true;
  }
  if (opts.percent != null && playback?.onTrackChange) {
    playback.onTrackChange("protocol-timeline", opts.percent);
    return true;
  }
  if (commandId && playback?.commands?.length && playback.setSelectedCommand) {
    const hit = playback.commands.find((item) => item.id === commandId);
    if (hit?.id) {
      playback.setSelectedCommand(hit.id);
      return true;
    }
  }
  const track = findVisualizerTrack(root);
  if (!track || opts.percent == null || track.getBoundingClientRect().width <= 0) return false;
  seekVisualizerTrack(track, opts.percent);
  return true;
}
