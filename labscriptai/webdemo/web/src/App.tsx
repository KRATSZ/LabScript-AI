import { lazy, Suspense, useCallback, useState } from "react";
import { isPlayableAnalyze } from "./analysis";
import { createSession, streamChat } from "./api";
import { ChatPane } from "./ChatPane";
import { IssuesPanel } from "./IssuesPanel";
import { OverlayChrome } from "./OverlayChrome";
import { Pipeline } from "./Pipeline.tsx";
import { StartForm } from "./StartForm";
import type { ChatMessage, SessionSnapshot } from "./types";

const AnimationOverlay = lazy(() => import("./AnimationOverlay"));

function phaseLabel(phase: string, lit: boolean, canWatch: boolean): string {
  if (canWatch) return "Ready to watch";
  if (lit) return "No animation yet";
  if (phase === "need_hw_slots") return "Missing deck details";
  if (phase === "ready") return "In progress";
  return "Which robot — OT-2 or Flex?";
}

export function App() {
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [overlay, setOverlay] = useState(false);
  const [error, setError] = useState("");
  const [runningTool, setRunningTool] = useState<string | null>(null);

  const applySnapshot = useCallback((snap: SessionSnapshot) => {
    setSession(snap);
  }, []);

  const runTurn = useCallback(
    async (sessionId: string, text: string, alreadyAddedUser: boolean) => {
      setBusy(true);
      setError("");
      if (!alreadyAddedUser && text.trim()) {
        setMessages((prev) => [...prev, { role: "user", text }]);
      }
      setMessages((prev) => [...prev, { role: "assistant", text: "", thinking: "", tools: [] }]);
      try {
        await streamChat(sessionId, text, {
          onThinking: (token) => {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (!last || last.role !== "assistant") return prev;
              next[next.length - 1] = { ...last, thinking: `${last.thinking || ""}${token}` };
              return next;
            });
          },
          onText: (token) => {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (!last || last.role !== "assistant") return prev;
              next[next.length - 1] = { ...last, text: `${last.text}${token}` };
              return next;
            });
          },
          onTool: (name, status) => {
            setRunningTool(status === "start" ? name : status === "done" ? null : name);
          },
          onSnapshot: applySnapshot,
          onChecks: (checks) => {
            setSession((cur) => (cur && checks ? { ...cur, checks, fab: checks.fab } : cur));
          },
          onAnimation: (allowed) => {
            if (allowed) setOverlay(true);
          },
          onError: (message) => setError(message),
          onDone: () => undefined,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setRunningTool(null);
        setBusy(false);
      }
    },
    [applySnapshot]
  );

  const start = async (input: { goal: string; doc: string }) => {
    setBusy(true);
    setError("");
    try {
      const snap = await createSession(input);
      setSession(snap);
      setMessages([
        {
          role: "user",
          text: input.goal,
          meta: input.doc.trim() ? "Notes: draft" : "Notes: none",
        },
      ]);
      await runTurn(snap.id, "", true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  };

  const lit = Boolean(session?.fab.lit);
  const canWatch = lit && isPlayableAnalyze(session?.analyze ?? null);

  return (
    <div className="app">
      <div className="shell">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <h1>LabscriptAI</h1>
            <p>Local chat demo · 127.0.0.1</p>
          </div>
        </div>

        {!session ? (
          <>
            <StartForm busy={busy} onSubmit={start} />
            {error ? <p className="file" style={{ color: "var(--error)" }}>{error}</p> : null}
          </>
        ) : (
          <>
            <div className="card collapsed">
              <div>
                <div>
                  <strong>{phaseLabel(session.phase, lit, canWatch)}</strong>
                </div>
                <div>{session.goal}</div>
                <div>Notes: {session.doc === "none" || !session.doc ? "none" : "draft"}</div>
              </div>
            </div>
            <Pipeline session={session} runningTool={runningTool} busy={busy} />
            <ChatPane
              messages={messages}
              busy={busy}
              onSend={(text) => runTurn(session.id, text, false)}
            />
            <IssuesPanel checks={session.checks} />
            {error ? <p className="file" style={{ color: "var(--error)" }}>{error}</p> : null}
          </>
        )}
      </div>

      {canWatch ? (
        <button className="fab lit" title="Watch animation" onClick={() => setOverlay(true)}>
          Watch animation
        </button>
      ) : null}
      {overlay && canWatch ? (
        <Suspense
          fallback={
            <OverlayChrome onClose={() => setOverlay(false)}>
              <p className="file">Opening…</p>
            </OverlayChrome>
          }
        >
          <AnimationOverlay
            analyze={session?.analyze ?? null}
            robot={session?.robot}
            onClose={() => setOverlay(false)}
          />
        </Suspense>
      ) : null}
    </div>
  );
}
