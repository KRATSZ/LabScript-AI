export const CONTEXT_TYPES = {
  PROTOCOL: "protocol",
  MAINTENANCE: "maintenance",
};

export function normalizeContextType(contextType, { protocolId = null } = {}) {
  if (contextType === CONTEXT_TYPES.MAINTENANCE) {
    return CONTEXT_TYPES.MAINTENANCE;
  }
  if (contextType === CONTEXT_TYPES.PROTOCOL || protocolId) {
    return CONTEXT_TYPES.PROTOCOL;
  }
  return CONTEXT_TYPES.MAINTENANCE;
}

export function buildCreateRunContextRequest({
  contextType,
  protocolId = null,
  runTimeParameters = null,
  labwareOffsets = null,
} = {}) {
  const normalizedContextType = normalizeContextType(contextType, { protocolId });
  if (normalizedContextType === CONTEXT_TYPES.PROTOCOL && !protocolId) {
    throw new Error("protocol_id is required when context_type is protocol.");
  }

  const data =
    normalizedContextType === CONTEXT_TYPES.PROTOCOL
      ? {
          protocolId,
          ...(runTimeParameters ? { runTimeParameterValues: runTimeParameters } : {}),
          ...(labwareOffsets ? { labwareOffsets } : {}),
        }
      : {
          ...(labwareOffsets ? { labwareOffsets } : {}),
        };

  return {
    contextType: normalizedContextType,
    path: normalizedContextType === CONTEXT_TYPES.PROTOCOL ? "/runs" : "/maintenance_runs",
    body: {
      data,
    },
  };
}

export function buildContextPaths(contextType, contextId) {
  const normalizedContextType = normalizeContextType(contextType);
  const basePath =
    normalizedContextType === CONTEXT_TYPES.PROTOCOL
      ? `/runs/${contextId}`
      : `/maintenance_runs/${contextId}`;

  return {
    contextType: normalizedContextType,
    detailPath: basePath,
    commandsPath: `${basePath}/commands`,
    commandPath: commandId => `${basePath}/commands/${commandId}`,
    actionsPath: normalizedContextType === CONTEXT_TYPES.PROTOCOL ? `${basePath}/actions` : null,
  };
}

export function buildCommandPayload({
  commandType,
  params = {},
  intent = null,
  key = null,
} = {}) {
  if (!commandType) {
    throw new Error("commandType is required.");
  }

  return {
    data: {
      commandType,
      params,
      ...(intent ? { intent } : {}),
      ...(key ? { key } : {}),
    },
  };
}

export function isTerminalCommandStatus(status) {
  return ["succeeded", "failed"].includes(String(status || "").toLowerCase());
}

export function buildLoadPipetteCommand({
  pipetteName,
  mount,
  pipetteId = null,
  tipOverlapNotAfterVersion = null,
  liquidPresenceDetection = null,
  intent = "setup",
  key = null,
} = {}) {
  return buildCommandPayload({
    commandType: "loadPipette",
    intent,
    key,
    params: {
      pipetteName,
      mount,
      ...(pipetteId ? { pipetteId } : {}),
      ...(tipOverlapNotAfterVersion ? { tipOverlapNotAfterVersion } : {}),
      ...(typeof liquidPresenceDetection === "boolean"
        ? { liquidPresenceDetection }
        : {}),
    },
  });
}

export function buildLoadLabwareCommand({
  location,
  loadName,
  namespace,
  version,
  labwareId = null,
  displayName = null,
  intent = "setup",
  key = null,
} = {}) {
  return buildCommandPayload({
    commandType: "loadLabware",
    intent,
    key,
    params: {
      location,
      loadName,
      namespace,
      version,
      ...(labwareId ? { labwareId } : {}),
      ...(displayName ? { displayName } : {}),
    },
  });
}

export function buildLoadModuleCommand({
  model,
  location,
  moduleId = null,
  intent = "setup",
  key = null,
} = {}) {
  return buildCommandPayload({
    commandType: "loadModule",
    intent,
    key,
    params: {
      model,
      location,
      ...(moduleId ? { moduleId } : {}),
    },
  });
}

export function buildMoveLabwareCommand({
  labwareId,
  newLocation,
  strategy = "usingGripper",
  pickUpOffset = null,
  dropOffset = null,
  intent = null,
  key = null,
} = {}) {
  return buildCommandPayload({
    commandType: "moveLabware",
    intent,
    key,
    params: {
      labwareId,
      newLocation,
      strategy,
      ...(pickUpOffset ? { pickUpOffset } : {}),
      ...(dropOffset ? { dropOffset } : {}),
    },
  });
}

export function buildTemperatureModuleCommand({
  action,
  moduleId,
  celsius = null,
  intent = "setup",
  key = null,
} = {}) {
  const commandTypeByAction = {
    set_target_temperature: "temperatureModule/setTargetTemperature",
    wait_for_temperature: "temperatureModule/waitForTemperature",
    deactivate: "temperatureModule/deactivate",
  };
  const commandType = commandTypeByAction[action];
  if (!commandType) {
    throw new Error(`Unsupported temperature module action: ${action}`);
  }
  return buildCommandPayload({
    commandType,
    intent,
    key,
    params: {
      moduleId,
      ...(typeof celsius === "number" ? { celsius } : {}),
    },
  });
}

