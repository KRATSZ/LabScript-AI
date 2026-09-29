import { lazy, Suspense, useCallback, useEffect, useRef, useState, type PointerEvent } from "react";
import { sessionCanWatch } from "./analysis";
import { createSession, fetchHealth, streamChat, type DemoHealth } from "./api";
import { ChatPane } from "./ChatPane";
import { isPlanCodegen, robotSupportsWatch } from "./devices";
import { OverlayChrome } from "./OverlayChrome";
import { headerGoalPreview, hasAttachedNotes } from "./display";
import { LanguageSwitch } from "./LanguageSwitch";
import { useLang } from "./LangContext";
import { deckReadyLine, headerTone, phaseLabel } from "./pipelineLogic.ts";
import { clampChatPct, loadChatPct, saveChatPct } from "./paneSplit.ts";
import { RightStage } from "./RightStage";
import { StartForm } from "./StartForm";
import { HistoryRail } from "./HistoryRail";
import { archiveThread, loadThreads, persistFinished, railThreads, type ArchivedThread } from "./threadArchive";
import { thoughtNotesFromChat, thoughtTurnsFromChat } from "./trajectoryLogic";
import type { AgentEvent, ChatMessage, SessionSnapshot, StartInput } from "./types";

const AnimationOverlay = lazy(() => import("./AnimationOverlay"));

function patchLastAssistant(prev: ChatMessage[], field: "text" | "thinking", token: string): ChatMessage[] {
  const last = prev[prev.length - 1];
  if (!last || last.role !== "assistant") return prev;
  return [...prev.slice(0, -1), { ...last, [field]: `${last[field] || ""}${token}` }];
}

function ErrorNote({ error }: { error: string }) {
  if (!error) return null;
  return (
    <p className="file error-note" role="alert">
      {error}
    </p>
  );
}

