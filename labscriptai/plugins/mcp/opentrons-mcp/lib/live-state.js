import { normalizeLiquidTracking } from "./state.js";
import { parseProtocolDeckLabware } from "./protocol-liquid-sources.js";

const CONTACT_CLASSES = new Set(["clean", "sample", "stock", "waste"]);
const WELL_ROLES = new Set(["sample", "common_stock", "waste", "unknown"]);
const SAMPLE_CONTACT_COMMANDS = new Set([
  "aspirate",
  "liquidProbe",
  "requireLiquidPresence",
  "require_liquid_presence",
]);

function unwrapData(payload) {
  if (payload && typeof payload === "object" && "data" in payload) {
    return payload.data;
  }
  return payload;
}

function asArray(value) {
  if (Array.isArray(value)) {
    return value;
  }
  if (value && typeof value === "object") {
    return Object.values(value);
  }
  return [];
}

function unwrapCommandList(commands) {
  if (!commands) {
    return [];
  }
  if (Array.isArray(commands)) {
    return commands;
  }
  if (commands && typeof commands === "object" && "data" in commands) {
    const inner = commands.data;
    if (Array.isArray(inner)) {
      return inner;
    }
    if (inner && typeof inner === "object" && Array.isArray(inner.data)) {
      return inner.data;
    }
  }
  return [];
}

function normalizeUpper(value) {
  const text = String(value || "").trim().toUpperCase();
  return text || null;
}

function liquidKey(slotName, wellName) {
  const slot = normalizeUpper(slotName);
  const well = normalizeUpper(wellName);
  return slot && well ? `${slot}.${well}` : null;
}

function inferRoleFromLabwareLoadName(loadName = "") {
  const name = String(loadName || "").toLowerCase();
  if (!name) {
    return null;
  }
  if (name.includes("trash")) {
    return "waste";
  }
  if (name.includes("reservoir")) {
    return "common_stock";
  }
  if (name.includes("wellplate") || name.includes("plate")) {
    return "sample";
  }
  return null;
}

/**
 * Resolve a well role for tip-contact tracking.
 * Priority: session liquid source map role (contract vocabulary) >
 * protocol/labware inference (reservoir→common_stock, plate→sample, trash→waste) >
 * "unknown".
 */
export function resolveWellRole({
  slotName = null,
  wellName = null,
  sourceKey = null,
  sessionState = null,
  protocolSource = "",
  labwareLoadName = null,
} = {}) {
  const key = sourceKey || liquidKey(slotName, wellName);
  const sources = sessionState?.liquid_tracking?.sources || {};
  const containers = sessionState?.liquid_tracking?.containers || {};
  const entry = (key && (sources[key] || containers[key])) || null;
  const sessionRole = String(entry?.role || "").trim().toLowerCase();
  if (WELL_ROLES.has(sessionRole)) {
    return sessionRole;
  }

  const deckLabware = parseProtocolDeckLabware(protocolSource || "");
  const slot = normalizeUpper(slotName) || (key ? key.split(".")[0] : null);
  const inferred =
    inferRoleFromLabwareLoadName(labwareLoadName) ||
    inferRoleFromLabwareLoadName(entry?.labware_load_name) ||
    inferRoleFromLabwareLoadName(slot ? deckLabware[slot] : null);
  return inferred || "unknown";
}

/**
 * Build slot.well → role map from session + protocol deck hints + run labware.
 */
export function buildWellRoleMap({
  sessionState = null,
  protocolSource = "",
  run = null,
} = {}) {
  const roles = {};
  const tracking = normalizeLiquidTracking(sessionState?.liquid_tracking || {});
  for (const [key, entry] of Object.entries(tracking.containers || {})) {
    roles[key] = resolveWellRole({
      sourceKey: key,
      slotName: entry.slot_name,
      wellName: entry.well_name,
      sessionState,
      protocolSource,
      labwareLoadName: entry.labware_load_name,
    });
  }

  const deckLabware = parseProtocolDeckLabware(protocolSource || "");
  for (const [slot, loadName] of Object.entries(deckLabware)) {
    const role = inferRoleFromLabwareLoadName(loadName) || "unknown";
    // Slot-level default used when a command only names slot.well later.
    roles[`${slot}.*`] = role;
  }

  const runData = unwrapData(run) || {};
  for (const labware of asArray(runData.labware || runData.labwareById)) {
    const slot = normalizeUpper(
      labware?.location?.slotName || labware?.slotName || labware?.slot || null,
    );
    const loadName = labware?.loadName || labware?.load_name || labware?.definitionUri || "";
    if (slot) {
      roles[`${slot}.*`] = inferRoleFromLabwareLoadName(loadName) || roles[`${slot}.*`] || "unknown";
    }
  }

  return roles;
}

