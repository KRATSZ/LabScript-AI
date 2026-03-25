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
}) {
  const healthSummary = summarizeHealth(health);
  const instrumentSummary = summarizeInstruments(instruments);
  const doorSummary = summarizeDoor(doorStatus);
  const estopSummary = summarizeEstop(estopStatus);
  const deckSummary = summarizeDeck(deckConfiguration);

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

  return {
    robot_reachable: true,
    health_summary: healthSummary,
    instruments_summary: instrumentSummary,
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
  const errorDetail = readNested(data, [["error", "detail"], ["error", "message"]], null);
  return {
    id: readNested(data, [["id"]]),
    command_type: readNested(data, [["commandType"], ["command_type"]]),
    key: readNested(data, [["key"]]),
    status: readNested(data, [["status"]]),
    created_at: readNested(data, [["createdAt"], ["created_at"]]),
    completed_at: readNested(data, [["completedAt"], ["completed_at"]]),
    error: errorDetail,
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