export function App() {
  const { lang, t } = useLang();
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [canRetry, setCanRetry] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const lastRequest = useRef<
    | { kind: "start"; input: StartInput }
    | { kind: "chat"; sessionId: string; text: string }
    | null
  >(null);
  const [overlay, setOverlay] = useState(false);
  const [error, setError] = useState("");
  const [runningTool, setRunningTool] = useState<string | null>(null);
  const [health, setHealth] = useState<DemoHealth | null>(null);
  const [notesAttached, setNotesAttached] = useState(false);
  const [chatPct, setChatPct] = useState(0.38);
  const [dragging, setDragging] = useState(false);
  const [threads, setThreads] = useState<ArchivedThread[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const robotRef = useRef<SessionSnapshot["robot"]>(null);
  const workspaceRef = useRef<HTMLDivElement>(null);
  const chatPctRef = useRef(chatPct);
  const dragRef = useRef<{ startX: number; startPct: number; width: number } | null>(null);
  chatPctRef.current = chatPct;

  useEffect(() => {
    const widthOf = () => workspaceRef.current?.clientWidth || 1280;
    setChatPct(loadChatPct(widthOf()));
    setThreads(loadThreads());
    const onResize = () => setChatPct((pct) => clampChatPct(pct, widthOf()));
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

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

  useEffect(() => {
    if (!session?.id) return;
    void fetch(`/api/session/${session.id}/language`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language: lang }),
    }).catch(() => undefined);
  }, [lang, session?.id]);

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
      const controller = new AbortController();
      abortRef.current = controller;
      lastRequest.current = { kind: "chat", sessionId, text };
      setCanRetry(false);
      setBusy(true);
      setError("");
      if (!alreadyAddedUser && text.trim()) {
        setMessages((prev) => [...prev, { role: "user", text }]);
      }
      setMessages((prev) => [...prev, { role: "assistant", text: "", thinking: "" }]);
      try {
        await streamChat(sessionId, text, {
          onThinking: (token) => setMessages((prev) => patchLastAssistant(prev, "thinking", token)),
          onText: (token) => setMessages((prev) => patchLastAssistant(prev, "text", token)),
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
        }, controller.signal);
        if (!controller.signal.aborted) setCanRetry(false);
      } catch (err) {
        const aborted = controller.signal.aborted || (err instanceof DOMException && err.name === "AbortError");
        if (aborted) setCanRetry(true);
        else setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (abortRef.current === controller) abortRef.current = null;
        setRunningTool(null);
        setBusy(false);
      }
    },
    [applySnapshot]
  );

  const parkCurrent = useCallback(() => {
    setThreads((prev) => archiveThread(prev, session, messages, events));
  }, [session, messages, events]);

  useEffect(() => {
    setThreads((prev) => persistFinished(prev, session, messages, events));
  }, [session, messages, events]);

  const changeDevice = () => {
    parkCurrent();
    setOverlay(false);
    setSession(null);
    setMessages([]);
    setEvents([]);
    setError("");
    setRunningTool(null);
    setNotesAttached(false);
  };

  const cancelTurn = () => {
    abortRef.current?.abort();
    setCanRetry(true);
    setRunningTool(null);
    setBusy(false);
  };

  const retryTurn = () => {
    const last = lastRequest.current;
    if (!last || busy) return;
    if (last.kind === "start") {
      void start(last.input);
      return;
    }
    void runTurn(last.sessionId, last.text, true);
  };

  const start = async (input: StartInput) => {
    const controller = new AbortController();
    abortRef.current = controller;
    lastRequest.current = { kind: "start", input };
    parkCurrent();
    setCanRetry(false);
    setBusy(true);
    setError("");
    setEvents([]);
    setNotesAttached(hasAttachedNotes(input.doc));
    try {
      const snap = await createSession({ ...input, language: lang }, controller.signal);
      robotRef.current = snap.robot;
      setSession(snap);
      if (Array.isArray(snap.events)) setEvents(snap.events);
      setMessages([
        {
          role: "user",
          text: input.goal,
          meta: hasAttachedNotes(input.doc) ? "Notes attached" : undefined,
        },
      ]);
      if (controller.signal.aborted) {
        setCanRetry(true);
        setBusy(false);
        return;
      }
      await runTurn(snap.id, "", true);
    } catch (err) {
      const aborted = controller.signal.aborted || (err instanceof DOMException && err.name === "AbortError");
      if (aborted) setCanRetry(true);
      else setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  };

  const status = session?.checks?.status;
  const canWatch = sessionCanWatch(session?.robot, status, session?.analyze ?? null);
  const planBackend = isPlanCodegen(session?.robot);
  const deckPreview = planBackend && status === "pass" && Boolean(session?.plan && typeof session.plan === "object");
  const tone = headerTone(status, canWatch && !busy);
  const lastMessage = messages[messages.length - 1];
  const thinkingLive =
    busy && lastMessage?.role === "assistant" && Boolean(lastMessage.thinking) && !lastMessage.text && !runningTool;
  const hasRail = Boolean(session) || threads.length > 0;
  const listedThreads = railThreads(threads, session, messages, events);
  const robotLabel = session?.device_label ?? session?.robot ?? "";

  const onSeamPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    const width = workspaceRef.current?.clientWidth || 1280;
    dragRef.current = { startX: event.clientX, startPct: chatPct, width };
    setDragging(true);
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const onSeamPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag) return;
    setChatPct(clampChatPct(drag.startPct + (event.clientX - drag.startX) / drag.width, drag.width));
  };
  const onSeamPointerUp = () => {
    if (!dragRef.current) return;
    dragRef.current = null;
    setDragging(false);
    saveChatPct(chatPctRef.current);
  };

  const restoreThread = (id: string) => {
    if (session?.id === id) return;
    const thread = listedThreads.find((item) => item.id === id) ?? threads.find((item) => item.id === id);
    if (!thread) return;
    parkCurrent();
    robotRef.current = thread.session.robot;
    setSession(thread.session);
    setMessages(thread.messages);
    setEvents(thread.events);
    setError("");
    setOverlay(false);
    setNotesAttached(hasAttachedNotes(thread.session.doc));
  };

  return (
    <div className="app">
      <header className="workspace-header">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <h1>LabscriptAI</h1>
            {!session ? <p>{t("On-screen preview only")}</p> : null}
          </div>
        </div>
        {session ? (
          <div className="header-status">
            <strong className={tone ? `status-${tone}` : undefined} data-testid="check-verdict">
              {t(
                phaseLabel(
                  session.phase,
                  status,
                  canWatch,
                  planBackend,
                  session.checks,
                  session.intake_done,
                  Boolean(session.sop?.trim()),
                  deckPreview,
                  busy
                )
              )}
            </strong>
            {deckReadyLine(canWatch, busy, status) ? (
              <span data-testid="deck-ready">{t(deckReadyLine(canWatch, busy, status) || "")}</span>
            ) : null}
            <span>
              {t(robotLabel)}
              {session.goal ? ` · ${headerGoalPreview(robotLabel, session.goal)}` : ""}
            </span>
            {notesAttached ? <span>{t("Notes attached")}</span> : null}
            {session.code_service === "down" && !planBackend ? (
              <span className="code-offline">{t("Preview service down — OT-2 and Flex scripts stay off")}</span>
            ) : null}
            <button type="button" className="ghost" disabled={busy} onClick={changeDevice}>
              {t("Change robot")}
            </button>
          </div>
        ) : health && (!health.hasKey || health.code_service !== "up") ? (
          <p className="demo-health" data-testid="demo-health">
            {health.hasKey ? t("preview down") : t("No DeepSeek key")}
          </p>
        ) : health ? (
          <p className="demo-health" data-testid="demo-health">
            {t("preview ready")}
          </p>
        ) : null}
        <LanguageSwitch />
      </header>

      <div
        className={[
          "workspace",
          dragging ? "dragging" : "",
          hasRail ? "has-history" : "",
          hasRail && historyOpen ? "history-open" : "",
          session ? "session-mode" : "start-mode",
          canWatch ? "watch-ready" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        data-testid="shell"
        ref={workspaceRef}
        style={{ ["--chat-pct" as string]: `${(chatPct * 100).toFixed(2)}%` }}
      >
        <section className="chat-column" data-testid="chat-column">
          {!session ? (
            <div className="start-scroll">
              <StartForm busy={busy} onSubmit={start} onCancel={cancelTurn} />
              <ErrorNote error={error} />
              {!busy && canRetry ? (
                <button type="button" className="primary retry-turn" data-testid="retry-turn" onClick={retryTurn}>
                  {t("Retry")}
                </button>
              ) : null}
            </div>
          ) : (
            <div className="chat-column-body">
              <ChatPane
                messages={messages}
                busy={busy}
                robot={session.robot}
                session={session}
                canRetry={canRetry}
                onCancel={cancelTurn}
                onRetry={retryTurn}
                onSend={(text) => runTurn(session.id, text, false)}
              />
              <ErrorNote error={error} />
            </div>
          )}
        </section>
        <div
          className="split-seam"
          role="separator"
          aria-orientation="vertical"
          aria-label={t("Resize chat")}
          data-testid="split-seam"
          onPointerDown={onSeamPointerDown}
          onPointerMove={onSeamPointerMove}
          onPointerUp={onSeamPointerUp}
          onPointerCancel={onSeamPointerUp}
        />
        <RightStage
          session={session}
          events={events}
          runningTool={runningTool}
          busy={busy}
          canWatch={canWatch}
          onWatch={() => setOverlay(true)}
          live={{
            thinking: thinkingLive,
            thoughtTurns: thoughtTurnsFromChat(messages),
            thoughtNotes: thoughtNotesFromChat(messages),
            thinkingNote: lastMessage?.thinking,
          }}
        />
        <HistoryRail
          threads={listedThreads}
          currentId={session?.id}
          open={historyOpen}
          onToggle={() => setHistoryOpen((open) => !open)}
          onSelect={restoreThread}
        />
      </div>

      {overlay && canWatch && robotSupportsWatch(robotRef.current) ? (
        <Suspense
          fallback={
            <OverlayChrome onClose={() => setOverlay(false)}>
              <p className="file">{t("Opening…")}</p>
            </OverlayChrome>
          }
        >
          <AnimationOverlay
            key={session?.robot ?? ""}
            session={session}
            analyze={session?.analyze ?? null}
            robot={session?.robot}
            onClose={() => setOverlay(false)}
          />
        </Suspense>
      ) : null}
    </div>
  );
}