function roleForCommandTarget(command, wellRoles = {}, labwareById = {}) {
  const params = command?.params || {};
  const wellName = normalizeUpper(params.wellName || params.well_name);
  const labwareId = params.labwareId || params.labware_id || null;
  const labware = labwareId ? labwareById[labwareId] : null;
  const slot = normalizeUpper(
    labware?.location?.slotName || labware?.slotName || params.slotName || params.slot_name || null,
  );
  const key = liquidKey(slot, wellName);
  if (key && wellRoles[key]) {
    return wellRoles[key];
  }
  if (slot && wellRoles[`${slot}.*`]) {
    return wellRoles[`${slot}.*`];
  }
  return resolveWellRole({
    slotName: slot,
    wellName,
    labwareLoadName: labware?.loadName || labware?.load_name || null,
  });
}

function contactClassFromWellRole(role) {
  if (role === "sample") {
    return "sample";
  }
  if (role === "common_stock") {
    return "stock";
  }
  if (role === "waste") {
    return "waste";
  }
  return null;
}

/**
 * Derive per-mount tip contact_class from command history.
 * Any aspirate / liquidProbe / require_liquid_presence against a sample well
 * marks the tip "sample". A new pickUpTip resets to "clean". State only —
 * no JS-side interception.
 */
export function deriveInstrumentContactClasses({
  instruments = [],
  commands = null,
  wellRoles = {},
  run = null,
} = {}) {
  const runData = unwrapData(run) || {};
  const labwareById = {};
  for (const labware of asArray(runData.labware || [])) {
    if (labware?.id) {
      labwareById[labware.id] = labware;
    }
  }

  const byMount = {};
  for (const instrument of asArray(instruments)) {
    const mount = instrument?.mount;
    if (mount) {
      byMount[mount] = "clean";
    }
  }

  // Fallback single-channel tracking when mount is absent on commands.
  let fallbackContact = "clean";

  for (const command of unwrapCommandList(commands)) {
    const type = String(command?.commandType || command?.command_type || "");
    const status = String(command?.status || "").toLowerCase();
    if (status && status !== "succeeded" && status !== "running") {
      // Still count failed liquidProbe as contact for contamination tracking.
      if (!(SAMPLE_CONTACT_COMMANDS.has(type) && status === "failed")) {
        continue;
      }
    }

    const pipetteId = command?.params?.pipetteId || command?.params?.pipette_id || null;
    const mount =
      (pipetteId && asArray(instruments).find(item => item.id === pipetteId || item.pipette_id === pipetteId)?.mount) ||
      Object.keys(byMount)[0] ||
      null;

    if (type === "pickUpTip") {
      if (mount && byMount[mount] !== undefined) {
        byMount[mount] = "clean";
      }
      fallbackContact = "clean";
      continue;
    }

    if (type === "dropTip" || type === "dropTipInPlace") {
      if (mount && byMount[mount] !== undefined) {
        byMount[mount] = "clean";
      }
      fallbackContact = "clean";
      continue;
    }

    if (!SAMPLE_CONTACT_COMMANDS.has(type)) {
      continue;
    }

    const role = roleForCommandTarget(command, wellRoles, labwareById);
    const contact = contactClassFromWellRole(role);
    if (!contact) {
      continue;
    }
    if (mount && byMount[mount] !== undefined) {
      byMount[mount] = contact;
    }
    fallbackContact = contact;
  }

  return asArray(instruments).map(instrument => {
    const mount = instrument?.mount;
    const contactClass = (mount && byMount[mount]) || fallbackContact || "clean";
    return {
      ...instrument,
      contact_class: CONTACT_CLASSES.has(contactClass) ? contactClass : "clean",
    };
  });
}

function readNested(value, candidates, fallback = null) {
  for (const candidate of candidates) {
    let current = value;
    let found = true;
    for (const part of candidate) {
      if (current && typeof current === "object" && part in current) {
        current = current[part];
      } else {
        found = false;
        break;
      }
    }
    if (found && current !== undefined) {
      return current;
    }
  }
  return fallback;
}

