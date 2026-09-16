import { useEffect, useMemo, useState } from "react";

interface StartResponse {
  ok?: boolean;
  url?: string;
  deck?: string;
  note?: string;
  error?: string;
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
  const key = useMemo(() => JSON.stringify({ robot: robot ?? "", plan: plan ?? null }), [plan, robot]);

  useEffect(() => {
    if (!plan || !robot) return;
    let cancelled = false;
    setUrl("");
    setError("");
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
  }, [key, plan, robot]);

  return (
    <div className="plr-deck-embed" data-testid="plr-deck-replay">
      {error ? (
        <p className="file" style={{ color: "var(--error)" }}>
          {error}
        </p>
      ) : url ? (
        <div className="plr-deck-viewport">
          <iframe className="plr-deck-frame" title="Deck preview" src={url} />
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
