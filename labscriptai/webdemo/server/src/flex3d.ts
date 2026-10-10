/**
 * Flex 3D view: which protocol the MuJoCo player shows for a chat session.
 *
 * The chat session's own script is shown when it is a Flex script that passes
 * the checks. Otherwise the serial dilution example is shown and the reason is
 * returned as a note, so the page never shows the example for a passing script
 * by accident. The player does the physics and rendering (sim/web_player.py);
 * this module only decides and forwards.
 */
import { deviceFor } from "./devices.ts";
import { animationAllowed } from "./gate.ts";
import type { SessionState } from "./session.ts";

export const FLEX3D_EXAMPLE_KEY = "example";
const LOAD_TIMEOUT_MS = 30_000;
const INFO_TIMEOUT_MS = 10_000;

export class Flex3dError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string
  ) {
    super(message);
  }
}

export interface Flex3dView {
  /** "session": the chat script. "example": the bundled serial dilution, with `note` saying why. */
  source: "session" | "example";
  /** Key the page uses for /flex3d/<key>/... (the analysis hash, or "example"). */
  key: string;
  note: string;
  /** The player's info: title, duration, steps, camera defaults and limits. */
  info: Record<string, unknown>;
}

/** Why the session's own script cannot be shown in 3D, or null when it can. */
export function flex3dBlocker(
  session: Pick<SessionState, "robot" | "analyze" | "lastChecks">
): string | null {
  if (deviceFor(session.robot)?.id !== "flex") return "这个会话不是 Flex 脚本";
  const commands = session.analyze?.commands;
  if (!Array.isArray(commands) || commands.length === 0) return "还没有可以播放的分析结果";
  const checks = session.lastChecks;
  if (!checks || checks.status !== "pass" || !animationAllowed(checks, commands.length)) {
    return "还没有通过检查的脚本";
  }
  return null;
}

export function flex3dPlayerBase(): string {
  return (process.env.FLEX3D_URL || "http://127.0.0.1:8791").replace(/\/+$/, "");
}

async function playerRequest(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  try {
    return await fetch(url, { ...init, signal: AbortSignal.timeout(timeoutMs) });
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    throw new Flex3dError(
      503,
      "player_unavailable",
      `3D 播放器没有响应（${reason}）。请在 webdemo 目录用 npm run dev 启动它。`
    );
  }
}

async function playerJson(response: Response): Promise<Record<string, unknown>> {
  const body = (await response.json().catch(() => ({}))) as Record<string, unknown>;
  if (response.ok) return body;
  const message = typeof body.message === "string" ? body.message : `播放器返回 ${response.status}`;
  if (response.status === 422) throw new Flex3dError(422, "unsupported", message);
  if (response.status === 400) throw new Flex3dError(400, "bad_analysis", message);
  throw new Flex3dError(502, "player_failed", message);
}

/** Load the session's analysis into the player. The player keys it by hash, so a repeat call is cheap. */
export async function loadSessionScript(analyze: Record<string, unknown>): Promise<Record<string, unknown>> {
  const response = await playerRequest(
    `${flex3dPlayerBase()}/flex3d/load`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(analyze),
    },
    LOAD_TIMEOUT_MS
  );
  return playerJson(response);
}

export async function loadExampleScript(): Promise<Record<string, unknown>> {
  const response = await playerRequest(
    `${flex3dPlayerBase()}/flex3d/${FLEX3D_EXAMPLE_KEY}/info`,
    { method: "GET" },
    INFO_TIMEOUT_MS
  );
  return playerJson(response);
}

/** The view for a session: its own passing script, or the example with the reason. */
export async function flex3dForSession(session: SessionState): Promise<Flex3dView> {
  const blocker = flex3dBlocker(session);
  if (blocker === null) {
    const info = await loadSessionScript(session.analyze as Record<string, unknown>);
    return { source: "session", key: String(info.key), note: "", info };
  }
  const info = await loadExampleScript();
  return {
    source: "example",
    key: FLEX3D_EXAMPLE_KEY,
    note: `${blocker}，先显示串行稀释示例。`,
    info,
  };
}
