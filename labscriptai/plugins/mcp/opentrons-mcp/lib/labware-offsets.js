import fs from "fs";
import path from "path";

import { requestRobotJson } from "./http.js";
import { extractDeclaredProtocolLoads } from "./protocol-deck.js";

const DEFAULT_HISTORY_LIMIT = 5;
const DEFAULT_MAX_ABS_XY_MM = 5;
const DEFAULT_MAX_ABS_Z_MM = 3;

export function locationSequenceKey(locationSequence) {
  if (locationSequence === "anyLocation" || locationSequence == null) {
    return "anyLocation";
  }
  return JSON.stringify(locationSequence);
}

export function offsetRecordKey(offset) {
  return `${offset?.definitionUri || ""}::${locationSequenceKey(offset?.locationSequence)}`;
}

export function resolveWorkspaceRoot(explicitRoot = null) {
  if (explicitRoot && String(explicitRoot).trim()) {
    return path.resolve(String(explicitRoot).trim());
  }
  const fromEnv = process.env.LABSCRIPTAI_WORKSPACE;
  if (fromEnv && String(fromEnv).trim()) {
    return path.resolve(String(fromEnv).trim());
  }
  return process.cwd();
}

export function sanitizeDeviceId(deviceId) {
  const raw = String(deviceId || "").trim();
  if (!raw || raw.toLowerCase() === "unknown") {
    return null;
  }
  return raw.replace(/[^a-zA-Z0-9._-]+/g, "_");
}

export function offsetsDir(workspaceRoot) {
  return path.join(resolveWorkspaceRoot(workspaceRoot), ".labscriptai", "offsets");
}

export function offsetLedgerPath(workspaceRoot, deviceId) {
  const safeId = sanitizeDeviceId(deviceId);
  if (!safeId) {
    throw new Error("device_id_required");
  }
  return path.join(offsetsDir(workspaceRoot), `${safeId}.json`);
}

export function memoryChangelogPath(workspaceRoot, deviceId) {
  const safeId = sanitizeDeviceId(deviceId);
  if (!safeId) {
    throw new Error("device_id_required");
  }
  return path.join(
    resolveWorkspaceRoot(workspaceRoot),
    ".labscriptai",
    "memory",
    `offset_changelog__${safeId}.md`,
  );
}

export function emptyOffsetLedger(deviceId) {
  return {
    device_id: String(deviceId),
    updated_at: new Date().toISOString(),
    offsets: [],
  };
}

export function readOffsetLedger(workspaceRoot, deviceId) {
  const filePath = offsetLedgerPath(workspaceRoot, deviceId);
  if (!fs.existsSync(filePath)) {
    return emptyOffsetLedger(deviceId);
  }
  const raw = JSON.parse(fs.readFileSync(filePath, "utf8"));
  const offsets = Array.isArray(raw?.offsets) ? raw.offsets : [];
  return {
    device_id: raw?.device_id || String(deviceId),
    updated_at: raw?.updated_at || null,
    offsets,
  };
}

export function writeOffsetLedger(workspaceRoot, ledger) {
  const deviceId = ledger?.device_id;
  const filePath = offsetLedgerPath(workspaceRoot, deviceId);
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const payload = {
    device_id: String(deviceId),
    updated_at: new Date().toISOString(),
    offsets: Array.isArray(ledger?.offsets) ? ledger.offsets : [],
  };
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  return { path: filePath, ledger: payload };
}

export function appendOffsetChangelog(workspaceRoot, deviceId, line) {
  const filePath = memoryChangelogPath(workspaceRoot, deviceId);
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const stamp = new Date().toISOString();
  const text = `- ${stamp} ${String(line || "").trim()}\n`;
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(
      filePath,
      `# Offset changelog (${deviceId})\n\n${text}`,
      "utf8",
    );
  } else {
    fs.appendFileSync(filePath, text, "utf8");
  }
  return filePath;
}

