export const CHAT_DEFAULT = 0.38;
export const CHAT_MIN = 0.28;
export const CHAT_MAX = 0.46;
export const CHAT_MIN_PX = 280;
export const SEAM_PX = 6;
export const HISTORY_COLLAPSED_PX = 32;
export const HISTORY_OPEN_PX = 220;
export const CHAT_PCT_KEY = "labscriptai.chatPct";

/** Chat share of the workspace. History steals Stage, not this. */
export function clampChatPct(pct: number, workspacePx: number): number {
  if (!Number.isFinite(pct) || workspacePx <= 0) return CHAT_DEFAULT;
  const min = Math.max(CHAT_MIN, CHAT_MIN_PX / workspacePx);
  if (min > CHAT_MAX) return CHAT_MAX;
  return Math.min(CHAT_MAX, Math.max(min, pct));
}

export function loadChatPct(workspacePx = 1280): number {
  try {
    const raw = localStorage.getItem(CHAT_PCT_KEY);
    if (raw == null) return clampChatPct(CHAT_DEFAULT, workspacePx);
    return clampChatPct(Number(raw), workspacePx);
  } catch {
    return CHAT_DEFAULT;
  }
}

export function saveChatPct(pct: number): void {
  try {
    localStorage.setItem(CHAT_PCT_KEY, String(pct));
  } catch {
    /* ignore quota / private mode */
  }
}

export function historyWidthPx(open: boolean, hasRail: boolean): number {
  if (!hasRail) return 0;
  return open ? HISTORY_OPEN_PX : HISTORY_COLLAPSED_PX;
}