function normalizeBool(value) {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    const normalized = value.toLowerCase();
    if (["true", "open", "engaged", "pressed", "on"].includes(normalized)) {
      return true;
    }
    if (["false", "closed", "disengaged", "released", "off"].includes(normalized)) {
      return false;
    }
  }
  return null;
}

function summarizeHealth(healthPayload) {
  const health = unwrapData(healthPayload) || {};
  return {
    name: readNested(health, [["name"]]),
    robot_model: readNested(health, [["robot_model"], ["robotModel"]]),
    robot_serial: readNested(health, [["robot_serial"], ["robotSerial"]]),
    api_version: readNested(health, [["api_version"], ["apiVersion"]]),
    firmware_version: readNested(health, [["fw_version"], ["fwVersion"]]),
    system_version: readNested(health, [["system_version"], ["systemVersion"]]),
  };
}

function summarizeInstruments(instrumentsPayload) {
  const instruments = asArray(unwrapData(instrumentsPayload));
  return instruments.map(instrument => {
    const ok = readNested(instrument, [["ok"], ["data", "ok"]], null);
    return {
      mount: readNested(instrument, [["mount"]]),
      instrument_name: readNested(instrument, [["instrumentName"], ["name"], ["model"]]),
      model: readNested(instrument, [["model"], ["instrumentModel"]]),
      serial: readNested(instrument, [["serialNumber"], ["serial"]]),
      ok,
      tip_detected: readNested(
        instrument,
        [["tipDetected"], ["data", "tipDetected"], ["pipette", "tipDetected"], ["state", "tipDetected"]],
        null,
      ),
      contact_class: "clean",
      raw_status: readNested(instrument, [["status"], ["data", "status"], ["state", "jawState"], ["data", "jawState"]]),
    };
  });
}

function summarizeDoor(doorPayload) {
  const door = unwrapData(doorPayload) || {};
  const rawStatus = readNested(door, [["status"], ["doorStatus"]], null);
  const open =
    normalizeBool(rawStatus) ??
    normalizeBool(readNested(door, [["open"]])) ??
    (typeof rawStatus === "string" ? rawStatus.toLowerCase() === "open" : null);
  return {
    status: rawStatus,
    open,
  };
}

function summarizeEstop(estopPayload) {
  const estop = unwrapData(estopPayload) || {};
  const rawStatus = readNested(estop, [["status"], ["estopStatus"]], null);
  const engaged =
    normalizeBool(rawStatus) ??
    normalizeBool(readNested(estop, [["engaged"]])) ??
    (typeof rawStatus === "string"
      ? ["engaged", "pressed", "triggered"].includes(rawStatus.toLowerCase())
      : null);
  return {
    status: rawStatus,
    engaged,
  };
}

function summarizeDeck(deckPayload) {
  const deck = unwrapData(deckPayload) || {};
  return {
    deck_type: readNested(deck, [["deckType"], ["type"]]),
    cutout_fixtures: readNested(deck, [["cutoutFixtures"], ["fixtures"]], []),
    raw: deck,
  };
}

export function buildRobotStatusSnapshot({
  health,
  instruments,
  doorStatus,
  estopStatus,
  deckConfiguration,
  commands = null,
  sessionState = null,
  protocolSource = "",
  run = null,
}) {
  const healthSummary = summarizeHealth(health);
  let instrumentSummary = summarizeInstruments(instruments);
  const doorSummary = summarizeDoor(doorStatus);
  const estopSummary = summarizeEstop(estopStatus);
  const deckSummary = summarizeDeck(deckConfiguration);
  const wellRoles = buildWellRoleMap({ sessionState, protocolSource, run });

  if (commands) {
    instrumentSummary = deriveInstrumentContactClasses({
      instruments: instrumentSummary,
      commands,
      wellRoles,
      run,
    });
  }

  const blockers = [];
  if (doorSummary.open === true) {
    blockers.push("door_open");
  }
  if (estopSummary.engaged === true) {
    blockers.push("estop_engaged");
  }
  if (instrumentSummary.some(instrument => instrument.ok === false)) {
    blockers.push("instrument_not_ready");
  }

  const wellsSummary = Object.entries(wellRoles)
    .filter(([key]) => !key.endsWith(".*"))
    .map(([key, role]) => {
      const [slot_name, well_name] = key.split(".");
      return { key, slot_name, well_name, role };
    });

  return {
    robot_reachable: true,
    health_summary: healthSummary,
    instruments_summary: instrumentSummary,
    wells_summary: wellsSummary,
    well_roles: wellRoles,
    door: doorSummary,
    estop: estopSummary,
    deck_configuration: deckSummary,
    ready_for_physical_action: blockers.length === 0,
    blockers,
  };
}