export function dedupeLabwareOffsets(offsets) {
  const byKey = new Map();
  for (const offset of offsets || []) {
    const definitionUri = offset?.definitionUri;
    if (!definitionUri) {
      continue;
    }
    const key = offsetRecordKey(offset);
    const existing = byKey.get(key);
    if (
      !existing ||
      new Date(offset.createdAt || offset.updated_at || 0).getTime() >
        new Date(existing.createdAt || existing.updated_at || 0).getTime()
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

export function mergeWorkspaceAndRobotOffsets(workspaceRecords, robotOffsets) {
  const byKey = new Map();
  for (const offset of robotOffsets || []) {
    if (!offset?.definitionUri) {
      continue;
    }
    byKey.set(offsetRecordKey(offset), offset);
  }
  for (const record of workspaceRecords || []) {
    if (!record?.definitionUri || !Array.isArray(record.locationSequence)) {
      continue;
    }
    const key = offsetRecordKey(record);
    if (record.enabled === false) {
      // Tombstone: suppress matching robot offset for auto-merge.
      byKey.delete(key);
      continue;
    }
    byKey.set(key, {
      definitionUri: record.definitionUri,
      locationSequence: record.locationSequence,
      vector: record.vector,
      createdAt: record.updated_at || record.created_at || null,
      source: "workspace_ledger",
    });
  }
  return [...byKey.values()];
}

export function validateOffsetVector(
  vector,
  {
    force = false,
    maxAbsXyMm = DEFAULT_MAX_ABS_XY_MM,
    maxAbsZMm = DEFAULT_MAX_ABS_Z_MM,
  } = {},
) {
  if (!vector || typeof vector !== "object") {
    return { ok: false, error: "vector_required" };
  }
  const x = Number(vector.x);
  const y = Number(vector.y);
  const z = Number(vector.z);
  if (![x, y, z].every(Number.isFinite)) {
    return { ok: false, error: "vector_must_be_finite_xyz" };
  }
  const large =
    Math.abs(x) > maxAbsXyMm || Math.abs(y) > maxAbsXyMm || Math.abs(z) > maxAbsZMm;
  if (large && !force) {
    return {
      ok: false,
      error: "vector_magnitude_requires_force",
      limits: { maxAbsXyMm, maxAbsZMm },
      vector: { x, y, z },
    };
  }
  return { ok: true, vector: { x, y, z }, large };
}

function pushHistory(existing, limit = DEFAULT_HISTORY_LIMIT) {
  if (!existing?.vector) {
    return Array.isArray(existing?.history) ? existing.history.slice(0, limit) : [];
  }
  const entry = {
    vector: existing.vector,
    updated_at: existing.updated_at || existing.created_at || null,
    source: existing.source || null,
    note: existing.note || null,
  };
  const prior = Array.isArray(existing.history) ? existing.history : [];
  return [entry, ...prior].slice(0, limit);
}

export function upsertOffsetRecord(ledger, {
  definitionUri,
  locationSequence,
  vector,
  source = "operator_confirmed",
  note = null,
  enabled = true,
}) {
  if (!definitionUri || typeof definitionUri !== "string") {
    throw new Error("definitionUri_required");
  }
  if (!Array.isArray(locationSequence)) {
    throw new Error("locationSequence_must_be_array");
  }
  const now = new Date().toISOString();
  const key = offsetRecordKey({ definitionUri, locationSequence });
  const offsets = Array.isArray(ledger.offsets) ? [...ledger.offsets] : [];
  const index = offsets.findIndex(item => offsetRecordKey(item) === key);
  if (index >= 0) {
    const existing = offsets[index];
    offsets[index] = {
      ...existing,
      definitionUri,
      locationSequence,
      vector,
      enabled: enabled !== false,
      source,
      note: note ?? existing.note ?? null,
      created_at: existing.created_at || now,
      updated_at: now,
      history: pushHistory(existing),
    };
  } else {
    offsets.push({
      definitionUri,
      locationSequence,
      vector,
      enabled: enabled !== false,
      source,
      note: note || null,
      created_at: now,
      updated_at: now,
      history: [],
    });
  }
  return {
    ...ledger,
    updated_at: now,
    offsets,
  };
}

export function disableOffsetRecord(ledger, { definitionUri, locationSequence }) {
  const key = offsetRecordKey({ definitionUri, locationSequence });
  const now = new Date().toISOString();
  const offsets = (ledger.offsets || []).map(item => {
    if (offsetRecordKey(item) !== key) {
      return item;
    }
    return {
      ...item,
      enabled: false,
      updated_at: now,
      history: pushHistory(item),
    };
  });
  if (!offsets.some(item => offsetRecordKey(item) === key)) {
    throw new Error("offset_not_found");
  }
  return { ...ledger, updated_at: now, offsets };
}

export function revertOffsetRecord(ledger, { definitionUri, locationSequence }) {
  const key = offsetRecordKey({ definitionUri, locationSequence });
  const now = new Date().toISOString();
  let found = false;
  const offsets = (ledger.offsets || []).map(item => {
    if (offsetRecordKey(item) !== key) {
      return item;
    }
    found = true;
    const history = Array.isArray(item.history) ? item.history : [];
    if (history.length === 0) {
      throw new Error("offset_history_empty");
    }
    const [previous, ...rest] = history;
    return {
      ...item,
      vector: previous.vector,
      source: previous.source || "reverted",
      note: previous.note ?? item.note ?? null,
      enabled: true,
      updated_at: now,
      history: rest,
    };
  });
  if (!found) {
    throw new Error("offset_not_found");
  }
  return { ...ledger, updated_at: now, offsets };
}

export async function fetchRobotLabwareOffsets(robotIp) {
  const response = await requestRobotJson("GET", robotIp, "/labwareOffsets");
  return response?.data ?? [];
}

export async function fetchRobotSerial(robotIp) {
  const health = await requestRobotJson("GET", robotIp, "/health");
  const serial = health?.serialNumber || health?.robot_serial || health?.robotSerial || null;
  const safe = sanitizeDeviceId(serial);
  if (!safe) {
    throw new Error("robot_serial_unavailable");
  }
  return { serial: safe, health };
}

export async function postRobotLabwareOffset(robotIp, {
  definitionUri,
  locationSequence,
  vector,
}) {
  return requestRobotJson("POST", robotIp, "/labwareOffsets", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      data: {
        definitionUri,
        locationSequence,
        vector,
      },
    }),
  });
}

