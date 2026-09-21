import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { ProtocolSummaryCard } from "./SummaryCard";
import {
  findVisualizerTrack,
  pauseVisualizer,
  readTrackPercent,
  seekVisualizerTrack,
  visualizerIndexFromPercent,
  visualizerPlayPercent,
} from "./otPlaybackSync";
import { clampStepIndex, replayStepsFor, type ReplayStep } from "./replaySteps";
import { useLang } from "./LangContext";
import type { SessionSnapshot } from "./types";

interface Props {
  session: SessionSnapshot;
  children: ReactNode;
  current?: number;
  totalHint?: number;
  onSeek?: (index: number) => void;
}

function stepStatus(index: number, current: number): "done" | "current" | "todo" {
  if (index < current) return "done";
  if (index === current) return "current";
  return "todo";
}

export function DemoReplay({ session, children, current = 0, totalHint, onSeek }: Props) {
  const { t } = useLang();
  const hostRef = useRef<HTMLDivElement>(null);
  const steps = useMemo(() => replayStepsFor(session), [session]);
  const total = Math.max(steps.length, totalHint ?? 0, 1);
  const [index, setIndex] = useState(() => clampStepIndex(current, total));
  const listRef = useRef<HTMLUListElement>(null);
  const suppressUntil = useRef(0);

  useEffect(() => {
    setIndex(clampStepIndex(current, total));
  }, [current, total]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let raf = 0;
    const syncFromVisualizer = () => {
      if (Date.now() < suppressUntil.current) return;
      const track = findVisualizerTrack(host);
      if (!track) return;
      const pct = readTrackPercent(track);
      if (pct == null) return;
      const next = visualizerIndexFromPercent(pct, total);
      setIndex((cur) => (cur === next ? cur : next));
    };
    const mo = new MutationObserver(() => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(syncFromVisualizer);
    });
    mo.observe(host, { attributes: true, subtree: true, attributeFilter: ["style", "class"] });
    const timer = window.setInterval(syncFromVisualizer, 80);
    syncFromVisualizer();
    return () => {
      mo.disconnect();
      window.clearInterval(timer);
      cancelAnimationFrame(raf);
    };
  }, [total]);

  useEffect(() => {
    const el = listRef.current?.querySelector('[data-status="current"]');
    if (el instanceof HTMLElement) el.scrollIntoView({ block: "nearest" });
  }, [index]);

  const seek = (next: number) => {
    const clamped = clampStepIndex(next, total);
    suppressUntil.current = Date.now() + 160;
    setIndex(clamped);
    onSeek?.(clamped);
    const host = hostRef.current;
    if (!host) return;
    pauseVisualizer(host);
    const track = findVisualizerTrack(host);
    if (!track || track.getBoundingClientRect().width <= 0) return;
    seekVisualizerTrack(track, visualizerPlayPercent(clamped, total));
  };

  const visible: ReplayStep[] = steps.length
    ? steps
    : Array.from({ length: total }, (_, i) => ({
        id: `slot-${i}`,
        index: i,
        kind: "step",
        label: `${t("Steps")} ${i + 1}`,
        detail: "",
      }));

  return (
    <div className="demo-replay" data-testid="demo-replay" ref={hostRef}>
      <div className="demo-replay-deck">{children}</div>
      <aside className="demo-replay-side" data-testid="demo-replay-side">
        <ProtocolSummaryCard session={session} />
        <div className="plan-heading">{t("Steps")}</div>
        <p className="hint">{t("Previous steps stay listed")}</p>
        <ul className="demo-step-list" ref={listRef} data-testid="demo-step-list">
          {visible.map((step) => {
            const status = stepStatus(step.index, index);
            return (
              <li
                key={step.id}
                className={`demo-step ${status}`}
                data-status={status}
                data-kind={step.kind}
                data-testid={status === "current" ? "demo-step-current" : undefined}
              >
                <button type="button" className="demo-step-btn" onClick={() => seek(step.index)}>
                  <span className="demo-step-index">{step.index + 1}</span>
                  <span className="demo-step-body">
                    <strong>{step.label}</strong>
                    {step.detail ? <span>{step.detail}</span> : null}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </aside>
      <div className="demo-replay-scrub" data-testid="demo-progress">
        <label className="replay-progress-label" htmlFor="demo-progress-range">
          {t("Demo progress")}
          {visible[index] ? ` · ${visible[index].label} · ${index + 1} / ${visible.length}` : ""}
        </label>
        <input
          id="demo-progress-range"
          type="range"
          min={0}
          max={Math.max(visible.length - 1, 0)}
          step={1}
          value={index}
          aria-label={t("Demo progress")}
          data-testid="demo-progress-range"
          onChange={(event) => seek(Number(event.target.value))}
        />
      </div>
    </div>
  );
}