function normalizeModule(module) {
  const data = module || {};
  const currentTemp =
    readNested(data, [["currentTemperature"], ["data", "currentTemperature"]]) ?? null;
  const targetTemp =
    readNested(data, [["targetTemperature"], ["data", "targetTemperature"]]) ?? null;
  const currentSpeed =
    readNested(data, [["currentSpeed"], ["data", "currentSpeed"]]) ?? null;
  const targetSpeed =
    readNested(data, [["targetSpeed"], ["data", "targetSpeed"]]) ?? null;
  const currentLidTemp =
    readNested(data, [["currentLidTemperature"], ["data", "currentLidTemperature"]]) ?? null;
  const targetLidTemp =
    readNested(data, [["targetLidTemperature"], ["data", "targetLidTemperature"]]) ?? null;
  const rawStatus = readNested(
    data,
    [["status"], ["moduleStatus"], ["data", "status"]],
    null,
  );
  const lowerStatus =
    typeof rawStatus === "string" ? rawStatus.toLowerCase() : String(rawStatus || "");

  const thermalReady =
    targetTemp == null ||
    currentTemp == null ||
    Math.abs(Number(currentTemp) - Number(targetTemp)) < 0.5;
  const speedReady =
    targetSpeed == null ||
    currentSpeed == null ||
    Number(currentSpeed) === Number(targetSpeed);
  const statusReady =
    !rawStatus ||
    ["idle", "holding at target", "engaged", "disengaged", "ready", "steady"].some(
      token => lowerStatus.includes(token),
    );

  return {
    id: readNested(data, [["id"], ["moduleId"], ["serialNumber"], ["serial"]]),
    serial: readNested(data, [["serialNumber"], ["serial"]]),
    model: readNested(data, [["moduleModel"], ["model"], ["moduleType"]]),
    module_type: readNested(data, [["moduleType"], ["moduleModel"], ["model"]]),
    slot: readNested(data, [["location", "slotName"], ["moduleOffset", "slot"], ["slot"], ["data", "slot"]]),
    status: rawStatus,
    current_temperature: currentTemp,
    target_temperature: targetTemp,
    temperature_status: readNested(data, [["temperatureStatus"], ["data", "temperatureStatus"]], null),
    current_speed: currentSpeed,
    target_speed: targetSpeed,
    speed_status: readNested(data, [["speedStatus"], ["data", "speedStatus"]], null),
    current_lid_temperature: currentLidTemp,
    target_lid_temperature: targetLidTemp,
    lid_status: readNested(data, [["lidStatus"], ["data", "lidStatus"]], null),
    labware_latch_status: readNested(data, [["labwareLatchStatus"], ["data", "labwareLatchStatus"]], null),
    magnetic_engaged: readNested(
      data,
      [["magneticEngaged"], ["engaged"], ["data", "engaged"]],
      null,
    ),
    ready: Boolean(thermalReady && speedReady && statusReady),
  };
}

export function buildModuleStatusSnapshot(modulesPayload) {
  const modules = asArray(unwrapData(modulesPayload)).map(normalizeModule);
  const blockers = modules
    .filter(module => module.ready === false)
    .map(module => `module_not_ready:${module.id || module.slot || module.model || "unknown"}`);

  return {
    modules,
    module_count: modules.length,
    ready_module_count: modules.filter(module => module.ready).length,
    blockers,
  };
}