export async function resolveRunLabwareOffsets(
  robotIp,
  explicitOffsets = undefined,
  { workspaceRoot = null } = {},
) {
  // Explicit (including []) fully replaces — do not merge workspace or robot.
  if (explicitOffsets !== undefined) {
    const prepared = prepareOffsetsForRunCreate(explicitOffsets);
    return prepared.length > 0 ? prepared : null;
  }

  const robotOffsets = await fetchRobotLabwareOffsets(robotIp);
  let workspaceRecords = [];
  try {
    const { serial } = await fetchRobotSerial(robotIp);
    const ledger = readOffsetLedger(workspaceRoot, serial);
    workspaceRecords = ledger.offsets || [];
  } catch {
    workspaceRecords = [];
  }

  const merged = mergeWorkspaceAndRobotOffsets(workspaceRecords, robotOffsets);
  const prepared = prepareOffsetsForRunCreate(merged);
  return prepared.length > 0 ? prepared : null;
}

export async function recordLabwareOffset({
  robotIp,
  op = "upsert",
  definitionUri,
  locationSequence,
  vector,
  source = "operator_confirmed",
  note = null,
  force = false,
  writeChangelog = true,
  syncRobot = true,
  workspaceRoot = null,
}) {
  const { serial } = await fetchRobotSerial(robotIp);
  let ledger = readOffsetLedger(workspaceRoot, serial);
  const normalizedOp = String(op || "upsert").trim().toLowerCase();

  if (normalizedOp === "upsert") {
    const validated = validateOffsetVector(vector, { force });
    if (!validated.ok) {
      return {
        ok: false,
        error: validated.error,
        details: validated,
        device_id: serial,
      };
    }
    ledger = upsertOffsetRecord(ledger, {
      definitionUri,
      locationSequence,
      vector: validated.vector,
      source,
      note,
      enabled: true,
    });
  } else if (normalizedOp === "disable") {
    ledger = disableOffsetRecord(ledger, { definitionUri, locationSequence });
  } else if (normalizedOp === "revert") {
    ledger = revertOffsetRecord(ledger, { definitionUri, locationSequence });
  } else {
    return { ok: false, error: "invalid_op", allowed: ["upsert", "disable", "revert"] };
  }

  const written = writeOffsetLedger(workspaceRoot, ledger);
  const record = (written.ledger.offsets || []).find(
    item => offsetRecordKey(item) === offsetRecordKey({ definitionUri, locationSequence }),
  );

  let changelogPath = null;
  if (writeChangelog) {
    const summary =
      normalizedOp === "upsert"
        ? `upsert ${definitionUri} @ ${locationSequenceKey(locationSequence)} -> ${JSON.stringify(record?.vector)}`
        : `${normalizedOp} ${definitionUri} @ ${locationSequenceKey(locationSequence)}`;
    changelogPath = appendOffsetChangelog(workspaceRoot, serial, note ? `${summary} (${note})` : summary);
  }

  let robotSync = { attempted: false, ok: null, response: null, error: null };
  if (syncRobot && normalizedOp !== "disable" && record?.enabled !== false && record?.vector) {
    robotSync.attempted = true;
    try {
      robotSync.response = await postRobotLabwareOffset(robotIp, {
        definitionUri: record.definitionUri,
        locationSequence: record.locationSequence,
        vector: record.vector,
      });
      robotSync.ok = true;
    } catch (error) {
      robotSync.ok = false;
      robotSync.error = error?.message || String(error);
    }
  }

  return {
    ok: true,
    op: normalizedOp,
    device_id: serial,
    ledger_path: written.path,
    record,
    changelog_path: changelogPath,
    robot_sync: robotSync,
  };
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

export function slotLocationSequence(slotName) {
  const slot = String(slotName || "")
    .trim()
    .toUpperCase();
  if (!/^[A-D][1-3]$/.test(slot)) {
    return null;
  }
  return [{ kind: "onAddressableArea", addressableAreaName: slot }];
}

export function slotFromLocationSequence(locationSequence) {
  if (!Array.isArray(locationSequence)) {
    return null;
  }
  for (const step of locationSequence) {
    if (!step || typeof step !== "object") {
      continue;
    }
    if (step.addressableAreaName) {
      return String(step.addressableAreaName).trim().toUpperCase();
    }
    if (step.slotName) {
      return String(step.slotName).trim().toUpperCase();
    }
  }
  return null;
}

export function guessDefinitionUri(loadName, version = 1) {
  const name = String(loadName || "").trim();
  if (!name) {
    return null;
  }
  if (name.includes("/")) {
    return name;
  }
  return `opentrons/${name}/${version}`;
}

export function normalizeRobotOffsetForLedger(offset) {
  if (!offset?.definitionUri || !offset?.vector) {
    return null;
  }
  let locationSequence = offset.locationSequence;
  if (!Array.isArray(locationSequence)) {
    const slot =
      offset.location?.slotName ||
      offset.location?.slot_name ||
      slotFromLocationSequence(locationSequence);
    if (!slot) {
      return null;
    }
    locationSequence = slotLocationSequence(slot);
    if (!locationSequence) {
      return null;
    }
  }
  return {
    definitionUri: offset.definitionUri,
    locationSequence,
    vector: {
      x: Number(offset.vector.x),
      y: Number(offset.vector.y),
      z: Number(offset.vector.z),
    },
    createdAt: offset.createdAt || offset.created_at || null,
    id: offset.id || null,
  };
}

function normalizeLoadToken(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/_/g, "-");
}

