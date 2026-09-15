export interface SseWriter {
  write(event: string, data: unknown): void;
  close(): void;
}

export type TrackedSse = SseWriter & { hasUserText: () => boolean };

function textToken(data: unknown): string {
  if (!data || typeof data !== "object" || !("token" in data)) return "";
  const token = (data as { token?: unknown }).token;
  return typeof token === "string" ? token : "";
}

/** Same SSE stream, plus whether any non-empty chat text already went out this turn. */
export function trackUserText(sse: SseWriter): TrackedSse {
  let sent = false;
  return {
    write(event, data) {
      if (event === "text" && textToken(data).trim()) sent = true;
      sse.write(event, data);
    },
    close() {
      sse.close();
    },
    hasUserText() {
      return sent;
    },
  };
}

export function sseHasUserText(sse: SseWriter): boolean {
  return typeof (sse as TrackedSse).hasUserText === "function" && (sse as TrackedSse).hasUserText();
}

export function createSseWriter(res: {
  writeHead: (code: number, headers: Record<string, string>) => void;
  write: (chunk: string) => boolean;
  end: () => void;
}): SseWriter {
  res.writeHead(200, {
    "Content-Type": "text/event-stream; charset=utf-8",
    "Cache-Control": "no-cache, no-transform",
    Connection: "keep-alive",
    "X-Accel-Buffering": "no",
  });
  return {
    write(event, data) {
      res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
    },
    close() {
      res.end();
    },
  };
}

export function parseSseBuffer(
  buffer: string,
  onFrame: (payload: Record<string, unknown>) => void
): string {
  const frames = buffer.split("\n\n");
  const rest = frames.pop() ?? "";
  for (const frame of frames) {
    for (const line of frame.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      const raw = trimmed.slice(trimmed.indexOf(":") + 1).trim();
      if (!raw) continue;
      try {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object") {
          onFrame(parsed as Record<string, unknown>);
        }
      } catch {
        // ignore partial JSON
      }
    }
  }
  return rest;
}
