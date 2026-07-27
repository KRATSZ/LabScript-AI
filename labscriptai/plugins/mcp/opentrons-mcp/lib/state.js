import fs from "fs";
import path from "path";

import { SESSION_STATE_DIR } from "./paths.js";

function sessionStateDir() {
  return process.env.OPENTRONS_SESSION_STATE_DIR
    ? path.resolve(process.env.OPENTRONS_SESSION_STATE_DIR)
    : SESSION_STATE_DIR;
}

export const DEFAULT_SESSION_ID = "default";
export const FLEX_SLOT_NAMES = [
  "A1",
  "A2",
  "A3",
  "B1",
  "B2",
  "B3",
  "C1",
  "C2",
  "C3",
  "D1",
  "D2",
  "D3",
];

export const COLUMN_MAJOR_WELL_ORDER_96 = Array.from({ length: 12 }, (_, columnIndex) =>
  ["A", "B", "C", "D", "E", "F", "G", "H"].map(row => `${row}${columnIndex + 1}`),
).flat();

export const LIQUID_TRUST_LEVELS = Object.freeze(["declared", "simulated", "observed", "reconciled"]);

export const TRUST_LEVEL_RANK = Object.freeze({
  declared: 0,
  simulated: 1,
  observed: 2,
  reconciled: 3,
});

export function canOverwriteTrust(currentTrust, newTrust) {
  const currentRank = TRUST_LEVEL_RANK[normalizeTrustLevel(currentTrust, "declared")] ?? TRUST_LEVEL_RANK.declared;
  const newRank = TRUST_LEVEL_RANK[normalizeTrustLevel(newTrust, "declared")] ?? TRUST_LEVEL_RANK.declared;
  return newRank >= currentRank;
}

function trustLevelFromRank(rank) {
  for (const level of LIQUID_TRUST_LEVELS) {
    if (TRUST_LEVEL_RANK[level] === rank) {
      return level;
    }
  }
  return "declared";
}

export const MAX_STATE_HISTORY_ENTRIES = 2000;

function sanitizeSessionId(sessionId = DEFAULT_SESSION_ID) {
  return String(sessionId || DEFAULT_SESSION_ID).replace(/[^a-zA-Z0-9._-]/g, "_");
}

function buildDefaultSessionState(sessionId = DEFAULT_SESSION_ID) {
  return {
    session_id: sanitizeSessionId(sessionId),
    state_revision: 0,
    robot_serial: null,
    last_run_id: null,
    needs_reconciliation: false,
    deck: {
      slots: {},
    },
    pipettes: {},
    tip_tracking: {
      tipracks: {},
    },
    liquid_tracking: {
      containers: {},
      sources: {},
    },
    state_history: [],
    cleanup: {
      pending_actions: [],
      auto_home_allowed: null,
    },
    updated_at: new Date().toISOString(),
  };
}

function ensureStateDirectory() {
  fs.mkdirSync(sessionStateDir(), { recursive: true });
}

