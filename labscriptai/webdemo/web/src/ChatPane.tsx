import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "./types";

const THINK_DISPLAY_CAP = 8000;

interface Props {
  messages: ChatMessage[];
  busy: boolean;
  onSend: (text: string) => void;
}

export function ChatPane({ messages, busy, onSend }: Props) {
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
    el.style.height = `${Math.min(el.scrollHeight, 96)}px`;
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
        {messages.map((msg, i) => {
          const last = i === messages.length - 1;
          const showThinking = msg.role === "assistant" && Boolean(msg.thinking);
          const emptyAssistant = msg.role === "assistant" && !msg.text && !msg.thinking;
          if (emptyAssistant && !(busy && last)) return null;
          const shown = (msg.thinking || "").slice(-THINK_DISPLAY_CAP);
          return (
            <div key={i} className={`bubble-row ${msg.role}`}>
              <div className={`avatar ${msg.role === "user" ? "user" : "bot"}`}>
                {msg.role === "user" ? "U" : "A"}
              </div>
              <div className={`bubble ${msg.role === "user" ? "user" : "bot"}`}>
                {msg.meta ? <div className="meta">{msg.meta}</div> : null}
                {showThinking ? (
                  <details className="thinking-box">
                    <summary>Reasoning</summary>
                    <div className="thinking">{shown}</div>
                  </details>
                ) : null}
                {msg.text || (emptyAssistant ? "Working…" : "")}
              </div>
            </div>
          );
        })}
      </div>
      <form className="composer" onSubmit={submit}>
        <textarea
          ref={areaRef}
          rows={1}
          placeholder="Add details or answer the agent…"
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
        <button className="send" type="submit" disabled={busy || !text.trim()}>
          ➤
        </button>
      </form>
    </div>
  );
}
