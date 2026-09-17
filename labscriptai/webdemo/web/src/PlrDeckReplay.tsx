import { useEffect, useMemo, useState } from "react";

interface StartResponse {
  ok?: boolean;
  url?: string;
  deck?: string;
  note?: string;
  error?: string;
}

interface Progress {
  step: number;
  total: number;
  label: string;
  playing: boolean;
}

interface StatusResponse {
  ok?: boolean;
  running?: boolean;
  progress?: Progress;
}

const STEP_LABELS: Record<string, string> = {
  "Pick Tips": "Pick tips",
  "Drop Tips": "Drop tips",
  Aspirate: "Aspirate",
  Dispense: "Dispense",
  Mix: "Mix",
  Wait: "Wait",
};

function planStepCount(plan: Record<string, unknown> | null): number {
  const steps = plan?.steps;
  return Array.isArray(steps) ? steps.length : 0;
}

function progressCopy(progress: Progress | null, fallbackTotal: number): string {
  if (!progress || !progress.total) {
    return fallbackTotal ? `0 / ${fallbackTotal}` : "";
  }
  const label = STEP_LABELS[progress.label] || progress.label;
  const fraction = `${progress.step} / ${progress.total}`;
  if (!label) return progress.playing ? fraction : "Done";
  return `${label} · ${fraction}`;
}

export function PlrDeckReplay({
  plan,
  robot,
}: {
  plan: Record<string, unknown> | null;
  robot?: string | null;
}) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [progress, setProgress] = useState<Progress | null>(null);
  const key = useMemo(() => JSON.stringify({ robot: robot ?? "", plan: plan ?? null }), [plan, robot]);
  const fallbackTotal = planStepCount(plan);

  useEffect(() => {
    if (!plan || !robot) return;
    let cancelled = false;
    setUrl("");
    setError("");
    setProgress({ step: 0, total: fallbackTotal, label: "", playing: true });
    fetch("/api/plr/visualizer/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan, robot }),
    })
      .then(async (response) => {
        const body = (await response.json().catch(() => null)) as StartResponse | null;
        if (cancelled) return;
        if (!response.ok || !body?.ok || !body.url) {
          setError(body?.error || "Deck preview could not start.");
          return;
        }
        setUrl(body.url);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
      void fetch("/api/plr/visualizer/stop", { method: "POST" }).catch(() => undefined);
    };
  }, [key, plan, robot, fallbackTotal]);

  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    const tick = () => {
      fetch("/api/plr/visualizer/status")
        .then(async (response) => (await response.json().catch(() => null)) as StatusResponse | null)
        .then((body) => {
          if (cancelled || !body?.progress) return;
          setProgress({
            step: body.progress.step,
            total: body.progress.total,
            label: body.progress.label,
            playing: body.progress.playing,
          });
        })
        .catch(() => undefined);
    };
    tick();
    const id = window.setInterval(tick, 250);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [url]);

  const total = progress?.total || fallbackTotal;
  const pct = total > 0 ? Math.min(100, Math.round(((progress?.step || 0) / total) * 100)) : 0;
  const copy = progressCopy(progress, fallbackTotal);

  return (
    <div className="plr-deck-embed" data-testid="plr-deck-replay">
      {error ? (
        <p className="file" style={{ color: "var(--error)" }}>
          {error}
        </p>
      ) : url ? (
        <div className="plr-deck-viewport">
          <iframe className="plr-deck-frame" title="Deck preview" src={url} />
          {total > 0 ? (
            <div className="replay-progress" data-testid="plr-progress">
              <div className="replay-progress-track">
                <div className="replay-progress-fill" style={{ width: `${pct}%` }} />
              </div>
              <span className="replay-progress-label">{copy}</span>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="stage-empty">
          <h2>Deck</h2>
          <p>Opening the bench preview…</p>
        </div>
      )}
    </div>
  );
}
