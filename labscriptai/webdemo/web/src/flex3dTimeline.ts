/**
 * One timeline for the Flex 3D view. The top half (the MuJoCo views) owns time in
 * seconds. The bottom half (the Opentrons animator) shows a command id and the
 * progress through it. These helpers convert between the two. Setup steps have no
 * animator event; the animator shows the end of the last event before them.
 */

export interface TimelineStep {
  commandId: string | null;
  kind: string;
  t0: number;
  t1: number;
}

export interface AnimatorSpot {
  commandId: string | null;
  fraction: number;
}

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

/** Index of the step on screen at `t`: the last step that has started, as the player picks it. */
export function stepIndexAt(steps: readonly TimelineStep[], t: number): number {
  let current = -1;
  steps.forEach((step, index) => {
    if (step.kind !== "loadLiquid" && step.t0 <= t + 1e-9) current = index;
  });
  return current;
}

export function spotForTime(steps: readonly TimelineStep[], t: number): AnimatorSpot {
  const index = stepIndexAt(steps, t);
  if (index < 0) return { commandId: null, fraction: 0 };
  const step = steps[index];
  const span = step.t1 - step.t0;
  const fraction = span > 1e-9 ? clamp01((t - step.t0) / span) : 1;
  return { commandId: step.commandId, fraction };
}

export function timeForSpot(
  steps: readonly TimelineStep[],
  commandId: string | null,
  fraction: number
): number {
  if (commandId == null) return 0;
  const step = steps.find((candidate) => candidate.commandId === commandId);
  if (step == null) return 0;
  return step.t0 + clamp01(fraction) * Math.max(0, step.t1 - step.t0);
}
