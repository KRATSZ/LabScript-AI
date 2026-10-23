/** Explicit user facts, kept outside model-written goals and plans.
 * This is a deliberately bounded parser, not a general SOP interpreter. Full
 * source text still goes to semantic review. Unknown wording is not inferred.
 */
export interface InitialVolume { location: string; ul: number }
export interface UserRequirements {
  initial: InitialVolume[];
  transferUl?: number;
  destination?: string;
  wellCapacityUl?: number;
  noSplit?: boolean;
  noMix?: boolean;
}

const AMOUNT = String.raw`(\d+(?:\.\d+)?)\s*(µl|μl|ul|ml|微升|毫升)`;
const LOC = String.raw`((?:[A-D][1-4]|\d{1,2})\s*\/\s*[A-P]\d{1,2}|\b[A-P]\d{1,2}\b)`;
const ul = (n: string, unit: string) => Number(n) * (/ml|毫升/i.test(unit) ? 1000 : 1);

export function readUserRequirements(text: string, previous?: UserRequirements): UserRequirements {
  const out: UserRequirements = { ...previous, initial: [...(previous?.initial ?? [])] };
  const transfer = text.match(new RegExp(String.raw`(?:transfer|转移)\s*${AMOUNT}`, "i"))
    ?? text.match(new RegExp(String.raw`(?:change|reduce|改|调整|降低|减少)[^\n。;；]{0,45}?(?:to|为|成|到)\s*(?:每孔\s*)?${AMOUNT}`, "i"));
  // A total/per-sample mixture is not a single transfer.
  const singleAmendment = previous?.transferUl != null && previous.destination && /change|reduce|改|调整|降低|减少/i.test(text);
  if (transfer && (singleAmendment || !/\beach\b|每(?:孔|个|份)|\bsamples?\b|样本|[A-H]\d\s*[–-]\s*[A-H]\d/i.test(text))) {
    out.transferUl = ul(transfer[1], transfer[2]);
  }
  const dest = text.match(new RegExp(String.raw`(?:\bto\b|转移到|打至|转移至|到)\s*(?:empty\s+)?(?:plate\s+)?(?:well\s+)?${LOC}`, "i"));
  if (dest) out.destination = dest[1].replace(/\s/g, "").toUpperCase();
  const capacity = text.match(new RegExp(String.raw`${AMOUNT}\s*(?:\d+\s*[- ]?well\s*)?(?:plate|孔板|孔)`, "i"))
    ?? text.match(new RegExp(String.raw`(?:well\s+capacity|孔容量|孔的容量)\s*(?:is|为|[:：])?\s*${AMOUNT}`, "i"));
  if (capacity) out.wellCapacityUl = ul(capacity[1], capacity[2]);
  if (/do not split|no split|禁止拆分|不(?:要|允许)?拆分/i.test(text)) out.noSplit = true;
  else if (/allow splitting|may split|允许拆分|可以拆分/i.test(text)) out.noSplit = false;
  if (/no mix(?:ing)?|do not mix|不混匀|不要混匀/i.test(text)) out.noMix = true;
  else if (/\bmix\s+\d|混匀\s*\d/i.test(text)) out.noMix = false;

  // Reagent inventory rows and explicit "initially contains" phrases only.
  // Exclude transfer/mix/final-volume statements, even when they name a well.
  for (const line of text.split(/\n/)) {
    const inventory = /reagents?\s*[:：]|试剂\s*[:：]|初始|initial|start(?:ing|s)?\s+(?:with|volume)|contains/i.test(line);
    if (!inventory) continue;
    for (const clause of line.split(/[;；]/)) {
      const match = clause.match(new RegExp(String.raw`${LOC}[^\n;；]{0,65}?${AMOUNT}`, "i"));
      if (!match || /转移|aspirat|dispens|transfer|余约|remaining|final|\/\s*(?:孔|well|sample)|per\s+(?:well|sample)/i.test(clause)) continue;
      const fact = { location: match[1].replace(/\s/g, "").toUpperCase(), ul: ul(match[2], match[3]) };
      out.initial = [...out.initial.filter(f => f.location !== fact.location), fact];
    }
  }
  return out;
}

export function requirementsText(facts?: UserRequirements, zh = false): string {
  if (!facts) return "";
  const lines = facts.initial.map(f => `${f.location}: ${f.ul} µL ${zh ? "初始量" : "initial volume"}`);
  if (facts.wellCapacityUl != null) lines.push(`${zh ? "用户指定孔容量" : "User-specified well capacity"}: ${facts.wellCapacityUl} µL`);
  if (facts.noSplit) lines.push(zh ? "不得拆分转移" : "Do not split the transfer");
  if (facts.noMix) lines.push(zh ? "不混匀" : "No mixing");
  return lines.length ? `${zh ? "用户指定的条件" : "User-specified conditions"}:\n${lines.map(s => `- ${s}`).join("\n")}` : "";
}

/** Keep explicit initial conditions visible in the exported SOP and code input. */
export function retainInitialConditions(sop: string, facts?: UserRequirements, zh = false): string {
  if (!facts?.initial.length) return sop;
  return `${sop.trim()}\n\n${requirementsText({ initial: facts.initial }, zh)}`;
}