export function offsetCoversDeclaredLoad(offset, load) {
  if (!offset || !load?.slot || !load?.load_name) {
    return false;
  }
  const slot = String(load.slot).trim().toUpperCase();
  const offsetSlot = slotFromLocationSequence(offset.locationSequence);
  if (offsetSlot !== slot) {
    return false;
  }
  const loadToken = normalizeLoadToken(load.load_name);
  const uriToken = normalizeLoadToken(offset.definitionUri);
  if (!loadToken || !uriToken) {
    return false;
  }
  return (
    uriToken.includes(loadToken) ||
    uriToken.includes(`/${loadToken}/`) ||
    loadToken.includes(uriToken.split("/").slice(-2, -1)[0] || "")
  );
}

export function assessOffsetCoverage({
  declaredLoads = [],
  workspaceRecords = [],
  robotOffsets = [],
  strict = false,
} = {}) {
  const labwareLoads = (declaredLoads || []).filter(
    load => load?.kind === "labware" && load.load_name && load.slot,
  );
  const merged = mergeWorkspaceAndRobotOffsets(workspaceRecords, robotOffsets);
  const applicable = selectOffsetsForRun(merged);

  const covered = [];
  const missing = [];
  for (const load of labwareLoads) {
    const match = applicable.find(offset => offsetCoversDeclaredLoad(offset, load));
    const expectedLocationSequence = slotLocationSequence(load.slot);
    const row = {
      kind: load.kind,
      load_name: load.load_name,
      slot: String(load.slot).toUpperCase(),
      expected_definitionUri: guessDefinitionUri(load.load_name),
      expected_locationSequence: expectedLocationSequence,
    };
    if (match) {
      covered.push({
        ...row,
        matched: {
          definitionUri: match.definitionUri,
          locationSequence: match.locationSequence,
          vector: match.vector,
          source: match.source || null,
        },
      });
    } else {
      missing.push(row);
    }
  }

  const status = missing.length === 0 ? "pass" : strict ? "fail" : "warn";
  return {
    ok: status !== "fail",
    status,
    strict: Boolean(strict),
    covered,
    missing,
    covered_count: covered.length,
    missing_count: missing.length,
    summary:
      missing.length === 0
        ? `Offset coverage complete for ${covered.length} declared labware load(s).`
        : `Missing offsets for ${missing.length} declared labware load(s): ${missing
            .map(item => `${item.load_name}@${item.slot}`)
            .join(", ")}. Import LPC via import_robot_labware_offsets or record_labware_offset.`,
  };
}

