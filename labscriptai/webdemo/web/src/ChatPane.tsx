import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { sanitizeAssistantText } from "./display";
import type { ChatMessage } from "./types";

const THINK_DISPLAY_CAP = 8000;

interface Props {
  messages: ChatMessage[];
  busy: boolean;
  onSend: (text: string) => void;
  robot?: string | null;
}

function MarkdownBody({ text, className }: { text: string; className?: string }) {
  return (
    <div className={className}>
      <ReactMarkdown>{text}</ReactMarkdown>
    </div>
  );
}

function Bubble({
  msg,
  last,
  busy,
  robot,
}: {
  msg: ChatMessage;
  last: boolean;
  busy: boolean;
  robot?: string | null;
}) {
  const showThinking = last && busy && msg.role === "assistant" && Boolean(msg.thinking) && !msg.text;
  const emptyAssistant = msg.role === "assistant" && !msg.text && !msg.thinking;
  if (emptyAssistant && !(busy && last)) return null;
  const shown = (msg.thinking || "").slice(-THINK_DISPLAY_CAP);
  const emptyBusy = emptyAssistant && busy && last;
  const raw = msg.text || "";
  const body = msg.role === "assistant" ? sanitizeAssistantText(raw, robot) : raw;
  return (
    <div className={`bubble-row ${msg.role}`}>
      <div className={`bubble ${msg.role === "user" ? "user" : "bot"}`}>
        {msg.meta ? <div className="meta">{msg.meta}</div> : null}
        {showThinking ? (
          <details className="thinking-box">
            <summary>Thinking</summary>
            <div className="thinking">{shown}</div>
          </details>
        ) : null}
        {emptyBusy && !showThinking ? <div className="typing" aria-label="Writing" /> : null}
        {body ? <MarkdownBody text={body} className={msg.role === "user" ? "md md-user" : "md"} /> : null}
      </div>
    </div>
  );
}

export function ChatPane({ messages, busy, onSend, robot }: Props) {
  const [text, setText] = useState("");
  const historyRef = useRef<HTMLDivElement>(null);
  const areaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = historyRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, busy]);

  const resize = (el: HTMLTextAreaElement | null) => {
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  };

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    const next = text.trim();
    if (!next || busy) return;
    setText("");
    requestAnimationFrame(() => resize(areaRef.current));
    onSend(next);
  };

  return (
    <div className="chat">
      <div className="history" ref={historyRef}>
        {messages.map((msg, i) => (
          <Bubble key={i} msg={msg} last={i === messages.length - 1} busy={busy} robot={robot} />
        ))}
      </div>
      <form className="composer" onSubmit={submit}>
        <textarea
          ref={areaRef}
          rows={1}
          placeholder="Volume, wells, or a confirm…"
          value={text}
          disabled={busy}
          onChange={(e) => {
            setText(e.target.value);
            resize(e.target);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit(e);
            }
          }}
        />
        <button className="send" type="submit" disabled={busy || !text.trim()} aria-label="Send">
          Send
        </button>
      </form>
    </div>
  );
}
