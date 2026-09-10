const HEARTBEAT = /^model is reasoning\.\.\.$/i;

/** Prefer real `token`; drop 8010 heartbeat-only `message` frames. */
export function codeThinkingToken(data: Record<string, unknown>): string {
  const token = typeof data.token === "string" ? data.token : "";
  if (token.trim()) return token;
  const message = typeof data.message === "string" ? data.message.trim() : "";
  if (!message || HEARTBEAT.test(message)) return "";
  return message;
}
