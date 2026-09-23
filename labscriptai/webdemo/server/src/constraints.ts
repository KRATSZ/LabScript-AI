/** Intake facts the generator must obey: reservoir opt-out and confirmed on-hand volume. */

export interface SourceFill {
  well: string;
  ul: number;
}

const RESERVOIR_WORD = /reservoir|trough|储液槽|储液/gi;
const NEAR_DENY =
  /不用|勿用|不要|没有|去掉|取消|without|\bno\b|\bnot\b|don'?t|do not|\bremove\b|\bmissing\b|isn'?t/i;

const FILL_WELL_THEN =
  /([A-H])\s*(\d{1,2}).{0,20}?(?:只有|仅有|only(?:\s+has)?|has\s+only)\s*(\d+(?:\.\d+)?)\s*(?:µl|ul|μl)/i;
const FILL_AMOUNT_THEN =
  /(?:只有|仅有|only(?:\s+has)?|has\s+only)\s*(\d+(?:\.\d+)?)\s*(?:µl|ul|μl).{0,20}?([A-H])\s*(\d{1,2})/i;

export function textRejectsReservoir(text: string): boolean {
  if (!text) return false;
  for (const match of text.matchAll(RESERVOIR_WORD)) {
    const index = match.index ?? 0;
    const window = text.slice(Math.max(0, index - 24), Math.min(text.length, index + match[0].length + 12));
    if (NEAR_DENY.test(window)) return true;
  }
  return false;
}

export function isReservoirName(name: string): boolean {
  return /reservoir|trough|储液/i.test(name);
}

export function parseSourceFill(text: string): SourceFill | null {
  if (!text) return null;
  const wellFirst = text.match(FILL_WELL_THEN);
  if (wellFirst) {
    return { well: `${wellFirst[1].toUpperCase()}${wellFirst[2]}`, ul: Number(wellFirst[3]) };
  }
  const amountFirst = text.match(FILL_AMOUNT_THEN);
  if (amountFirst) {
    return { well: `${amountFirst[2].toUpperCase()}${amountFirst[3]}`, ul: Number(amountFirst[1]) };
  }
  return null;
}

/** First transfer-like µL in the goal. Tip-capacity numbers are not read here. */
export function transferUl(goal: string): number | undefined {
  const hit = goal.match(/(\d+(?:\.\d+)?)\s*(?:µl|ul|μl)/i);
  if (!hit) return undefined;
  const ul = Number(hit[1]);
  return Number.isFinite(ul) ? ul : undefined;
}

export function fillGap(
  goal: string,
  fill: SourceFill | undefined
): { transfer: number; fill: SourceFill } | null {
  if (!fill) return null;
  const transfer = transferUl(goal);
  if (transfer == null || transfer <= fill.ul) return null;
  return { transfer, fill };
}

export function fillShortfallLine(goal: string, fill: SourceFill | undefined, language: "en" | "zh" = "en"): string | null {
  const gap = fillGap(goal, fill);
  if (!gap) return null;
  if (language === "zh") {
    return `你确认 ${gap.fill.well} 只有 ${gap.fill.ul} µL，这次要吸 ${gap.transfer} µL。`;
  }
  return `You confirmed ${gap.fill.well} holds only ${gap.fill.ul} µL, but this transfer aspirates ${gap.transfer} µL.`;
}

export function confirmedFillLine(fill: SourceFill | undefined, language: "en" | "zh" = "en"): string | null {
  if (!fill) return null;
  if (language === "zh") return `按你确认的 ${fill.well} = ${fill.ul} µL 检查`;
  return `Checked using the ${fill.ul} µL you confirmed in ${fill.well}`;
}

export function reservoirRuledOutLine(language: "en" | "zh" = "en"): string {
  return language === "zh"
    ? "方案仍列出你已去掉的储液槽。"
    : "The draft still lists the reservoir you ruled out.";
}

export function fillMismatchLine(fill: SourceFill, language: "en" | "zh" = "en"): string {
  return language === "zh"
    ? `校验没有使用你确认的 ${fill.well} = ${fill.ul} µL。`
    : `Checks did not use the ${fill.ul} µL you confirmed in ${fill.well}.`;
}

function stepSources(step: unknown): string[] {
  if (!step || typeof step !== "object") return [];
  const rec = step as { source?: unknown; destination?: unknown; location?: unknown };
  const out: string[] = [];
  for (const value of [rec.source, rec.destination, rec.location]) {
    if (typeof value === "string") out.push(value);
    else if (Array.isArray(value)) {
      for (const item of value) if (typeof item === "string") out.push(item);
    }
  }
  return out;
}

export function draftMentionsReservoir(sop: string, plan: unknown): boolean {
  if (isReservoirName(sop)) return true;
  if (!plan || typeof plan !== "object") return false;
  const rec = plan as { resources?: unknown; steps?: unknown };
  const resources = Array.isArray(rec.resources) ? rec.resources : [];
  for (const item of resources) {
    if (!item || typeof item !== "object") continue;
    const row = item as { type?: unknown; id?: unknown; name?: unknown };
    if (isReservoirName(`${row.type ?? ""} ${row.id ?? ""} ${row.name ?? ""}`)) return true;
  }
  const steps = Array.isArray(rec.steps) ? rec.steps : [];
  for (const step of steps) {
    if (stepSources(step).some((part) => isReservoirName(part))) return true;
  }
  return false;
}

/** Write the confirmed on-hand volume onto every initial volume for that well. */
export function stampConfirmedFill(
  plan: Record<string, unknown>,
  fill: SourceFill
): { plan: Record<string, unknown>; applied: boolean } {
  const well = fill.well.toUpperCase();
  const vols: Record<string, unknown> =
    plan.initial_volumes_ul && typeof plan.initial_volumes_ul === "object"
      ? { ...(plan.initial_volumes_ul as Record<string, unknown>) }
      : {};
  const keys = new Set(Object.keys(vols).filter((key) => key.toUpperCase().endsWith(`:${well}`)));
  const steps = Array.isArray(plan.steps) ? plan.steps : [];
  for (const step of steps) {
    for (const source of stepSources(step)) {
      if (source.toUpperCase().endsWith(`:${well}`)) keys.add(source);
    }
  }
  if (!keys.size) return { plan, applied: false };
  for (const key of keys) vols[key] = fill.ul;
  return { plan: { ...plan, initial_volumes_ul: vols }, applied: true };
}

export function planMatchesFill(plan: unknown, fill: SourceFill): boolean {
  if (!plan || typeof plan !== "object") return false;
  const vols = (plan as { initial_volumes_ul?: unknown }).initial_volumes_ul;
  if (!vols || typeof vols !== "object") return false;
  const well = fill.well.toUpperCase();
  const hits = Object.entries(vols as Record<string, unknown>).filter(([key]) =>
    key.toUpperCase().endsWith(`:${well}`)
  );
  if (!hits.length) return false;
  return hits.every(([, value]) => Number(value) === fill.ul);
}
