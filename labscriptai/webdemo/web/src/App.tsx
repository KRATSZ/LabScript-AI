import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { sessionCanWatch } from "./analysis";
import { createSession, fetchHealth, streamChat, type DemoHealth } from "./api";
import { ChatPane } from "./ChatPane";
import { isPlanCodegen, robotSupportsWatch } from "./devices";
import { OverlayChrome } from "./OverlayChrome";
import { headerGoalPreview } from "./display";
import { headerTone, phaseLabel } from "./pipelineLogic.ts";
import { RightStage } from "./RightStage";
import { StartForm } from "./StartForm";
import type { AgentEvent, ChatMessage, SessionSnapshot, StartInput } from "./types";

const AnimationOverlay = lazy(() => import("./AnimationOverlay"));

export function App() {
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [overlay, setOverlay] = useState(false);
  const [error, setError] = useState("");
  const [runningTool, setRunningTool] = useState<string | null>(null);
  const [health, setHealth] = useState<DemoHealth | null>(null);
  const robotRef = useRef<SessionSnapshot["robot"]>(null);

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then((next) => {
        if (!cancelled) setHealth(next);
      })
      .catch(() => {
        if (!cancelled) setHealth(null);
      });
    return () => {
      cancelled = true;
    };
  }, [session?.id]);

  const applySnapshot = useCallback((snap: SessionSnapshot) => {
    robotRef.current = snap.robot;
    setSession(snap);
    if (Array.isArray(snap.events)) setEvents(snap.events);
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
          onEvent: (event) => {
            setEvents((prev) => {
              if (prev.some((item) => item.seq === event.seq && item.kind === event.kind)) return prev;
              return [...prev, event].sort((a, b) => a.seq - b.seq);
            });
          },
          onSnapshot: applySnapshot,
          onChecks: (checks) => {
            setSession((cur) => (cur && checks ? { ...cur, checks } : cur));
          },
          onAnimation: () => undefined,
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
    setEvents([]);
    setError("");
    setRunningTool(null);
  };

  const start = async (input: StartInput) => {
    setBusy(true);
    setError("");
    setEvents([]);
    try {
      const snap = await createSession(input);
      robotRef.current = snap.robot;
      setSession(snap);
      if (Array.isArray(snap.events)) setEvents(snap.events);
      setMessages([
        {
          role: "user",
          text: input.goal,
          meta: input.doc.trim() ? "Notes attached" : undefined,
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
  const planBackend = isPlanCodegen(session?.robot);
  const deckPreview =
    planBackend &&
    status === "pass" &&
    Boolean(session?.plan && typeof session.plan === "object");
  const tone = headerTone(status, canWatch);

  return (
    <div className="app">
      <header className="workspace-header">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <h1>LabscriptAI</h1>
            <p>Local lab copilot — on-screen preview only</p>
            {health ? (
              <p className="demo-health" data-testid="demo-health">
                {health.hasKey ? `Model ${health.model}` : "No DeepSeek key"}
                {" · "}
                {health.code_service === "up" ? "preview ready" : "preview down"}
              </p>
            ) : null}
            {session?.code_service === "down" && !planBackend ? (
              <p className="code-offline">Preview service down — OT-2 and Flex scripts stay off</p>
            ) : null}
          </div>
        </div>
        {session ? (
          <div className="card collapsed header-status">
            <div>
              <div>
                <strong className={tone ? `status-${tone}` : undefined}>
                  {phaseLabel(
                    session.phase,
                    status,
                    canWatch,
                    planBackend,
                    session.checks,
                    session.intake_done,
                    Boolean(session.sop?.trim()),
                    deckPreview
                  )}
                </strong>
              </div>
              <div>
                {session.device_label ?? session.robot}
                {session.goal
                  ? ` · ${headerGoalPreview(session.device_label ?? session.robot ?? "", session.goal)}`
                  : ""}
              </div>
              {session.doc && session.doc !== "none" ? <div>Notes attached</div> : null}
            </div>
            <button type="button" className="ghost" disabled={busy} onClick={changeDevice}>
              Change robot
            </button>
          </div>
        ) : null}
      </header>

      <div className="workspace" data-testid="shell">
        <section className="chat-column" data-testid="chat-column">
          {!session ? (
            <div className="start-scroll">
              <StartForm busy={busy} onSubmit={start} />
              {error ? (
                <p className="file" style={{ color: "var(--error)" }}>
                  {error}
                </p>
              ) : null}
            </div>
          ) : (
            <div className="chat-column-body">
              <ChatPane
                messages={messages}
                busy={busy}
                onSend={(text) => runTurn(session.id, text, false)}
              />
              {error ? (
                <p className="file" style={{ color: "var(--error)" }}>
                  {error}
                </p>
              ) : null}
            </div>
          )}
        </section>
        <RightStage
          session={session}
          events={events}
          runningTool={runningTool}
          busy={busy}
          canWatch={canWatch}
          onWatch={() => setOverlay(true)}
        />
      </div>

      {overlay && canWatch && robotSupportsWatch(robotRef.current) ? (
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
