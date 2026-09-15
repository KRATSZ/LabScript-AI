import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { sessionCanWatch } from "./analysis";
import { createSession, streamChat } from "./api";
import { ChatPane } from "./ChatPane";
import { robotSupportsWatch } from "./devices";
import { ExportsPanel } from "./ExportsPanel";
import { IssuesPanel } from "./IssuesPanel";
import { OverlayChrome } from "./OverlayChrome";
import { Pipeline } from "./Pipeline.tsx";
import { headerTone, phaseLabel } from "./pipelineLogic.ts";
import { StartForm } from "./StartForm";
import type { ChatMessage, SessionSnapshot, StartInput } from "./types";

const AnimationOverlay = lazy(() => import("./AnimationOverlay"));

export function App() {
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [overlay, setOverlay] = useState(false);
  const [error, setError] = useState("");
  const [runningTool, setRunningTool] = useState<string | null>(null);
  const robotRef = useRef<SessionSnapshot["robot"]>(null);

  const applySnapshot = useCallback((snap: SessionSnapshot) => {
    robotRef.current = snap.robot;
    setSession(snap);
  }, []);

  useEffect(() => {
    const prev = robotRef.current;
    const next = session?.robot ?? null;
    if (prev && next && prev !== next) setOverlay(false);
    robotRef.current = next;
  }, [session?.robot]);

  const runTurn = useCallback(
    async (sessionId: string, text: string, alreadyAddedUser: boolean) => {
      setBusy(true);
      setError("");
      if (!alreadyAddedUser && text.trim()) {
        setMessages((prev) => [...prev, { role: "user", text }]);
      }
      setMessages((prev) => [...prev, { role: "assistant", text: "", thinking: "" }]);
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
            setSession((cur) => (cur && checks ? { ...cur, checks } : cur));
          },
          onAnimation: (allowed) => {
            if (allowed && robotSupportsWatch(robotRef.current)) setOverlay(true);
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

  const changeDevice = () => {
    setOverlay(false);
    setSession(null);
    setMessages([]);
    setError("");
    setRunningTool(null);
  };

  const start = async (input: StartInput) => {
    setBusy(true);
    setError("");
    try {
      const snap = await createSession(input);
      robotRef.current = snap.robot;
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

  const status = session?.checks?.status;
  const canWatch = sessionCanWatch(session?.robot, status, session?.analyze ?? null);
  const planBackend = session?.robot === "Hamilton" || session?.robot === "Tecan";
  const tone = headerTone(status, canWatch);

  return (
    <div className="app">
      <div className="shell">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <h1>LabscriptAI</h1>
            <p>Local chat demo · 127.0.0.1</p>
            {session?.code_service === "down" && !planBackend ? (
              <p className="code-offline">Code service offline — animation unavailable</p>
            ) : null}
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
                  <strong className={tone ? `status-${tone}` : undefined}>
                    {phaseLabel(session.phase, status, canWatch, planBackend, session.checks)}
                  </strong>
                </div>
                <div>{session.goal}</div>
                <div>Notes: {session.doc === "none" || !session.doc ? "none" : "draft"}</div>
              </div>
              <button type="button" className="ghost" disabled={busy} onClick={changeDevice}>
                Change device
              </button>
            </div>
            <Pipeline session={session} runningTool={runningTool} busy={busy} />
            <ChatPane
              messages={messages}
              busy={busy}
              onSend={(text) => runTurn(session.id, text, false)}
            />
            <ExportsPanel session={session} />
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
            key={session?.robot ?? ""}
            analyze={session?.analyze ?? null}
            robot={session?.robot}
            onClose={() => setOverlay(false)}
          />
        </Suspense>
      ) : null}
    </div>
  );
}
