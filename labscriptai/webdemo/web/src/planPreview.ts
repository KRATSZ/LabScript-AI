import type { RobotModel, SessionSnapshot } from "./types";

export const PLAN_PREVIEW_GAP =
  "The bench preview needs a confirmed deck or plan labware. The step list stays available if one exists.";

function hasFilledDeck(deck: Record<string, string> | undefined): boolean {
  return Object.values(deck ?? {}).some((value) => value.trim());
}

function planResources(plan: Record<string, unknown> | null | undefined): Record<string, unknown>[] {
  return Array.isArray(plan?.resources)
    ? plan.resources.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === "object"))
    : [];
}

/** Deck map from plan resources when the session hardware deck is empty. */
export function deckFromPlan(plan: Record<string, unknown> | null | undefined): Record<string, string> {
  const out: Record<string, string> = {};
  for (const rec of planResources(plan)) {
    const slot = rec.slot != null ? String(rec.slot).trim() : "";
    if (!slot) continue;
    const id = String(rec.id ?? rec.name ?? "").trim();
    const type = String(rec.type ?? "").trim();
    const name = id || type;
    if (!name) continue;
    out[slot] = name;
  }
  return out;
}

export function planPreviewGap(
  plan: Record<string, unknown> | null | undefined,
  deck?: Record<string, string>
): string | null {
  if (hasFilledDeck(deck) || planResources(plan).length) return null;
  return PLAN_PREVIEW_GAP;
}

export function sessionForPlanSketch(
  session: SessionSnapshot | null | undefined,
  plan: Record<string, unknown> | null,
  robot?: string | null
): SessionSnapshot | null {
  const fromSession = session?.hardware?.deck ?? {};
  const deck = hasFilledDeck(fromSession) ? fromSession : deckFromPlan(plan ?? session?.plan);
  if (!session && !Object.keys(deck).length) return null;
  if (session) {
    return { ...session, hardware: { ...session.hardware, deck } };
  }
  return {
    id: "plan-preview",
    phase: "ready",
    missing: [],
    goal: "",
    doc: "",
    robot: (robot as RobotModel) || null,
    hardware: { deck },
    hardware_config: "",
    sop: "",
    code: "",
    plan: plan ?? null,
    analyze: null,
    checks: null,
    fab: { lit: false },
  };
}