export async function listLabwareOffsets({
  robotIp,
  workspaceRoot = null,
} = {}) {
  const { serial, health } = await fetchRobotSerial(robotIp);
  const ledger = readOffsetLedger(workspaceRoot, serial);
  const robotOffsets = await fetchRobotLabwareOffsets(robotIp);
  const merged = mergeWorkspaceAndRobotOffsets(ledger.offsets || [], robotOffsets);
  const mergePreview = prepareOffsetsForRunCreate(merged) || [];

  const ledgerByKey = new Map(
    (ledger.offsets || [])
      .filter(item => Array.isArray(item.locationSequence))
      .map(item => [offsetRecordKey(item), item]),
  );
  const robotNormalized = (robotOffsets || [])
    .map(normalizeRobotOffsetForLedger)
    .filter(Boolean);
  const robotByKey = new Map(robotNormalized.map(item => [offsetRecordKey(item), item]));

  const tombstones = (ledger.offsets || []).filter(
    item => item.enabled === false && Array.isArray(item.locationSequence),
  );
  const ledgerOnly = [];
  const robotOnly = [];
  const both = [];

  for (const [key, item] of ledgerByKey.entries()) {
    if (item.enabled === false) {
      continue;
    }
    if (robotByKey.has(key)) {
      both.push({ key, ledger: item, robot: robotByKey.get(key) });
    } else {
      ledgerOnly.push(item);
    }
  }
  for (const [key, item] of robotByKey.entries()) {
    const ledgerItem = ledgerByKey.get(key);
    if (!ledgerItem || ledgerItem.enabled === false) {
      robotOnly.push(item);
    }
  }

  return {
    ok: true,
    device_id: serial,
    robot_name: health?.name || null,
    ledger_path: offsetLedgerPath(workspaceRoot, serial),
    ledger: {
      updated_at: ledger.updated_at,
      offsets: ledger.offsets || [],
      enabled_count: (ledger.offsets || []).filter(item => item.enabled !== false).length,
      tombstone_count: tombstones.length,
    },
    robot: {
      count: Array.isArray(robotOffsets) ? robotOffsets.length : 0,
      offsets: robotOffsets,
      importable_count: robotNormalized.length,
    },
    merge_preview: mergePreview,
    diff: {
      both,
      ledger_only: ledgerOnly,
      robot_only: robotOnly,
      tombstones,
    },
  };
}

