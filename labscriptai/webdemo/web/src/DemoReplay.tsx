import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { ProtocolSummaryCard } from "./SummaryCard";
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

function findPlaybackRange(root: HTMLElement | null): HTMLInputElement | null {
  if (!root) return null;
  const ranges = [...root.querySelectorAll<HTMLInputElement>('input[type="range"]')];
  return ranges.find((el) => !el.closest(".demo-replay-scrub")) ?? ranges[0] ?? null;
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

  useEffect(() => {
    setIndex(clampStepIndex(current, total));
  }, [current, total]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const onInput = (event: Event) => {
      const el = event.target as HTMLInputElement;
      if (!el.closest(".ot-deck-embed") && !el.closest(".plr-deck-embed")) return;
      if (el.closest(".demo-replay-scrub")) return;
      const max = Number(el.max) || Math.max(total - 1, 1);
      const min = Number(el.min) || 0;
      const value = Number(el.value);
      const next = clampStepIndex(((value - min) / Math.max(max - min, 1)) * (total - 1), total);
      setIndex(next);
    };
    host.addEventListener("input", onInput, true);
    host.addEventListener("change", onInput, true);
    return () => {
      host.removeEventListener("input", onInput, true);
      host.removeEventListener("change", onInput, true);
    };
  }, [total]);

  useEffect(() => {
    const el = listRef.current?.querySelector('[data-status="current"]');
    if (el instanceof HTMLElement) el.scrollIntoView({ block: "nearest" });
  }, [index]);

  const seek = (next: number) => {
    const clamped = clampStepIndex(next, total);
    setIndex(clamped);
    onSeek?.(clamped);
    const range = findPlaybackRange(hostRef.current);
    if (!range) return;
    const max = Number(range.max);
    const min = Number(range.min) || 0;
    const span = Number.isFinite(max) && max > min ? max - min : Math.max(total - 1, 1);
    range.value = String(min + Math.round((clamped / Math.max(total - 1, 1)) * span));
    range.dispatchEvent(new Event("input", { bubbles: true }));
    range.dispatchEvent(new Event("change", { bubbles: true }));
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
