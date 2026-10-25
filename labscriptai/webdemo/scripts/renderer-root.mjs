import { existsSync } from "node:fs";
import path from "node:path";

/**
 * Return the renderer roots in precedence order.
 *
 * The explicit environment override intentionally returns only that path: a
 * caller who names a renderer should get a clear failed-start message rather
 * than silently running a different checkout.
 */
export function rendererCandidates({ root, repoRoot, env = process.env }) {
  const override = env.LABSCRIPTAI_PLAYER_ROOT?.trim();
  if (override) return [path.resolve(override)];
  return [
    path.resolve(root, "renderer"),
    path.resolve(repoRoot, "../virtual-lab"),
    path.resolve(repoRoot, "../../virtual-lab"),
  ];
}

export function resolveRendererRoot({ root, repoRoot, env = process.env, exists = existsSync }) {
  const candidates = rendererCandidates({ root, repoRoot, env });
  return candidates.find((candidate) => exists(path.join(candidate, "sim", "web_player.py"))) ?? candidates[0];
}