export async function importRobotLabwareOffsets({
  robotIp,
  workspaceRoot = null,
  confirm = false,
  force = false,
  writeChangelog = true,
  definitionUri = null,
  slot = null,
  note = null,
} = {}) {
  const { serial } = await fetchRobotSerial(robotIp);
  const robotOffsets = await fetchRobotLabwareOffsets(robotIp);
  const slotFilter = slot ? String(slot).trim().toUpperCase() : null;
  const uriFilter = definitionUri ? String(definitionUri).trim() : null;

  const candidates = [];
  const skipped = [];
  for (const raw of robotOffsets || []) {
    const normalized = normalizeRobotOffsetForLedger(raw);
    if (!normalized) {
      skipped.push({
        reason: "not_slot_scoped",
        definitionUri: raw?.definitionUri || null,
        locationSequence: raw?.locationSequence ?? null,
      });
      continue;
    }
    const offsetSlot = slotFromLocationSequence(normalized.locationSequence);
    if (slotFilter && offsetSlot !== slotFilter) {
      skipped.push({ reason: "slot_filter", ...normalized });
      continue;
    }
    if (uriFilter && normalized.definitionUri !== uriFilter) {
      skipped.push({ reason: "definition_filter", ...normalized });
      continue;
    }
    const validated = validateOffsetVector(normalized.vector, { force });
    if (!validated.ok) {
      skipped.push({
        reason: validated.error,
        ...normalized,
        details: validated,
      });
      continue;
    }
    candidates.push({
      ...normalized,
      vector: validated.vector,
      large: validated.large,
    });
  }

  if (!confirm) {
    return {
      ok: true,
      dry_run: true,
      device_id: serial,
      candidate_count: candidates.length,
      skipped_count: skipped.length,
      candidates,
      skipped,
      summary:
        candidates.length > 0
          ? `Dry run: ${candidates.length} LPC/robot offset(s) ready to import. Re-call with confirm=true to write ledger.`
          : "Dry run: no importable slot-scoped robot offsets matched filters.",
    };
  }

  let ledger = readOffsetLedger(workspaceRoot, serial);
  const imported = [];
  for (const candidate of candidates) {
    ledger = upsertOffsetRecord(ledger, {
      definitionUri: candidate.definitionUri,
      locationSequence: candidate.locationSequence,
      vector: candidate.vector,
      source: "lpc_import",
      note: note || "Imported from robot /labwareOffsets after LPC",
      enabled: true,
    });
    imported.push(candidate);
  }
  const written = writeOffsetLedger(workspaceRoot, ledger);

  let changelogPath = null;
  if (writeChangelog && imported.length > 0) {
    changelogPath = appendOffsetChangelog(
      workspaceRoot,
      serial,
      `import ${imported.length} robot offset(s)${note ? ` (${note})` : ""}`,
    );
  }

  return {
    ok: true,
    dry_run: false,
    device_id: serial,
    ledger_path: written.path,
    imported_count: imported.length,
    skipped_count: skipped.length,
    imported,
    skipped,
    changelog_path: changelogPath,
    summary: `Imported ${imported.length} robot offset(s) into workspace ledger.`,
  };
}

export async function assessOffsetCoverageForRobot({
  robotIp,
  filePath = null,
  protocolSource = null,
  workspaceRoot = null,
  strict = false,
  declaredLoads = null,
} = {}) {
  let loads = Array.isArray(declaredLoads) ? declaredLoads : null;
  let source = protocolSource;
  if (!loads && !source && filePath) {
    source = fs.readFileSync(path.resolve(filePath), "utf8");
  }
  if (!loads && source) {
    loads = extractDeclaredProtocolLoads(source);
  }
  loads = loads || [];

  let serial = null;
  let workspaceRecords = [];
  let robotOffsets = [];
  try {
    const fetched = await fetchRobotSerial(robotIp);
    serial = fetched.serial;
    workspaceRecords = readOffsetLedger(workspaceRoot, serial).offsets || [];
  } catch {
    workspaceRecords = [];
  }
  try {
    robotOffsets = await fetchRobotLabwareOffsets(robotIp);
  } catch {
    robotOffsets = [];
  }

  const coverage = assessOffsetCoverage({
    declaredLoads: loads,
    workspaceRecords,
    robotOffsets,
    strict,
  });
  return {
    ...coverage,
    device_id: serial,
    declared_labware_count: loads.filter(item => item.kind === "labware").length,
  };
}