export function capacityBlocker(facts?: UserRequirements, zh = false): string | null {
  if (facts?.transferUl == null || facts.wellCapacityUl == null || facts.transferUl <= facts.wellCapacityUl) return null;
  const { transferUl: v, wellCapacityUl: c } = facts;
  return zh
    ? `当前条件无法完成：${v} µL 会超过 ${c} µL 目标孔容量。同一孔分次加液也会溢出。需要你同意减小总量，或改用容量足够的容器并核对匹配的移液器和枪头；仅换大枪头不能解决孔容量不足。条件未改，未生成可执行文件。`
    : `These conditions cannot be completed: ${v} µL exceeds the ${c} µL destination capacity. Splitting into the same well still overflows. With your approval, reduce the total or use a larger destination together with compatible pipettes and tips. A larger tip alone cannot fix well overflow. No executable file was produced.`;
}

type RecordValue = Record<string, any>;
export function planRequirementIssues(plan: RecordValue, facts?: UserRequirements): string[] {
  if (!facts) return [];
  const issues: string[] = [];
  const resources: RecordValue[] = Array.isArray(plan.resources) ? plan.resources : [];
  const isPlate = (r: RecordValue) => /plate/i.test(String(r.type)) && !/tip|reservoir/i.test(String(r.type));
  const resolve = (location: string): string | undefined => {
    const parts = location.split("/");
    const matches = parts.length === 2 ? resources.filter(r => String(r.slot).toUpperCase() === parts[0]) : resources.filter(isPlate);
    return matches.length === 1 ? `${matches[0].id}:${parts.at(-1)}` : undefined;
  };
  for (const f of facts.initial) {
    const key = resolve(f.location);
    if (!key || plan.initial_volumes_ul?.[key] !== f.ul) issues.push(`Preserve the user-specified initial volume: ${f.location} = ${f.ul} µL; generated plan has ${key ? plan.initial_volumes_ul?.[key] ?? "no value" : "no unambiguous resource"}.`);
  }
  if (facts.wellCapacityUl != null) {
    for (const r of resources.filter(isPlate)) {
      if (Number(r.max_volume_ul) > facts.wellCapacityUl) issues.push(`Plan declares ${r.id} capacity ${r.max_volume_ul} µL, exceeding the user's ${facts.wellCapacityUl} µL well capacity.`);
    }
  }
  const totals = new Map<string, { ul: number; count: number }>();
  for (const s of (Array.isArray(plan.steps) ? plan.steps : []) as RecordValue[]) {
    if (facts.noMix && s.primitive_type === "MIX") issues.push("The user requested no mixing, but the plan includes MIX.");
    if (s.primitive_type !== "DISPENSE") continue;
    for (const loc of [s.destination ?? s.location].flat()) {
      const key = String(loc);
      const old = totals.get(key) ?? { ul: 0, count: 0 };
      totals.set(key, { ul: old.ul + Number(s.volume_ul), count: old.count + 1 });
    }
  }
  const destination = facts.destination ? resolve(facts.destination) : undefined;
  if (destination && facts.transferUl != null && totals.get(destination)?.ul !== facts.transferUl) issues.push(`Expected ${facts.transferUl} µL delivered to ${destination}; plan delivers ${totals.get(destination)?.ul ?? 0} µL.`);
  for (const [loc, total] of totals) {
    if (facts.noSplit && total.count > 1) issues.push(`The user prohibited splitting; ${loc} receives ${total.count} dispense steps.`);
    if (facts.wellCapacityUl != null && resources.some(r => r.id === loc.split(":")[0] && isPlate(r))) {
      const initial = Number(plan.initial_volumes_ul?.[loc] ?? 0);
      if (initial + total.ul > facts.wellCapacityUl) issues.push(`${loc} receives ${total.ul} µL plus ${initial} µL initial liquid, exceeding user-specified ${facts.wellCapacityUl} µL capacity.`);
    }
  }
  return [...new Set(issues)];
}

/** Reuse destination/total checks against actual analyzed commands, not prose. */
export function analyzeRequirementIssues(analyze: RecordValue, facts?: UserRequirements): string[] {
  if (!facts) return [];
  const resources = (analyze.labware ?? []).map((l: RecordValue) => ({ id: l.id, slot: l.location?.slotName,
    type: /wellplate|plate/.test(l.loadName ?? "") && !/tip|reservoir/.test(l.loadName ?? "") ? "plate" : "other" }));
  const steps = (analyze.commands ?? []).filter((c: RecordValue) => c.commandType === "dispense").map((c: RecordValue) => ({
    primitive_type: "DISPENSE", destination: `${c.params?.labwareId}:${c.params?.wellName}`, volume_ul: c.params?.volume,
  }));
  // Analyze has no independent source-inventory truth; those input conditions
  // stay in the SOP/review. Do not invent an initial ledger and call it tested.
  return planRequirementIssues({ resources, steps }, { ...facts, initial: [] });
}