function summarizeCommand(command) {
  const data = unwrapData(command) || {};
  const rawError = readNested(data, [["error"]], null);
  const errorDetail = readNested(data, [["error", "detail"], ["error", "message"]], null);
  const errorType = readNested(data, [["error", "errorType"], ["error", "type"]], null);
  const error =
    rawError && typeof rawError === "object"
      ? {
          ...rawError,
          errorType: errorType || rawError.errorType || rawError.type || null,
          detail: errorDetail || rawError.detail || rawError.message || null,
        }
      : errorDetail;
  return {
    id: readNested(data, [["id"]]),
    command_type: readNested(data, [["commandType"], ["command_type"]]),
    key: readNested(data, [["key"]]),
    status: readNested(data, [["status"]]),
    created_at: readNested(data, [["createdAt"], ["created_at"]]),
    completed_at: readNested(data, [["completedAt"], ["completed_at"]]),
    error,
  };
}

export function buildRunHistorySnapshot(runPayload, commandsPayload) {
  const run = unwrapData(runPayload) || {};
  const commands = asArray(unwrapData(commandsPayload)).map(summarizeCommand);
  const latestFailedCommand = commands.findLast
    ? commands.findLast(command => command.status === "failed")
    : [...commands].reverse().find(command => command.status === "failed");
  const latestRunningCommand = commands.findLast
    ? commands.findLast(command => command.status === "running")
    : [...commands].reverse().find(command => command.status === "running");

  const runStatus = readNested(run, [["status"]]);
  const awaitingRecovery =
    runStatus === "awaiting-recovery" ||
    Boolean(readNested(run, [["currentlyRecoveringFrom"]], null));

  return {
    run_id: readNested(run, [["id"]]),
    protocol_id: readNested(run, [["protocolId"], ["protocol_id"]]),
    status: runStatus,
    current_recovery_target: readNested(run, [["currentlyRecoveringFrom"]], null),
    awaiting_recovery: awaitingRecovery,
    has_ever_entered_error_recovery: readNested(
      run,
      [["hasEverEnteredErrorRecovery"]],
      null,
    ),
    command_counts: {
      total: commands.length,
      succeeded: commands.filter(command => command.status === "succeeded").length,
      failed: commands.filter(command => command.status === "failed").length,
      running: commands.filter(command => command.status === "running").length,
      queued: commands.filter(command => command.status === "queued").length,
    },
    latest_failed_command: latestFailedCommand || null,
    latest_running_command: latestRunningCommand || null,
    recent_commands: commands.slice(-10),
    command_errors: asArray(readNested(run, [["commandErrors"], ["errors"]], [])).map(error => ({
      id: readNested(error, [["id"]], null),
      created_at: readNested(error, [["createdAt"], ["created_at"]], null),
      detail: readNested(error, [["detail"], ["error", "detail"]], null),
      error_type: readNested(error, [["errorType"], ["error_type"]], null),
    })),
  };
}

export function buildLiquidTrackingSnapshot(sessionState = {}, { protocolSource = "" } = {}) {
  const tracking = normalizeLiquidTracking(sessionState.liquid_tracking || {});
  const containers = Object.values(tracking.containers || {});
  const overCapacity = containers.filter(
    container =>
      container.volume_ul !== null &&
      container.capacity_ul !== null &&
      Number(container.volume_ul) > Number(container.capacity_ul),
  );
  const belowDeadVolume = containers.filter(
    container =>
      container.volume_ul !== null &&
      container.dead_volume_ul !== null &&
      Number(container.volume_ul) < Number(container.dead_volume_ul),
  );
  const byTrustLevel = containers.reduce((acc, container) => {
    const trustLevel = container.trust_level || "declared";
    acc[trustLevel] = (acc[trustLevel] || 0) + 1;
    return acc;
  }, {});

  const containersWithRole = Object.fromEntries(
    containers.map(container => {
      const wellRole = resolveWellRole({
        sourceKey: container.key,
        slotName: container.slot_name,
        wellName: container.well_name,
        sessionState,
        protocolSource,
        labwareLoadName: container.labware_load_name,
      });
      return [container.key, { ...container, well_role: wellRole }];
    }),
  );

  return {
    container_count: containers.length,
    source_count: Object.keys(tracking.sources || {}).length,
    containers: containersWithRole,
    by_trust_level: byTrustLevel,
    incomplete_volume_count: containers.filter(container => container.volume_ul === null).length,
    over_capacity_count: overCapacity.length,
    over_capacity_containers: overCapacity.map(container => container.key),
    below_dead_volume_count: belowDeadVolume.length,
    below_dead_volume_containers: belowDeadVolume.map(container => container.key),
    state_history_count: Array.isArray(sessionState.state_history) ? sessionState.state_history.length : 0,
  };
}
