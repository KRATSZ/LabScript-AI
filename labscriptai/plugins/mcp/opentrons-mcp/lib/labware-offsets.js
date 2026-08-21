import { requestRobotJson } from "./http.js";

function locationSequenceKey(locationSequence) {
  if (locationSequence === "anyLocation" || locationSequence == null) {
    return "anyLocation";
  }
  return JSON.stringify(locationSequence);
}

export function dedupeLabwareOffsets(offsets) {
  const byKey = new Map();
  for (const offset of offsets || []) {
    const definitionUri = offset?.definitionUri;
    if (!definitionUri) {
      continue;
    }
    const key = `${definitionUri}::${locationSequenceKey(offset.locationSequence)}`;
    const existing = byKey.get(key);
    if (
      !existing ||
      new Date(offset.createdAt || 0).getTime() > new Date(existing.createdAt || 0).getTime()
    ) {
      byKey.set(key, offset);
    }
  }
  return [...byKey.values()];
}

export function selectOffsetsForRun(offsets) {
  return dedupeLabwareOffsets(offsets).filter(offset =>
    Array.isArray(offset.locationSequence),
  );
}

export function prepareOffsetsForRunCreate(offsets) {
  return selectOffsetsForRun(offsets).map(offset => ({
    definitionUri: offset.definitionUri,
    locationSequence: offset.locationSequence,
    vector: offset.vector,
  }));
}

/** Default staleness window for stored labware offsets. Not a magic number at call sites. */
export const DEFAULT_LABWARE_OFFSET_MAX_AGE_DAYS = 30;

export function loadNameFromDefinitionUri(definitionUri) {
  const parts = String(definitionUri || "").split("/").filter(Boolean);
  return parts.length >= 2 ? parts[1] : null;
}

export function offsetMatchesLoadName(offset, loadName) {
  return loadNameFromDefinitionUri(offset?.definitionUri) === String(loadName || "");
}

export function locationSequenceMentionsSlot(locationSequence, slot) {
  if (!Array.isArray(locationSequence)) {
    return false;
  }
  const slotU = String(slot || "")
    .trim()
    .toUpperCase();
  if (!slotU) {
    return false;
  }
  return locationSequence.some(item => String(item?.addressableAreaName || "").toUpperCase() === slotU);
}

export function offsetAgeDays(createdAt, now = new Date()) {
  const t = new Date(createdAt || 0).getTime();
  if (!Number.isFinite(t) || t <= 0) {
    return null;
  }
  return (now.getTime() - t) / 86400000;
}

function newestByCreatedAt(offsets) {
  return (offsets || []).reduce((best, offset) => {
    if (!best) {
      return offset;
    }
    return new Date(offset.createdAt || 0).getTime() > new Date(best.createdAt || 0).getTime()
      ? offset
      : best;
  }, null);
}

/**
 * Coverage + staleness for protocol-declared labware vs stored robot offsets.
 * Uses the same selection as run create (dedupe + drop anyLocation).
 *
 * @param {object} options
 * @param {Array<{ kind: string, load_name: string | null, slot: string }>} options.declaredLoads
 * @param {Array} options.storedOffsets  raw GET /labwareOffsets data
 * @param {number} [options.maxAgeDays=DEFAULT_LABWARE_OFFSET_MAX_AGE_DAYS]
 * @param {Date} [options.now]
 */
export function checkDeclaredLabwareOffsetCoverage({
  declaredLoads = [],
  storedOffsets = [],
  maxAgeDays = DEFAULT_LABWARE_OFFSET_MAX_AGE_DAYS,
  now = new Date(),
} = {}) {
  const threshold = Number(maxAgeDays);
  const resolvedMaxAgeDays = Number.isFinite(threshold) ? threshold : DEFAULT_LABWARE_OFFSET_MAX_AGE_DAYS;
  const errors = [];
  const selected = selectOffsetsForRun(storedOffsets);
  const labwareLoads = (declaredLoads || []).filter(item => item?.kind === "labware" && item.load_name);

  for (const load of labwareLoads) {
    const matchingStored = (storedOffsets || []).filter(offset =>
      offsetMatchesLoadName(offset, load.load_name),
    );
    const matchingSelected = selected.filter(offset => offsetMatchesLoadName(offset, load.load_name));
    const slotMatched = matchingSelected.filter(offset =>
      locationSequenceMentionsSlot(offset.locationSequence, load.slot),
    );

    if (matchingStored.length === 0) {
      errors.push({
        code: "offset_missing",
        slot: load.slot,
        load_name: load.load_name,
        message: `No stored labware offset for ${load.load_name} (slot ${load.slot}).`,
      });
      continue;
    }

    if (matchingSelected.length === 0) {
      errors.push({
        code: "offset_not_applied",
        slot: load.slot,
        load_name: load.load_name,
        message: `Stored offsets for ${load.load_name} are anyLocation-only and would be dropped by prepareOffsetsForRunCreate.`,
      });
      continue;
    }

    if (slotMatched.length === 0) {
      errors.push({
        code: "offset_slot_uncovered",
        slot: load.slot,
        load_name: load.load_name,
        message: `No selected offset locationSequence mentions slot ${load.slot} for ${load.load_name}; stored selected offsets would not apply to this load.`,
      });
    }

    const newest = newestByCreatedAt(slotMatched.length > 0 ? slotMatched : matchingSelected);
    const ageDays = newest ? offsetAgeDays(newest.createdAt, now) : null;
    if (ageDays != null && ageDays > resolvedMaxAgeDays) {
      errors.push({
        code: "offset_stale",
        slot: load.slot,
        load_name: load.load_name,
        definitionUri: newest.definitionUri,
        createdAt: newest.createdAt,
        age_days: Math.round(ageDays * 1000) / 1000,
        max_age_days: resolvedMaxAgeDays,
        message: `Selected offset for ${load.load_name} at ${load.slot} is ${ageDays.toFixed(1)} days old (threshold ${resolvedMaxAgeDays} d).`,
      });
    }
  }

  return {
    errors,
    warnings: [],
    max_age_days: resolvedMaxAgeDays,
  };
}

export async function fetchRobotLabwareOffsets(robotIp) {
  const response = await requestRobotJson("GET", robotIp, "/labwareOffsets");
  return response?.data ?? [];
}

export async function resolveRunLabwareOffsets(robotIp, explicitOffsets = undefined) {
  if (explicitOffsets !== undefined) {
    const prepared = prepareOffsetsForRunCreate(explicitOffsets);
    return prepared.length > 0 ? prepared : null;
  }
  const offsets = await fetchRobotLabwareOffsets(robotIp);
  const prepared = prepareOffsetsForRunCreate(offsets);
  return prepared.length > 0 ? prepared : null;
}

export function buildProtocolRunCreateBody({
  protocolId,
  runTimeParameters = null,
  labwareOffsets = null,
}) {
  return {
    data: {
      protocolId,
      ...(runTimeParameters ? { runTimeParameterValues: runTimeParameters } : {}),
      ...(labwareOffsets ? { labwareOffsets } : {}),
    },
  };
}