function sessionStatePath(sessionId = DEFAULT_SESSION_ID) {
  return path.join(sessionStateDir(), `${sanitizeSessionId(sessionId)}.json`);
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function uniqueStrings(values = []) {
  return [...new Set(values.filter(Boolean).map(value => String(value)))];
}

export function uniqueSessionStrings(values = []) {
  return uniqueStrings(values);
}

function normalizeSlotName(slotName) {
  return slotName ? String(slotName).trim().toUpperCase() : null;
}

function normalizeWellName(wellName) {
  return wellName ? String(wellName).trim().toUpperCase() : null;
}

function normalizeLiquidNumber(value, fallback = null) {
  if (value === undefined || value === null || value === "") {
    return fallback;
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

export function normalizeTrustLevel(value, fallback = "declared") {
  const normalized = String(value || fallback || "declared").trim().toLowerCase();
  return LIQUID_TRUST_LEVELS.includes(normalized) ? normalized : fallback;
}

function normalizeContainerRole(value, fallback = "source") {
  const normalized = String(value || fallback || "unknown").trim().toLowerCase();
  return ["source", "destination", "intermediate", "waste", "unknown"].includes(normalized)
    ? normalized
    : fallback;
}

export function liquidSourceKey({ slotName, wellName } = {}) {
  const slot = normalizeSlotName(slotName);
  const well = normalizeWellName(wellName);
  return slot && well ? `${slot}.${well}` : null;
}

export function liquidContainerKey({ containerKey, key, slotName, wellName } = {}) {
  const explicit = containerKey || key;
  if (explicit) {
    const raw = String(explicit).trim();
    const match = raw.match(/^([a-d][1-3])\.([a-h][1-9][0-2]?|[a-h][1-9])$/i);
    return match ? `${match[1].toUpperCase()}.${match[2].toUpperCase()}` : raw;
  }
  return liquidSourceKey({ slotName, wellName });
}

function splitContainerKey(key) {
  const match = String(key || "").match(/^([A-D][1-3])\.([A-H][1-9][0-2]?|[A-H][1-9])$/i);
  return match ? { slot_name: match[1].toUpperCase(), well_name: match[2].toUpperCase() } : {};
}

function normalizeStepForHistory(step) {
  if (!step) {
    return null;
  }
  if (typeof step === "string") {
    return { id: step };
  }
  return {
    id: step.id || step.step_id || step.name || null,
    type: step.type || step.action || null,
  };
}

function sameJsonValue(left, right) {
  return JSON.stringify(left ?? null) === JSON.stringify(right ?? null);
}

export function appendStateHistoryEntry(sessionState, { step = null, field, oldValue, newValue, why = null, trustLevel = null, derivedFrom = null } = {}) {
  if (!field || sameJsonValue(oldValue, newValue)) {
    return null;
  }
  sessionState.state_history = Array.isArray(sessionState.state_history)
    ? sessionState.state_history
    : [];
  const entry = {
    timestamp: new Date().toISOString(),
    step: normalizeStepForHistory(step),
    field,
    old_value: oldValue ?? null,
    new_value: newValue ?? null,
    why: why || null,
    trust_level: trustLevel ? normalizeTrustLevel(trustLevel) : null,
  };
  if (derivedFrom !== null && derivedFrom !== undefined) {
    entry.derived_from = normalizeTrustLevel(derivedFrom, "declared");
  }
  sessionState.state_history.push(entry);
  if (sessionState.state_history.length > MAX_STATE_HISTORY_ENTRIES) {
    const overflow = sessionState.state_history.length - MAX_STATE_HISTORY_ENTRIES;
    sessionState.state_history.splice(0, overflow);
  }
  return entry;
}

function normalizeLiquidContainerEntry(key, entry = {}, { defaultRole = "source", defaultTrustLevel = "declared" } = {}) {
  const keyParts = splitContainerKey(key);
  const slotName = normalizeSlotName(entry.slot_name || entry.slotName || keyParts.slot_name);
  const wellName = normalizeWellName(entry.well_name || entry.wellName || keyParts.well_name);
  const resolvedKey = liquidContainerKey({
    containerKey: entry.container_key || entry.containerKey || entry.key || key,
    slotName,
    wellName,
  });
  if (!resolvedKey) {
    return null;
  }

  const volumeUl = normalizeLiquidNumber(entry.volume_ul ?? entry.volumeUl, null);
  const capacityUl = normalizeLiquidNumber(entry.capacity_ul ?? entry.capacityUl, null);
  const deadVolumeUl = normalizeLiquidNumber(entry.dead_volume_ul ?? entry.deadVolumeUl, null);
  const expectedMinHeightMm = normalizeLiquidNumber(
    entry.expected_min_height_mm ?? entry.expectedMinHeightMm,
    null,
  );

  return {
    ...entry,
    key: resolvedKey,
    container_key: resolvedKey,
    role: normalizeContainerRole(entry.role || entry.container_role || entry.containerRole, defaultRole),
    slot_name: slotName,
    well_name: wellName,
    labware_load_name: entry.labware_load_name || entry.labwareLoadName || null,
    liquid_name: entry.liquid_name || entry.liquidName || null,
    sample_id: entry.sample_id || entry.sampleId || null,
    liquid_class: entry.liquid_class || entry.liquidClass || null,
    volume_ul: volumeUl,
    capacity_ul: capacityUl,
    dead_volume_ul: deadVolumeUl,
    expected_presence: entry.expected_presence ?? entry.expectedPresence ?? null,
    observed_presence: entry.observed_presence ?? entry.observedPresence ?? null,
    observed_height_mm: normalizeLiquidNumber(entry.observed_height_mm ?? entry.observedHeightMm, null),
    observed_probe_mode: entry.observed_probe_mode || entry.observedProbeMode || null,
    observed_at: entry.observed_at || entry.observedAt || null,
    observed_run_id: entry.observed_run_id || entry.observedRunId || null,
    observed_source: entry.observed_source || entry.observedSource || null,
    expected_min_height_mm: expectedMinHeightMm,
    notes: entry.notes || null,
    trust_level: normalizeTrustLevel(entry.trust_level || entry.trustLevel, defaultTrustLevel),
    updated_at: entry.updated_at || new Date().toISOString(),
  };
}

export function normalizeLiquidTracking(liquidTracking = {}) {
  const containers = {};
  const sourceEntries = Object.entries(liquidTracking?.sources || {});
  const containerEntries = Object.entries(liquidTracking?.containers || {});

  for (const [key, source] of sourceEntries) {
    const normalized = normalizeLiquidContainerEntry(key, source, {
      defaultRole: "source",
      defaultTrustLevel: source?.trust_level || source?.trustLevel || "declared",
    });
    if (normalized) {
      containers[normalized.key] = normalized;
    }
  }

  for (const [key, container] of containerEntries) {
    const existing = containers[liquidContainerKey({ containerKey: key })] || {};
    const normalized = normalizeLiquidContainerEntry(
      key,
      { ...existing, ...container },
      {
        defaultRole: container?.role || existing.role || "unknown",
        defaultTrustLevel: container?.trust_level || existing.trust_level || "declared",
      },
    );
    if (normalized) {
      containers[normalized.key] = normalized;
    }
  }

  const sources = Object.fromEntries(
    Object.entries(containers).filter(([, container]) => container.role === "source"),
  );

  return {
    ...liquidTracking,
    containers,
    sources,
  };
}

export function readSessionState(sessionId = DEFAULT_SESSION_ID) {
  ensureStateDirectory();
  const filePath = sessionStatePath(sessionId);
  const fallback = buildDefaultSessionState(sessionId);

  if (!fs.existsSync(filePath)) {
    return fallback;
  }

  try {
    const parsed = JSON.parse(fs.readFileSync(filePath, "utf8"));
    return {
      ...fallback,
      ...parsed,
      deck: {
        ...fallback.deck,
        ...(parsed.deck || {}),
        slots: {
          ...fallback.deck.slots,
          ...(parsed.deck?.slots || {}),
        },
      },
      pipettes: {
        ...fallback.pipettes,
        ...(parsed.pipettes || {}),
      },
      tip_tracking: {
        ...fallback.tip_tracking,
        ...(parsed.tip_tracking || {}),
        tipracks: {
          ...fallback.tip_tracking.tipracks,
          ...(parsed.tip_tracking?.tipracks || {}),
        },
      },
      liquid_tracking: {
        ...normalizeLiquidTracking({
          ...fallback.liquid_tracking,
          ...(parsed.liquid_tracking || {}),
          containers: {
            ...fallback.liquid_tracking.containers,
            ...(parsed.liquid_tracking?.containers || {}),
          },
          sources: {
            ...fallback.liquid_tracking.sources,
            ...(parsed.liquid_tracking?.sources || {}),
          },
        }),
      },
      state_history: Array.isArray(parsed.state_history) ? parsed.state_history : [],
      cleanup: {
        ...fallback.cleanup,
        ...(parsed.cleanup || {}),
        pending_actions: uniqueStrings(parsed.cleanup?.pending_actions || []),
      },
    };
  } catch {
    return fallback;
  }
}

export function writeSessionState(sessionState) {
  ensureStateDirectory();
  const normalized = {
    ...buildDefaultSessionState(sessionState?.session_id),
    ...clone(sessionState),
    session_id: sanitizeSessionId(sessionState?.session_id),
    updated_at: new Date().toISOString(),
  };
  normalized.liquid_tracking = normalizeLiquidTracking(normalized.liquid_tracking);
  normalized.state_history = Array.isArray(normalized.state_history) ? normalized.state_history : [];
  fs.writeFileSync(sessionStatePath(normalized.session_id), `${JSON.stringify(normalized, null, 2)}\n`);
  return normalized;
}

export function updateSessionState(sessionId, updater) {
  const currentState = readSessionState(sessionId);
  const draft = clone(currentState);
  const nextState = updater(draft) || draft;
  nextState.session_id = sanitizeSessionId(nextState.session_id || currentState.session_id || sessionId);
  nextState.state_revision = Number(currentState.state_revision || 0) + 1;
  nextState.updated_at = new Date().toISOString();
  return writeSessionState(nextState);
}

export function mutateSessionState(sessionId, mutator) {
  const currentState = readSessionState(sessionId);
  const draft = clone(currentState);
  const before = JSON.stringify(draft);
  const mutated = mutator(draft) || draft;
  const after = JSON.stringify(mutated);

  if (before === after) {
    return {
      state: currentState,
      changed: false,
    };
  }

  return {
    state: updateSessionState(sessionId, () => mutated),
    changed: true,
  };
}

export function ensureTiprackState(sessionState, { slotName, loadName = null } = {}) {
  if (!slotName) {
    return null;
  }

  sessionState.tip_tracking ||= { tipracks: {} };
  sessionState.tip_tracking.tipracks ||= {};

  const current = sessionState.tip_tracking.tipracks[slotName] || {
    slot_name: slotName,
    load_name: loadName,
    search_order: COLUMN_MAJOR_WELL_ORDER_96,
    missing_wells: [],
    depleted_wells: [],
    unknown_blocked_wells: [],
    last_suggested_well: null,
    last_good_tip: null,
  };

  current.load_name ||= loadName;
  current.search_order = Array.isArray(current.search_order) && current.search_order.length > 0
    ? current.search_order
    : COLUMN_MAJOR_WELL_ORDER_96;
  current.missing_wells = uniqueStrings(current.missing_wells);
  current.depleted_wells = uniqueStrings(current.depleted_wells);
  current.unknown_blocked_wells = uniqueStrings(current.unknown_blocked_wells);
  current.last_good_tip = current.last_good_tip ? String(current.last_good_tip) : null;

  sessionState.tip_tracking.tipracks[slotName] = current;
  return current;
}

export function markTipWellStatus(sessionState, { slotName, wellName, status } = {}) {
  if (!slotName || !wellName || !status) {
    return null;
  }

  const tiprackState = ensureTiprackState(sessionState, { slotName });
  const groups = {
    missing: "missing_wells",
    depleted: "depleted_wells",
    "unknown-blocked": "unknown_blocked_wells",
  };
  const targetKey = groups[status];

  if (!targetKey) {
    return tiprackState;
  }

  for (const key of Object.values(groups)) {
    tiprackState[key] = uniqueStrings(
      (tiprackState[key] || []).filter(existingWell => existingWell !== wellName),
    );
  }

  tiprackState[targetKey] = uniqueStrings([...(tiprackState[targetKey] || []), wellName]);
  if (status === "depleted") {
    tiprackState.last_good_tip = wellName;
  } else if (tiprackState.last_good_tip === wellName) {
    tiprackState.last_good_tip = null;
  }
  return tiprackState;
}

export function computeStartingTip(tiprackState = {}) {
  const searchOrder = Array.isArray(tiprackState.search_order) && tiprackState.search_order.length > 0
    ? tiprackState.search_order
    : COLUMN_MAJOR_WELL_ORDER_96;
  const missing = new Set(uniqueStrings(tiprackState.missing_wells || []));
  const depleted = new Set(uniqueStrings(tiprackState.depleted_wells || []));
  const unknownBlocked = new Set(uniqueStrings(tiprackState.unknown_blocked_wells || []));

  return searchOrder.find(
    wellName => !missing.has(wellName) && !depleted.has(wellName) && !unknownBlocked.has(wellName),
  ) || null;
}

export function setDeckSlotState(sessionState, slotName, slotState) {
  if (!slotName) {
    return;
  }
  sessionState.deck ||= { slots: {} };
  sessionState.deck.slots ||= {};
  sessionState.deck.slots[slotName] = {
    slot_name: slotName,
    ...(slotState || {}),
  };
}

export function setPipetteState(sessionState, mount, pipetteState) {
  if (!mount) {
    return;
  }
  sessionState.pipettes ||= {};
  sessionState.pipettes[mount] = {
    ...(sessionState.pipettes[mount] || {}),
    ...(pipetteState || {}),
  };
}

export function setCleanupState(sessionState, cleanupState) {
  sessionState.cleanup ||= {
    pending_actions: [],
    auto_home_allowed: null,
  };
  sessionState.cleanup = {
    ...sessionState.cleanup,
    ...(cleanupState || {}),
    pending_actions: uniqueStrings(
      cleanupState?.pending_actions ?? sessionState.cleanup.pending_actions ?? [],
    ),
  };
}

function ensureLiquidTracking(sessionState) {
  sessionState.liquid_tracking = normalizeLiquidTracking(
    sessionState.liquid_tracking || { containers: {}, sources: {} },
  );
  return sessionState.liquid_tracking;
}

function recordContainerFieldChanges(sessionState, { key, before = {}, after = {}, step = null, why = null } = {}) {
  const fields = [
    "role",
    "slot_name",
    "well_name",
    "labware_load_name",
    "liquid_name",
    "sample_id",
    "liquid_class",
    "volume_ul",
    "capacity_ul",
    "dead_volume_ul",
    "expected_presence",
    "observed_presence",
    "observed_height_mm",
    "observed_probe_mode",
    "observed_at",
    "observed_run_id",
    "observed_source",
    "expected_min_height_mm",
    "notes",
    "trust_level",
  ];

  for (const field of fields) {
    appendStateHistoryEntry(sessionState, {
      step,
      field: `liquid_tracking.containers.${key}.${field}`,
      oldValue: before[field] ?? null,
      newValue: after[field] ?? null,
      why,
      trustLevel: after.trust_level,
    });
  }
}

export function setLiquidContainerState(sessionState, container = {}) {
  const tracking = ensureLiquidTracking(sessionState);
  const slotName = normalizeSlotName(container.slot_name || container.slotName);
  const wellName = normalizeWellName(container.well_name || container.wellName);
  const key = liquidContainerKey({
    containerKey: container.container_key || container.containerKey || container.key,
    slotName,
    wellName,
  });
  if (!key) {
    return null;
  }

  const current = tracking.containers[key] || {};
  const explicitTrustLevel = container.trust_level ?? container.trustLevel;
  const inferredTrustLevel =
    explicitTrustLevel ||
    current.trust_level ||
    (container.observed_presence !== undefined || container.observedPresence !== undefined ? "observed" : "declared");
  const next = normalizeLiquidContainerEntry(
    key,
    {
      ...current,
      ...container,
      key,
      container_key: key,
      slot_name: slotName || current.slot_name,
      well_name: wellName || current.well_name,
      role: container.role || container.container_role || container.containerRole || current.role || "unknown",
      labware_load_name: container.labware_load_name ?? container.labwareLoadName ?? current.labware_load_name ?? null,
      liquid_name: container.liquid_name ?? container.liquidName ?? current.liquid_name ?? null,
      sample_id: container.sample_id ?? container.sampleId ?? current.sample_id ?? null,
      liquid_class: container.liquid_class ?? container.liquidClass ?? current.liquid_class ?? null,
      volume_ul: container.volume_ul ?? container.volumeUl ?? current.volume_ul ?? null,
      capacity_ul: container.capacity_ul ?? container.capacityUl ?? current.capacity_ul ?? null,
      dead_volume_ul: container.dead_volume_ul ?? container.deadVolumeUl ?? current.dead_volume_ul ?? null,
      expected_presence: container.expected_presence ?? container.expectedPresence ?? current.expected_presence ?? null,
      observed_presence: container.observed_presence ?? container.observedPresence ?? current.observed_presence ?? null,
      observed_height_mm:
        container.observed_height_mm ?? container.observedHeightMm ?? current.observed_height_mm ?? null,
      observed_probe_mode:
        container.observed_probe_mode ?? container.observedProbeMode ?? current.observed_probe_mode ?? null,
      observed_at: container.observed_at ?? container.observedAt ?? current.observed_at ?? null,
      observed_run_id: container.observed_run_id ?? container.observedRunId ?? current.observed_run_id ?? null,
      observed_source: container.observed_source ?? container.observedSource ?? current.observed_source ?? null,
      expected_min_height_mm:
        container.expected_min_height_mm ?? container.expectedMinHeightMm ?? current.expected_min_height_mm ?? null,
      notes: container.notes ?? current.notes ?? null,
      trust_level: inferredTrustLevel,
      updated_at: new Date().toISOString(),
    },
    {
      defaultRole: container.role || current.role || "unknown",
      defaultTrustLevel: inferredTrustLevel,
    },
  );

  tracking.containers[key] = next;
  sessionState.liquid_tracking = normalizeLiquidTracking(tracking);
  recordContainerFieldChanges(sessionState, {
    key,
    before: current,
    after: next,
    step: container.step || null,
    why: container.why || "set_liquid_container_state",
  });
  return sessionState.liquid_tracking.containers[key];
}

export function setLiquidSourceState(sessionState, source = {}) {
  return setLiquidContainerState(sessionState, {
    ...source,
    role: "source",
    why: source.why || "record_liquid_source_map",
  });
}

function buildViolation(step, code, message, details = {}) {
  return {
    code,
    severity: details.severity || "error",
    message,
    step: normalizeStepForHistory(step),
    ...details,
  };
}

function resolveStepContainerKey(step, names) {
  for (const name of names) {
    const value = step?.[name];
    if (!value) {
      continue;
    }
    if (typeof value === "string") {
      return liquidContainerKey({ containerKey: value });
    }
    const key = liquidContainerKey({
      containerKey: value.container_key || value.containerKey || value.key,
      slotName: value.slot_name || value.slotName,
      wellName: value.well_name || value.wellName,
    });
    if (key) {
      return key;
    }
  }
  return null;
}

function resolveStepVolume(step) {
  return normalizeLiquidNumber(step.volume_ul ?? step.volumeUl ?? step.volume, null);
}

function resolvePipetteId(step) {
  return step.pipette_id || step.pipetteId || step.mount || step.pipette || null;
}

function hasAttachedTip(state, pipetteId) {
  return Boolean(pipetteId && state?.pipettes?.[pipetteId]?.tip_attached === true);
}

function validateContainerCapacity(step, container, violations) {
  if (
    container?.volume_ul !== null &&
    container?.capacity_ul !== null &&
    Number(container.volume_ul) > Number(container.capacity_ul)
  ) {
    violations.push(buildViolation(
      step,
      "liquid_volume_exceeds_capacity",
      `${container.key || "container"} has ${container.volume_ul} uL but capacity is ${container.capacity_ul} uL.`,
      {
        container_key: container.key || container.container_key || null,
        volume_ul: container.volume_ul,
        capacity_ul: container.capacity_ul,
      },
    ));
  }
}

function validateTipPrerequisite(state, step, violations) {
  if (step.requires_tip === false) {
    return;
  }
  const pipetteId = resolvePipetteId(step);
  if (!pipetteId) {
    violations.push(buildViolation(step, "missing_required_field", "Step requires pipette_id for tip policy checks.", {
      field: "pipette_id",
    }));
    return;
  }
  if (!hasAttachedTip(state, pipetteId)) {
    violations.push(buildViolation(step, "missing_attached_tip", `Pipette ${pipetteId} has no attached tip.`, {
      pipette_id: pipetteId,
    }));
  }
}

function setPipetteTipAttached(state, pipetteId, attached, step, why) {
  state.pipettes ||= {};
  const current = state.pipettes[pipetteId] || {};
  appendStateHistoryEntry(state, {
    step,
    field: `pipettes.${pipetteId}.tip_attached`,
    oldValue: current.tip_attached ?? null,
    newValue: attached,
    why,
    trustLevel: "simulated",
  });
  state.pipettes[pipetteId] = {
    ...current,
    tip_attached: attached,
  };
}

export function setContainerVolume(
  state,
  containerKey,
  nextVolumeUl,
  step,
  why,
  trustLevel = "simulated",
  mode = "absolute",
  violations = null,
) {
  const tracking = ensureLiquidTracking(state);
  const container = tracking.containers[containerKey];
  const beforeVolume = container.volume_ul ?? null;
  const beforeTrust = normalizeTrustLevel(container.trust_level, "declared");
  const newTrustLevel = normalizeTrustLevel(trustLevel, "simulated");

  if (mode === "absolute" && !canOverwriteTrust(beforeTrust, newTrustLevel) && step?.force !== true) {
    const violation = buildViolation(
      step,
      "trust_downgrade_blocked",
      `Existing trust=${beforeTrust} cannot be overwritten by ${newTrustLevel}.`,
      {
        container_key: containerKey,
        current_trust: beforeTrust,
        attempted_trust: newTrustLevel,
      },
    );
    if (Array.isArray(violations)) {
      violations.push(violation);
    }
    return container;
  }

  container.volume_ul = normalizeLiquidNumber(nextVolumeUl, null);
  if (mode === "delta") {
    const cappedRank = Math.min(
      TRUST_LEVEL_RANK[beforeTrust] ?? TRUST_LEVEL_RANK.declared,
      TRUST_LEVEL_RANK.simulated,
    );
    container.trust_level = trustLevelFromRank(cappedRank);
  } else {
    container.trust_level = newTrustLevel;
  }
  container.updated_at = new Date().toISOString();
  tracking.containers[containerKey] = container;
  state.liquid_tracking = normalizeLiquidTracking(tracking);

  const historyDerivedFrom = mode === "delta" ? beforeTrust : null;
  appendStateHistoryEntry(state, {
    step,
    field: `liquid_tracking.containers.${containerKey}.volume_ul`,
    oldValue: beforeVolume,
    newValue: container.volume_ul,
    why,
    trustLevel: container.trust_level,
    derivedFrom: historyDerivedFrom,
  });
  appendStateHistoryEntry(state, {
    step,
    field: `liquid_tracking.containers.${containerKey}.trust_level`,
    oldValue: beforeTrust,
    newValue: container.trust_level,
    why,
    trustLevel: container.trust_level,
    derivedFrom: historyDerivedFrom,
  });
  return container;
}

function assertVolumeStepInputs(state, step, { sourceKey = null, targetKey = null, volumeUl = null, strict = false } = {}) {
  const violations = [];
  const tracking = ensureLiquidTracking(state);
  if (volumeUl === null || volumeUl <= 0) {
    violations.push(buildViolation(step, "missing_required_field", "Step requires a positive volume_ul.", {
      field: "volume_ul",
    }));
  }

  const source = sourceKey ? tracking.containers[sourceKey] : null;
  const target = targetKey ? tracking.containers[targetKey] : null;
  if (sourceKey && !source) {
    violations.push(buildViolation(step, "missing_required_prerequisite", `Source container ${sourceKey} is not declared.`, {
      field: "source_key",
      container_key: sourceKey,
    }));
  }
  if (targetKey && !target) {
    violations.push(buildViolation(step, "missing_required_prerequisite", `Target container ${targetKey} is not declared.`, {
      field: "target_key",
      container_key: targetKey,
    }));
  }

  if (source) {
    if (source.volume_ul === null) {
      if (strict) {
        violations.push(buildViolation(step, "missing_required_prerequisite", `Source container ${sourceKey} has no volume_ul.`, {
          field: "source.volume_ul",
          container_key: sourceKey,
        }));
      }
    } else {
      const available = Number(source.volume_ul) - Number(source.dead_volume_ul || 0);
      if (volumeUl !== null && Number(volumeUl) > available) {
        violations.push(buildViolation(
          step,
          "aspirate_exceeds_available_volume",
          `Aspirate ${volumeUl} uL exceeds available source volume ${available} uL after dead volume.`,
          {
            container_key: sourceKey,
            volume_ul: volumeUl,
            available_volume_ul: available,
            dead_volume_ul: source.dead_volume_ul || 0,
          },
        ));
      }
    }
  }

  if (target) {
    if (target.capacity_ul === null) {
      if (strict) {
        violations.push(buildViolation(step, "missing_required_prerequisite", `Target container ${targetKey} has no capacity_ul.`, {
          field: "target.capacity_ul",
          container_key: targetKey,
        }));
      }
    } else {
      const nextVolume = Number(target.volume_ul || 0) + Number(volumeUl || 0);
      if (nextVolume > Number(target.capacity_ul)) {
        violations.push(buildViolation(
          step,
          "liquid_volume_exceeds_capacity",
          `Dispense would leave ${targetKey} at ${nextVolume} uL but capacity is ${target.capacity_ul} uL.`,
          {
            container_key: targetKey,
            volume_ul: nextVolume,
            capacity_ul: target.capacity_ul,
          },
        ));
      }
    }
  }

  return violations;
}

const PURE_NO_OP_STEP_TYPES = new Set([
  "comment",
  "pause",
  "delay",
  "home",
  "drop_tip_in_place",
  "dropTipInPlace",
  "wait_for_temperature",
  "wait_for_temperature_module",
  "set_temperature",
  "setTemperature",
  "thermocycler_set",
  "thermocycler_set_lid_temperature",
  "heater_shaker_set",
  "heater_shaker_deactivate",
  "magnetic_block_engage",
  "magnetic_block_disengage",
  "set_module_state",
  "load_module",
  "loadModule",
]);

const TIP_NO_OP_STEP_TYPES = new Set([
  "air_gap",
  "touch_tip",
  "move_to_addressable_area",
  "moveToAddressableArea",
  "move_to_addressable_area_for_drop_tip",
  "moveToAddressableAreaForDropTip",
]);

function autoDeclareContainer(state, containerKey, role, step) {
  if (!containerKey) {
    return null;
  }
  const tracking = ensureLiquidTracking(state);
  if (tracking.containers[containerKey]) {
    return tracking.containers[containerKey];
  }
  const keyParts = splitContainerKey(containerKey);
  return setLiquidContainerState(state, {
    container_key: containerKey,
    role,
    slot_name: keyParts.slot_name || null,
    well_name: keyParts.well_name || null,
    volume_ul: null,
    capacity_ul: null,
    dead_volume_ul: null,
    trust_level: "declared",
    step,
    why: "auto_declare_container",
  });
}

function autoDeclareEnabled(state, step) {
  return Boolean(step?.auto_declare === true || state?.auto_declare_containers === true);
}

export function applyStep(sessionState, step = {}) {
  const nextState = {
    ...buildDefaultSessionState(sessionState?.session_id || DEFAULT_SESSION_ID),
    ...clone(sessionState || {}),
  };
  nextState.liquid_tracking = normalizeLiquidTracking(nextState.liquid_tracking);
  nextState.state_history = Array.isArray(nextState.state_history) ? nextState.state_history : [];
  const type = String(step.type || step.action || "").trim().toLowerCase();
  const violations = [];

  if (!type) {
    return {
      state: nextState,
      violations: [buildViolation(step, "missing_required_field", "Step requires type.", { field: "type" })],
    };
  }

  if (["declare_container", "set_container", "load_container", "record_liquid_container"].includes(type)) {
    const entry = setLiquidContainerState(nextState, {
      ...step.container,
      ...step,
      role: step.role || step.container_role || step.containerRole || step.container?.role || "unknown",
      step,
      why: step.why || type,
    });
    if (!entry) {
      violations.push(buildViolation(step, "missing_required_field", "Container declaration requires container_key or slot_name + well_name.", {
        field: "container_key",
      }));
    } else {
      validateContainerCapacity(step, entry, violations);
    }
    return { state: nextState, violations };
  }

  if (type === "pick_up_tip") {
    const pipetteId = resolvePipetteId(step);
    const slotName = normalizeSlotName(step.tiprack_slot || step.tiprackSlot || step.slot_name || step.slotName);
    const wellName = normalizeWellName(step.well_name || step.wellName);
    if (!pipetteId) {
      violations.push(buildViolation(step, "missing_required_field", "pick_up_tip requires pipette_id.", { field: "pipette_id" }));
    }
    if (!slotName || !wellName) {
      violations.push(buildViolation(step, "missing_required_field", "pick_up_tip requires tiprack_slot and well_name.", {
        field: "tiprack_slot/well_name",
      }));
    }
    if (pipetteId && hasAttachedTip(nextState, pipetteId)) {
      violations.push(buildViolation(step, "tip_reuse_violation", `Pipette ${pipetteId} already has a tip attached.`, {
        pipette_id: pipetteId,
      }));
    }
    const tiprackState = slotName ? ensureTiprackState(nextState, { slotName }) : null;
    if (tiprackState && wellName) {
      if ((tiprackState.missing_wells || []).includes(wellName)) {
        violations.push(buildViolation(step, "missing_required_prerequisite", `Tip ${slotName}.${wellName} is marked missing.`, {
          tiprack_slot: slotName,
          well_name: wellName,
        }));
      }
      if ((tiprackState.depleted_wells || []).includes(wellName)) {
        violations.push(buildViolation(step, "tip_reuse_violation", `Tip ${slotName}.${wellName} is already depleted.`, {
          tiprack_slot: slotName,
          well_name: wellName,
        }));
      }
    }
    if (violations.length === 0) {
      const beforeDepleted = [...(tiprackState.depleted_wells || [])];
      markTipWellStatus(nextState, { slotName, wellName, status: "depleted" });
      appendStateHistoryEntry(nextState, {
        step,
        field: `tip_tracking.tipracks.${slotName}.depleted_wells`,
        oldValue: beforeDepleted,
        newValue: nextState.tip_tracking.tipracks[slotName].depleted_wells,
        why: "pick_up_tip",
        trustLevel: "simulated",
      });
      setPipetteTipAttached(nextState, pipetteId, true, step, "pick_up_tip");
    }
    return { state: nextState, violations };
  }

  if (type === "drop_tip") {
    const pipetteId = resolvePipetteId(step);
    if (!pipetteId) {
      violations.push(buildViolation(step, "missing_required_field", "drop_tip requires pipette_id.", { field: "pipette_id" }));
    } else if (!hasAttachedTip(nextState, pipetteId)) {
      violations.push(buildViolation(step, "missing_attached_tip", `Pipette ${pipetteId} has no attached tip to drop.`, {
        pipette_id: pipetteId,
      }));
    }
    if (violations.length === 0) {
      setPipetteTipAttached(nextState, pipetteId, false, step, "drop_tip");
    }
    return { state: nextState, violations };
  }

  if (["aspirate", "dispense", "transfer"].includes(type)) {
    validateTipPrerequisite(nextState, step, violations);
    const volumeUl = resolveStepVolume(step);
    const sourceKey = type === "dispense"
      ? null
      : resolveStepContainerKey(step, ["source_key", "sourceKey", "source", "from", "container_key", "containerKey"]);
    const targetKey = type === "aspirate"
      ? null
      : resolveStepContainerKey(step, ["target_key", "targetKey", "destination_key", "destinationKey", "destination", "dest", "to", "container_key", "containerKey"]);

    if (type !== "dispense" && !sourceKey) {
      violations.push(buildViolation(step, "missing_required_field", `${type} requires source_key.`, { field: "source_key" }));
    }
    if (type !== "aspirate" && !targetKey) {
      violations.push(buildViolation(step, "missing_required_field", `${type} requires target_key.`, { field: "target_key" }));
    }

    if (autoDeclareEnabled(nextState, step)) {
      if (sourceKey) {
        autoDeclareContainer(nextState, sourceKey, "source", step);
      }
      if (targetKey) {
        autoDeclareContainer(nextState, targetKey, "destination", step);
      }
    }

    violations.push(
      ...assertVolumeStepInputs(nextState, step, {
        sourceKey,
        targetKey,
        volumeUl,
        strict: step.strict_volumes === true,
      }),
    );
    if (violations.length === 0) {
      const tracking = ensureLiquidTracking(nextState);
      const trustLevel = step.trust_level || step.trustLevel || "simulated";
      if (sourceKey) {
        const source = tracking.containers[sourceKey];
        if (source && source.volume_ul !== null) {
          setContainerVolume(nextState, sourceKey, Number(source.volume_ul) - volumeUl, step, `${type}:aspirate`, trustLevel, "delta", violations);
        }
      }
      if (targetKey) {
        const target = ensureLiquidTracking(nextState).containers[targetKey];
        if (target && target.volume_ul !== null) {
          setContainerVolume(nextState, targetKey, Number(target.volume_ul) + volumeUl, step, `${type}:dispense`, trustLevel, "delta", violations);
        }
      }
    }
    return { state: nextState, violations };
  }

  if (type === "mix") {
    validateTipPrerequisite(nextState, step, violations);
    const volumeUl = resolveStepVolume(step);
    const sourceKey = resolveStepContainerKey(step, ["source_key", "sourceKey", "source", "container_key", "containerKey", "from"]);
    if (!sourceKey) {
      violations.push(buildViolation(step, "missing_required_field", "mix requires source_key.", { field: "source_key" }));
    }
    if (autoDeclareEnabled(nextState, step) && sourceKey) {
      autoDeclareContainer(nextState, sourceKey, "source", step);
    }
    violations.push(
      ...assertVolumeStepInputs(nextState, step, {
        sourceKey,
        targetKey: null,
        volumeUl,
        strict: step.strict_volumes === true,
      }),
    );
    // mix aspirates and dispenses back into the same well: no net volume change, so no state mutation.
    return { state: nextState, violations };
  }

  if (type === "blow_out") {
    validateTipPrerequisite(nextState, step, violations);
    const volumeUl = resolveStepVolume(step) ?? 0;
    const targetKey = resolveStepContainerKey(step, ["target_key", "targetKey", "destination_key", "destinationKey", "destination", "dest", "to", "container_key", "containerKey"]);
    if (!targetKey) {
      violations.push(buildViolation(step, "missing_required_field", "blow_out requires target_key.", { field: "target_key" }));
    }
    if (autoDeclareEnabled(nextState, step) && targetKey) {
      autoDeclareContainer(nextState, targetKey, "destination", step);
    }
    violations.push(
      ...assertVolumeStepInputs(nextState, step, {
        sourceKey: null,
        targetKey,
        volumeUl,
        strict: step.strict_volumes === true,
      }),
    );
    if (violations.length === 0 && volumeUl > 0) {
      const target = ensureLiquidTracking(nextState).containers[targetKey];
      if (target && target.volume_ul !== null) {
        setContainerVolume(nextState, targetKey, Number(target.volume_ul) + volumeUl, step, "blow_out:dispense", "simulated", "delta", violations);
      }
    }
    return { state: nextState, violations };
  }

  if (type === "load_labware" || type === "loadLabware") {
    const slotName = normalizeSlotName(step.slot_name || step.slotName || step.slot);
    const loadName = step.load_name || step.loadName || step.labware_load_name || null;
    if (!slotName) {
      violations.push(buildViolation(step, "missing_required_field", "load_labware requires slot_name.", { field: "slot_name" }));
    } else {
      setDeckSlotState(nextState, slotName, {
        slot_name: slotName,
        occupant_type: "labware",
        occupant_name: loadName,
        observed_status: "declared",
        addressable: true,
      });
      appendStateHistoryEntry(nextState, {
        step,
        field: `deck.slots.${slotName}`,
        oldValue: null,
        newValue: { occupant_name: loadName },
        why: "load_labware",
        trustLevel: "declared",
      });
    }
    return { state: nextState, violations };
  }

  if (type === "load_pipette" || type === "loadPipette") {
    const pipetteId = resolvePipetteId(step);
    const pipetteName = step.pipette_name || step.pipetteName || step.instrument_name || null;
    if (!pipetteId) {
      violations.push(buildViolation(step, "missing_required_field", "load_pipette requires pipette_id.", { field: "pipette_id" }));
    } else {
      setPipetteState(nextState, pipetteId, {
        ...(nextState.pipettes?.[pipetteId] || {}),
        instrument_name: pipetteName,
        tip_attached: nextState.pipettes?.[pipetteId]?.tip_attached ?? false,
      });
      appendStateHistoryEntry(nextState, {
        step,
        field: `pipettes.${pipetteId}.instrument_name`,
        oldValue: null,
        newValue: pipetteName,
        why: "load_pipette",
        trustLevel: "declared",
      });
    }
    return { state: nextState, violations };
  }

  if (PURE_NO_OP_STEP_TYPES.has(type)) {
    return { state: nextState, violations };
  }

  if (TIP_NO_OP_STEP_TYPES.has(type)) {
    if (step.requires_tip !== false) {
      validateTipPrerequisite(nextState, step, violations);
    }
    return { state: nextState, violations };
  }

  return {
    state: nextState,
    violations: [buildViolation(step, "unsupported_step_type", `Unsupported Virtual Lab State step type: ${type}.`, {
      step_type: type,
    })],
  };
}

export function validateVirtualLabStateSteps(sessionState, steps = []) {
  const allViolations = [];
  let currentState = {
    ...buildDefaultSessionState(sessionState?.session_id || DEFAULT_SESSION_ID),
    ...clone(sessionState || {}),
  };
  currentState.liquid_tracking = normalizeLiquidTracking(currentState.liquid_tracking);
  currentState.state_history = Array.isArray(currentState.state_history) ? currentState.state_history : [];

  for (const [index, step] of (Array.isArray(steps) ? steps : []).entries()) {
    const result = applyStep(currentState, step);
    currentState = result.state;
    allViolations.push(...result.violations.map(violation => ({ ...violation, step_index: index })));
  }

  return {
    state: currentState,
    violations: allViolations,
    ok: allViolations.length === 0,
  };
}