export function buildHeaterShakerCommand({
  action,
  moduleId,
  celsius = null,
  rpm = null,
  intent = "setup",
  key = null,
} = {}) {
  const commandTypeByAction = {
    set_target_temperature: "heaterShaker/setTargetTemperature",
    wait_for_temperature: "heaterShaker/waitForTemperature",
    deactivate_heater: "heaterShaker/deactivateHeater",
    set_shake_speed: "heaterShaker/setShakeSpeed",
    set_and_wait_for_shake_speed: "heaterShaker/setAndWaitForShakeSpeed",
    deactivate_shaker: "heaterShaker/deactivateShaker",
    open_labware_latch: "heaterShaker/openLabwareLatch",
    close_labware_latch: "heaterShaker/closeLabwareLatch",
  };
  const commandType = commandTypeByAction[action];
  if (!commandType) {
    throw new Error(`Unsupported heater-shaker action: ${action}`);
  }
  return buildCommandPayload({
    commandType,
    intent,
    key,
    params: {
      moduleId,
      ...(typeof celsius === "number" ? { celsius } : {}),
      ...(typeof rpm === "number" ? { rpm } : {}),
    },
  });
}

export function isHeaterShakerLatchClosed(latchStatus) {
  const normalized = String(latchStatus || "").trim().toLowerCase();
  return normalized.includes("closed");
}

export function shouldPreflightCloseHeaterShakerLatch({
  action,
  latchStatus = null,
  ensureLatchClosed = true,
} = {}) {
  if (action !== "deactivate_shaker" || ensureLatchClosed === false) {
    return false;
  }
  return !isHeaterShakerLatchClosed(latchStatus);
}

export function shouldRetryHeaterShakerAfterLatchError(errorDetail) {
  const normalized = String(errorDetail || "").toLowerCase();
  return (
    normalized.includes("cannotperformmoduleaction") &&
    normalized.includes("latch") &&
    normalized.includes("closed")
  );
}

export function buildThermocyclerCommand({
  action,
  moduleId,
  celsius = null,
  holdTimeSeconds = null,
  blockMaxVolumeUl = null,
  rampRate = null,
  profile = null,
  intent = "setup",
  key = null,
} = {}) {
  const commandTypeByAction = {
    set_block_temperature: "thermocycler/setTargetBlockTemperature",
    wait_for_block_temperature: "thermocycler/waitForBlockTemperature",
    set_lid_temperature: "thermocycler/setTargetLidTemperature",
    wait_for_lid_temperature: "thermocycler/waitForLidTemperature",
    deactivate_block: "thermocycler/deactivateBlock",
    deactivate_lid: "thermocycler/deactivateLid",
    open_lid: "thermocycler/openLid",
    close_lid: "thermocycler/closeLid",
    run_profile: "thermocycler/runProfile",
  };
  const commandType = commandTypeByAction[action];
  if (!commandType) {
    throw new Error(`Unsupported thermocycler action: ${action}`);
  }
  return buildCommandPayload({
    commandType,
    intent,
    key,
    params: {
      moduleId,
      ...(typeof celsius === "number" ? { celsius } : {}),
      ...(typeof holdTimeSeconds === "number" ? { holdTimeSeconds } : {}),
      ...(typeof blockMaxVolumeUl === "number" ? { blockMaxVolumeUl } : {}),
      ...(typeof rampRate === "number" ? { rampRate } : {}),
      ...(Array.isArray(profile) ? { profile } : {}),
    },
  });
}

export function buildCaptureImageCommand({
  fileName = null,
  resolution = null,
  zoom = null,
  pan = null,
  contrast = null,
  brightness = null,
  saturation = null,
  intent = "setup",
  key = null,
} = {}) {
  return buildCommandPayload({
    commandType: "captureImage",
    intent,
    key,
    params: {
      ...(fileName ? { fileName } : {}),
      ...(Array.isArray(resolution) ? { resolution } : {}),
      ...(typeof zoom === "number" ? { zoom } : {}),
      ...(Array.isArray(pan) ? { pan } : {}),
      ...(typeof contrast === "number" ? { contrast } : {}),
      ...(typeof brightness === "number" ? { brightness } : {}),
      ...(typeof saturation === "number" ? { saturation } : {}),
    },
  });
}

export function buildOpenGripperJawCommand({ intent = "setup", key = null } = {}) {
  return buildCommandPayload({
    commandType: "robot/openGripperJaw",
    intent,
    key,
    params: {},
  });
}

export function buildMoveToMaintenancePositionCommand({
  mount = "extension",
  maintenancePosition = null,
  intent = "setup",
  key = null,
} = {}) {
  return buildCommandPayload({
    commandType: "calibration/moveToMaintenancePosition",
    intent,
    key,
    params: {
      mount,
      ...(maintenancePosition ? { maintenancePosition } : {}),
    },
  });
}

export function buildHomeCommand({
  axes = null,
  skipIfMountPositionOk = null,
  intent = "setup",
  key = null,
} = {}) {
  return buildCommandPayload({
    commandType: "home",
    intent,
    key,
    params: {
      ...(axes ? { axes } : {}),
      ...(skipIfMountPositionOk ? { skipIfMountPositionOk } : {}),
    },
  });
}

export function deriveCleanupPendingActions(commandType) {
  switch (commandType) {
    case "moveLabware":
      return ["open_gripper_jaw", "move_to_maintenance_position"];
    case "robot/openGripperJaw":
      return ["move_to_maintenance_position"];
    case "calibration/moveToMaintenancePosition":
      return [];
    case "home":
      return [];
    default:
      return null;
  }
}
