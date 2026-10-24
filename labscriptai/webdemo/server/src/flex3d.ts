/**
 * Flex 3D view: which protocol the MuJoCo player shows for a chat session.
 *
 * Only the current OT-2 and Flex scripts that pass the checks can be shown.
 * The player selects its scene from `analyze.robotType`, so this module adds
 * the canonical value for the trusted session robot (or rejects a conflicting
 * one) on a copy of the analysis. Unsupported or unfinished sessions are an
 * explicit error; they never fall back to the bundled example. The player does
 * the physics and rendering (sim/web_player.py); this module only decides and
 * forwards.
 */
import { deviceFor } from "./devices.ts";
import { animationAllowed } from "./gate.ts";
import type { SessionState } from "./session.ts";

export const FLEX3D_EXAMPLE_KEY = "example";
const LOAD_TIMEOUT_MS = 30_000;
const INFO_TIMEOUT_MS = 10_000;

interface Flex3dScene {
  id: "ot2" | "flex";
  label: string;
  /** The only scene names the player recognises for this robot. */
  robotType: "OT-2 Standard" | "OT-3 Standard";
}

const SCENES: Record<string, Flex3dScene> = {
  ot2: { id: "ot2", label: "OT-2", robotType: "OT-2 Standard" },
  flex: { id: "flex", label: "Flex", robotType: "OT-3 Standard" },
};

/** Conservative lookup: only the canonical scene names, ignoring case/whitespace. */
const SCENE_BY_ROBOT_TYPE: Record<string, Flex3dScene> = {
  "ot-2 standard": SCENES.ot2,
  "ot-3 standard": SCENES.flex,
};

type BlockerCode = "unsupported" | "not_ready";

interface Flex3dBlocker {
  code: BlockerCode;
  message: string;
}

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
  /** "session": the chat script. "example" remains for the standalone example helper. */
  source: "session" | "example";
  /** Key the page uses for /flex3d/<key>/... (the analysis hash, or "example"). */
  key: string;
  note: string;
  /** The player's info: title, duration, steps, camera defaults and limits. */
  info: Record<string, unknown>;
}

function sceneForSession(
  session: Pick<SessionState, "robot" | "analyze" | "lastChecks">
): Flex3dScene | undefined {
  const deviceId = deviceFor(session.robot)?.id;
  return deviceId === "ot2" || deviceId === "flex" ? SCENES[deviceId] : undefined;
}

function blockerForSession(
  session: Pick<SessionState, "robot" | "analyze" | "lastChecks">
): Flex3dBlocker | null {
  const scene = sceneForSession(session);
  if (!scene) {
    return {
      code: "unsupported",
      message: "这个会话的机器人不支持三维预演（仅支持 OT-2 和 Flex）",
    };
  }
  const commands = session.analyze?.commands;
  if (!Array.isArray(commands) || commands.length === 0) {
    return { code: "not_ready", message: "还没有可以播放的分析结果" };
  }
  const checks = session.lastChecks;
  if (!checks || checks.status !== "pass" || !animationAllowed(checks, commands.length)) {
    return { code: "not_ready", message: "还没有通过检查的脚本" };
  }
  return null;
}

/** Why the session's own script cannot be shown in 3D, or null when it can. */
export function flex3dBlocker(
  session: Pick<SessionState, "robot" | "analyze" | "lastChecks">
): string | null {
  return blockerForSession(session)?.message ?? null;
}

export function flex3dPlayerBase(): string {
  return (process.env.FLEX3D_URL || "http://127.0.0.1:8791").replace(/\/+$/, "");
}

async function playerRequest(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  try {
    return await fetch(url, { ...init, signal: AbortSignal.timeout(timeoutMs) });
  } catch {
    throw new Flex3dError(
      503,
      "player_unavailable",
      "三维预演服务暂时不可用，请稍后重试。"
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

/**
 * Copy the analysis and put it in the scene named by the trusted session robot.
 * A conflicting or unrecognised explicit `robotType` is rejected instead of
 * being overwritten (which could silently show the wrong scene). The original
 * `session.analyze` object is never mutated.
 */
function analysisForScene(
  analyze: Record<string, unknown>,
  scene: Flex3dScene
): Record<string, unknown> {
  const declared = analyze.robotType;
  if (declared !== undefined) {
    if (typeof declared !== "string" || !declared.trim()) {
      throw new Flex3dError(
        422,
        "robot_type_mismatch",
        `分析结果的 robotType 不是已知的 OT-2/Flex 场景，无法确认三维场景。`
      );
    }
    const declaredScene = SCENE_BY_ROBOT_TYPE[declared.trim().toLowerCase()];
    if (!declaredScene) {
      throw new Flex3dError(
        422,
        "robot_type_mismatch",
        `分析结果的 robotType（${declared}）不是已知的 OT-2/Flex 场景，无法确认三维场景。`
      );
    }
    if (declaredScene.id !== scene.id) {
      throw new Flex3dError(
        422,
        "robot_type_mismatch",
        `分析结果的 robotType（${declared}）与会话机器人（${scene.label}）不一致，未转发到三维预演。`
      );
    }
  }
  return { ...analyze, robotType: scene.robotType };
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

/** The view for an accepted current session. Unsupported or unfinished sessions throw a 422. */
export async function flex3dForSession(session: SessionState): Promise<Flex3dView> {
  const blocker = blockerForSession(session);
  if (blocker) throw new Flex3dError(422, blocker.code, blocker.message);

  const scene = sceneForSession(session);
  if (!scene) throw new Flex3dError(422, "unsupported", "这个会话不支持三维预演");
  const analyze = analysisForScene(session.analyze as Record<string, unknown>, scene);
  const info = await loadSessionScript(analyze);
  return { source: "session", key: String(info.key), note: "", info };
}
