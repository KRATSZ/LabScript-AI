import fs from "fs";

export function inferSlotFromProtocolPath(protocolPath) {
  const text = protocolPath && fs.existsSync(protocolPath) ? fs.readFileSync(protocolPath, "utf8") : "";
  const match = text.match(/protocol\.load_labware\([^,\n]+,\s*["']([A-D][1-4])["']/i);
  return match ? match[1].toUpperCase() : null;
}

export function inferLabwareFromProtocolPath(protocolPath) {
  const text = protocolPath && fs.existsSync(protocolPath) ? fs.readFileSync(protocolPath, "utf8") : "";
  const match = text.match(/protocol\.load_labware\(["']([^"']+)["'],\s*["'][A-D][1-4]["']/i);
  return match ? match[1] : null;
}

export function resolveProbeContext({
  probe_results: probeResults = [],
  probe_artifact_path: probeArtifactPath = null,
  probe_artifact: probeArtifact = null,
  generated_protocol_path: generatedProtocolPath = null,
  slot_name: slotName = null,
  labware_load_name: labwareLoadName = null,
  labware_slot: labwareSlot = null,
  run_id: runId = null,
  mode = null,
} = {}) {
  let artifact = probeArtifact;
  if (!artifact && probeArtifactPath) {
    artifact = JSON.parse(fs.readFileSync(probeArtifactPath, "utf8"));
  }

  const resolvedProbeResults = probeResults.length
    ? probeResults
    : Array.isArray(artifact?.probe_results)
      ? artifact.probe_results
      : [];

  if (resolvedProbeResults.length === 0) {
    throw new Error("apply_liquid_probe_results requires probe_results or a probe artifact containing probe_results.");
  }

  const protocolPath = generatedProtocolPath || artifact?.generated_protocol_path || null;
  const resolvedSlotName = String(
    slotName || labwareSlot || inferSlotFromProtocolPath(protocolPath) || "",
  ).toUpperCase();
  if (!resolvedSlotName) {
    throw new Error(
      "slot_name (or labware_slot) is required when it cannot be inferred from generated_protocol_path.",
    );
  }

  const resolvedLabwareLoadName =
    labwareLoadName || inferLabwareFromProtocolPath(protocolPath) || null;
  const resolvedRunId = runId || artifact?.run_id || artifact?.run_protocol?.runId || null;
  const resolvedMode = mode || artifact?.mode || resolvedProbeResults[0]?.mode || "detect_presence";

  return {
    probeResults: resolvedProbeResults,
    slotName: resolvedSlotName,
    labwareLoadName: resolvedLabwareLoadName,
    runId: resolvedRunId,
    mode: resolvedMode,
    generatedProtocolPath: protocolPath,
    probeArtifactPath: probeArtifactPath || null,
  };
}

export function probeResultToSourceUpdate(result, { slotName, labwareLoadName, runId, mode, observedAt } = {}) {
  const probeMode = result.mode || mode || "detect_presence";
  const success = result.success !== false;
  const rawValue = result.value;

  let observedPresence = null;
  let observedHeightMm = null;

  if (probeMode === "measure_height") {
    const height = Number(rawValue);
    observedHeightMm = Number.isFinite(height) ? height : null;
    observedPresence = success && observedHeightMm !== null ? true : success ? false : null;
  } else if (probeMode === "require_presence") {
    observedPresence = success && rawValue === true;
  } else {
    observedPresence = rawValue === true;
  }

  const notes =
    probeMode === "measure_height"
      ? observedHeightMm !== null
        ? `Live probe ${runId || "unknown-run"} measured liquid height ${observedHeightMm} mm.`
        : `Live probe ${runId || "unknown-run"} did not return a measurable liquid height.`
      : observedPresence
        ? `Live probe ${runId || "unknown-run"} observed liquid present.`
        : `Live probe ${runId || "unknown-run"} observed no liquid.`;

  return {
    slot_name: slotName,
    well_name: result.well,
    labware_load_name: labwareLoadName,
    observed_presence: observedPresence,
    observed_height_mm: observedHeightMm,
    observed_probe_mode: probeMode,
    observed_at: observedAt,
    observed_run_id: runId,
    observed_source: "live_probe",
    notes,
  };
}

export function buildSourcesFromProbeResults(probeResults, options = {}) {
  const observedAt = options.observed_at || new Date().toISOString();
  return probeResults.map(result =>
    probeResultToSourceUpdate(result, {
      ...options,
      mode: result.mode || options.mode,
      observedAt,
    }),
  );
}

export async function applyLiquidProbeResults(args, { writeObservedProbeResults, summarizeLiquidSourceMap } = {}) {
  if (typeof writeObservedProbeResults !== "function") {
    throw new Error("applyLiquidProbeResults requires writeObservedProbeResults.");
  }
  if (typeof summarizeLiquidSourceMap !== "function") {
    throw new Error("applyLiquidProbeResults requires summarizeLiquidSourceMap.");
  }

  const sessionId = args.session_id || args.sessionId || "default";
  const context = resolveProbeContext(args);
  const sources = buildSourcesFromProbeResults(context.probeResults, {
    slotName: context.slotName,
    labwareLoadName: context.labwareLoadName,
    runId: context.runId,
    mode: context.mode,
  });

  const writebackResult = await writeObservedProbeResults({
    sessionId,
    context,
    sources,
  });
  const summaryResult = await summarizeLiquidSourceMap({
    session_id: sessionId,
  });

  return {
    data: {
      status: "completed",
      session_id: sessionId,
      probe_artifact_path: context.probeArtifactPath,
      run_id: context.runId,
      slot_name: context.slotName,
      labware_load_name: context.labwareLoadName,
      probe_mode: context.mode,
      applied_count: writebackResult.applied_count,
      applied_sources: writebackResult.applied_sources || sources,
      blocked_sources: writebackResult.blocked_sources || [],
      record_result: writebackResult,
      source_map_summary: summaryResult.data,
    },
    stateRevision: summaryResult.stateRevision,
    sessionId: summaryResult.sessionId,
  };
}
