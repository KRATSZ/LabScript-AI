export function isPlayableAnalyze(analyze: Record<string, unknown> | null): boolean {
  return Boolean(analyze && Array.isArray(analyze.commands) && analyze.commands.length > 0);
}

function firstCommandCreatedAt(analyze: Record<string, unknown>): string | undefined {
  const cmds = analyze.commands;
  if (!Array.isArray(cmds) || !cmds[0] || typeof cmds[0] !== "object") return undefined;
  const created = (cmds[0] as Record<string, unknown>).createdAt;
  return typeof created === "string" && created.trim() ? created : undefined;
}

function looksLikeFlex(analyze: Record<string, unknown>, robotHint?: string | null): boolean {
  const hint = `${analyze.robotType ?? ""} ${analyze.robot_type ?? ""} ${analyze.robot ?? ""} ${robotHint ?? ""}`;
  return /flex|ot-?3/i.test(hint);
}

function isTiprackRecord(rec: Record<string, unknown>): boolean {
  if (rec.isTiprack === true || rec.is_tiprack === true) return true;
  const load = `${rec.loadName ?? ""} ${rec.definitionUri ?? ""} ${rec.displayName ?? ""}`;
  return /tiprack/i.test(load);
}

function tiprackIds(analyze: Record<string, unknown>): Set<string> {
  const ids = new Set<string>();
  const list = Array.isArray(analyze.labware) ? analyze.labware : [];
  for (const item of list) {
    if (!item || typeof item !== "object") continue;
    const rec = item as Record<string, unknown>;
    if (isTiprackRecord(rec) && rec.id != null) ids.add(String(rec.id));
  }
  return ids;
}

function rewriteTrashDropTips(analyze: Record<string, unknown>): unknown[] {
  const racks = tiprackIds(analyze);
  const commands = Array.isArray(analyze.commands) ? analyze.commands : [];
  return commands.map((cmd) => {
    if (!cmd || typeof cmd !== "object") return cmd;
    const rec = cmd as Record<string, unknown>;
    if (rec.commandType !== "dropTip") return cmd;
    const params =
      rec.params && typeof rec.params === "object"
        ? (rec.params as Record<string, unknown>)
        : {};
    const labwareId = params.labwareId == null ? "" : String(params.labwareId);
    if (labwareId && racks.has(labwareId)) return cmd;
    return {
      ...rec,
      commandType: "dropTipInPlace",
      params: { pipetteId: params.pipetteId },
    };
  });
}

export function padAnalysisForAnimator(
  analyze: Record<string, unknown>,
  robotHint?: string | null
): Record<string, unknown> {
  const robotType =
    typeof analyze.robotType === "string" && analyze.robotType.trim()
      ? analyze.robotType
      : looksLikeFlex(analyze, robotHint)
        ? "OT-3 Standard"
        : "OT-2 Standard";
  const createdAt =
    typeof analyze.createdAt === "string" && analyze.createdAt.trim()
      ? analyze.createdAt
      : firstCommandCreatedAt(analyze) ?? new Date().toISOString();
  const rawConfig = analyze.config;
  const config =
    rawConfig &&
    typeof rawConfig === "object" &&
    typeof (rawConfig as { protocolType?: unknown }).protocolType === "string"
      ? rawConfig
      : { protocolType: "python", apiVersion: [2, 15] };
  return { ...analyze, createdAt, robotType, config, commands: rewriteTrashDropTips(analyze) };
}

export function safeNormalizeAnalysis<T>(
  analyze: Record<string, unknown> | null,
  normalize: (input: Record<string, unknown>) => T,
  robotHint?: string | null
): T | null {
  if (!isPlayableAnalyze(analyze) || !analyze) return null;
  try {
    return normalize(padAnalysisForAnimator(analyze, robotHint));
  } catch {
    return null;
  }
}

export function analysisResetKey(analyze: Record<string, unknown> | null): string {
  if (!analyze) return "none";
  const created = analyze.createdAt == null ? "" : String(analyze.createdAt);
  const n = Array.isArray(analyze.commands) ? analyze.commands.length : 0;
  return `${created}:${n}`;
}
