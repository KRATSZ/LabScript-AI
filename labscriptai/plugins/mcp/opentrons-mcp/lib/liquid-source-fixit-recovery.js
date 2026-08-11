import {
  buildCommandPayload,
  buildDropTipInPlaceCommand,
  buildMoveToAddressableAreaForDropTipCommand,
} from "./execution.js";
import { parseLiquidSourceMapKey } from "./liquid-source-substitution.js";
import {
  parseProtocolDeckHints,
  parseProtocolTransferContinuationHints,
} from "./protocol-liquid-sources.js";

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

function normalizeRunRecord(runPayload) {
  if (!runPayload) {
    return null;
  }
  if (runPayload.data && typeof runPayload.data === "object") {
    return runPayload.data;
  }
  return runPayload;
}

export function extractRunLabware(runPayload) {
  const run = normalizeRunRecord(runPayload) || {};
  return asArray(readNested(run, [["labware"]], []));
}

export function findRunLabwareIdBySlot(runPayload, slotName) {
  const normalizedSlot = String(slotName || "").trim().toUpperCase();
  if (!normalizedSlot) {
    return null;
  }
  for (const labware of extractRunLabware(runPayload)) {
    const slot = readNested(labware, [["location", "slotName"]], null);
    if (String(slot || "").toUpperCase() === normalizedSlot) {
      return readNested(labware, [["id"]], null);
    }
  }
  return null;
}

export function buildLiquidProbeFixitPayload({
  pipetteId,
  labwareId,
  wellName,
  key = null,
} = {}) {
  return buildCommandPayload({
    commandType: "liquidProbe",
    intent: "fixit",
    key,
    params: {
      pipetteId,
      labwareId,
      wellName,
    },
  });
}

export function buildAspirateFixitPayload({
  pipetteId,
  labwareId,
  wellName,
  volume,
  flowRate = 716,
  key = null,
} = {}) {
  return buildCommandPayload({
    commandType: "aspirate",
    intent: "fixit",
    key,
    params: {
      pipetteId,
      labwareId,
      wellName,
      volume,
      flowRate,
      wellLocation: {
        origin: "bottom",
        offset: { x: 0, y: 0, z: 1 },
      },
    },
  });
}

export function buildDispenseFixitPayload({
  pipetteId,
  labwareId,
  wellName,
  volume,
  flowRate = 716,
  key = null,
} = {}) {
  return buildCommandPayload({
    commandType: "dispense",
    intent: "fixit",
    key,
    params: {
      pipetteId,
      labwareId,
      wellName,
      volume,
      flowRate,
      wellLocation: {
        origin: "bottom",
        offset: { x: 0, y: 0, z: 1 },
      },
    },
  });
}

export function buildPickUpTipFixitPayload({
  pipetteId,
  labwareId,
  wellName,
  key = null,
} = {}) {
  return buildCommandPayload({
    commandType: "pickUpTip",
    intent: "fixit",
    key,
    params: {
      pipetteId,
      labwareId,
      wellName,
    },
  });
}

export function normalizeCommandsList(commandsPayload) {
  if (Array.isArray(commandsPayload)) {
    return commandsPayload;
  }
  const unwrapped = commandsPayload?.data ?? commandsPayload;
  if (Array.isArray(unwrapped)) {
    return unwrapped;
  }
  if (Array.isArray(unwrapped?.data)) {
    return unwrapped.data;
  }
  return [];
}

export function isFixitCommand(command) {
  const intent = command?.intent ?? command?.data?.intent;
  return String(intent || "").toLowerCase() === "fixit";
}

/** Last succeeded protocol (non-fixit) pickUpTip well — the tip consumed before liquidProbe failure. */
export function findLastSucceededProtocolPickUpTipWell(commandsPayload) {
  const commands = normalizeCommandsList(commandsPayload);
  for (let index = commands.length - 1; index >= 0; index -= 1) {
    const command = commands[index];
    if (command?.commandType !== "pickUpTip") {
      continue;
    }
    if (String(command?.status || "").toLowerCase() !== "succeeded") {
      continue;
    }
    if (isFixitCommand(command)) {
      continue;
    }
    return readNested(command, [["params", "wellName"]], null);
  }
  return null;
}

export function splitLiquidSubstitutionFixitSteps(steps = []) {
  const confirmIndex = steps.findIndex(step => String(step?.name || "").startsWith("confirm_"));
  if (confirmIndex === -1) {
    return { transferSteps: steps, confirmSteps: [] };
  }
  return {
    transferSteps: steps.slice(0, confirmIndex),
    confirmSteps: steps.slice(confirmIndex),
  };
}

/**
 * Split the leading replacement_liquid_probe from remaining transfer (+ later confirm) steps.
 */
export function splitReplacementProbeStep(steps = []) {
  const list = Array.isArray(steps) ? steps : [];
  const probeIndex = list.findIndex(
    step => String(step?.name || "") === "replacement_liquid_probe",
  );
  if (probeIndex === -1) {
    return { probeStep: null, postProbeSteps: list };
  }
  return {
    probeStep: list[probeIndex],
    postProbeSteps: [...list.slice(0, probeIndex), ...list.slice(probeIndex + 1)],
  };
}

/**
 * Read liquid height (mm from well bottom) from a succeeded liquidProbe command/result.
 * Opentrons protocol-engine uses result.z_position; tolerate a few aliases.
 */
export function extractLiquidProbeHeightMm(commandOrResult = null) {
  const terminal = commandOrResult?.terminal ?? commandOrResult;
  const unwrapped =
    terminal && typeof terminal === "object" && "data" in terminal ? terminal.data : terminal;
  const candidates = [
    ["result", "z_position"],
    ["data", "result", "z_position"],
    ["result", "zPosition"],
    ["data", "result", "zPosition"],
    ["result", "liquidHeight"],
    ["data", "result", "liquidHeight"],
    ["result", "height"],
    ["data", "result", "height"],
    ["z_position"],
    ["zPosition"],
  ];
  for (const path of candidates) {
    let current = unwrapped;
    let found = true;
    for (const part of path) {
      if (current && typeof current === "object" && part in current) {
        current = current[part];
      } else {
        found = false;
        break;
      }
    }
    if (found && current !== undefined && current !== null && current !== "") {
      const number = Number(current);
      if (Number.isFinite(number)) {
        return number;
      }
    }
  }
  return null;
}

/** Drop-tip suffix used when reserve LPD/volume gate aborts before transfers. */
export function selectDropTipCleanupSteps(steps = []) {
  const names = new Set(["move_to_trash_for_drop", "drop_attached_tip"]);
  return (Array.isArray(steps) ? steps : []).filter(step => names.has(String(step?.name || "")));
}

export function planConfirmProbeFixitSteps({
  pipetteId,
  tiprackLabwareId,
  plateLabwareId,
  tipWell,
  confirmWell = "A1",
  trashSlot = "A3",
  idempotencyKeyPrefix = null,
} = {}) {
  if (!pipetteId || !tiprackLabwareId || !plateLabwareId || !tipWell) {
    throw new Error(
      "planConfirmProbeFixitSteps requires pipetteId, tiprackLabwareId, plateLabwareId, and tipWell.",
    );
  }
  const trashArea = `movableTrash${trashSlot}`;
  const keyPrefix = idempotencyKeyPrefix ? `${idempotencyKeyPrefix}:` : "";
  const steps = [
    {
      name: "confirm_pick_up_tip",
      payload: buildPickUpTipFixitPayload({
        pipetteId,
        labwareId: tiprackLabwareId,
        wellName: tipWell,
        key: `${keyPrefix}confirm-pick-up-tip`,
      }),
    },
    {
      name: "confirm_liquid_probe",
      payload: buildLiquidProbeFixitPayload({
        pipetteId,
        labwareId: plateLabwareId,
        wellName: confirmWell,
        key: `${keyPrefix}confirm-liquid-probe`,
      }),
    },
    {
      name: "confirm_move_to_trash_for_drop",
      payload: buildMoveToAddressableAreaForDropTipCommand({
        pipetteId,
        addressableAreaName: trashArea,
        intent: "fixit",
        key: `${keyPrefix}confirm-move-to-trash`,
      }),
    },
    {
      name: "confirm_drop_tip",
      payload: buildDropTipInPlaceCommand({
        pipetteId,
        intent: "fixit",
        key: `${keyPrefix}confirm-drop-tip`,
      }),
    },
  ];
  return {
    confirm_tip_well: tipWell,
    confirm_destination_well: confirmWell,
    steps,
  };
}

export function buildInRunLiquidSubstitutionRecord({
  runId,
  fixitPlan,
  failedSourceKey,
  preferredSourceKey,
  transfersCompleted = false,
  confirmCompleted = false,
  confirmDestinationWell = null,
  trashSlot = "A3",
} = {}) {
  return {
    run_id: runId,
    transfers_completed: transfersCompleted,
    confirm_completed: confirmCompleted,
    pipette_id: fixitPlan?.pipette_id || null,
    plate_labware_id: fixitPlan?.plate_labware_id || null,
    tiprack_labware_id: fixitPlan?.tiprack_labware_id || null,
    tiprack_slot: fixitPlan?.tiprack_slot || null,
    confirm_destination_well:
      confirmDestinationWell || fixitPlan?.destination_wells?.[0] || "A1",
    trash_slot: trashSlot,
    failed_source_key: failedSourceKey || null,
    preferred_source_key: preferredSourceKey || null,
  };
}

/** True when liquid-substitution fixit finished transfers but confirm is still pending. */
export function readPendingInRunLiquidSubstitutionConfirm(sessionState, runId) {
  const ctx = sessionState?.in_run_liquid_substitution;
  if (!ctx || ctx.run_id !== runId) {
    return null;
  }
  if (ctx.transfers_completed !== true || ctx.confirm_completed === true) {
    return null;
  }
  return ctx;
}

export function planInRunLiquidSourceSubstitutionFixitSteps({
  failedCommand = null,
  runDetail = null,
  preferredSourceKey = null,
  protocolSource = "",
  nextTipWell = null,
  tiprackSlot = null,
  idempotencyKeyPrefix = null,
} = {}) {
  const pipetteId = readNested(failedCommand, [["params", "pipetteId"]], null);
  const sourceLabwareId = readNested(failedCommand, [["params", "labwareId"]], null);
  const replacement = parseLiquidSourceMapKey(preferredSourceKey);
  if (!pipetteId || !sourceLabwareId || !replacement.well_name) {
    throw new Error(
      "In-run liquid substitution fixit requires pipetteId, source labwareId, and replacement well.",
    );
  }

  const hints = parseProtocolTransferContinuationHints(protocolSource);
  const deckHints = parseProtocolDeckHints(protocolSource);
  const plateLabwareId = findRunLabwareIdBySlot(runDetail, hints.plate_slot || "D2");
  const resolvedTiprackSlot = tiprackSlot || deckHints.tiprack_slot || "B2";
  const tiprackLabwareId = findRunLabwareIdBySlot(runDetail, resolvedTiprackSlot);
  if (!plateLabwareId) {
    throw new Error(
      `In-run liquid substitution fixit could not resolve plate labware on slot ${hints.plate_slot || "D2"}.`,
    );
  }

  const destinationWells = hints.destination_wells?.length ? hints.destination_wells : ["A1"];
  const transferVolume = hints.transfer_volume ?? 100;
  const trashArea = `movableTrash${hints.trash_slot || "A3"}`;
  const steps = [];
  const keyPrefix = idempotencyKeyPrefix ? `${idempotencyKeyPrefix}:` : "";

  steps.push({
    name: "replacement_liquid_probe",
    payload: buildLiquidProbeFixitPayload({
      pipetteId,
      labwareId: sourceLabwareId,
      wellName: replacement.well_name,
      key: `${keyPrefix}replacement-liquid-probe`,
    }),
  });

  for (const [index, destWell] of destinationWells.entries()) {
    steps.push({
      name: `transfer_aspirate_${destWell}`,
      payload: buildAspirateFixitPayload({
        pipetteId,
        labwareId: sourceLabwareId,
        wellName: replacement.well_name,
        volume: transferVolume,
        key: `${keyPrefix}aspirate-${index}-${destWell}`,
      }),
    });
    steps.push({
      name: `transfer_dispense_${destWell}`,
      payload: buildDispenseFixitPayload({
        pipetteId,
        labwareId: plateLabwareId,
        wellName: destWell,
        volume: transferVolume,
        key: `${keyPrefix}dispense-${index}-${destWell}`,
      }),
    });
  }

  steps.push({
    name: "move_to_trash_for_drop",
    payload: buildMoveToAddressableAreaForDropTipCommand({
      pipetteId,
      addressableAreaName: trashArea,
      intent: "fixit",
      key: `${keyPrefix}move-to-trash`,
    }),
  });
  steps.push({
    name: "drop_attached_tip",
    payload: buildDropTipInPlaceCommand({
      pipetteId,
      intent: "fixit",
      key: `${keyPrefix}drop-attached-tip`,
    }),
  });

  if (hints.has_confirm_probe_cycle !== false) {
    if (!tiprackLabwareId || !nextTipWell) {
      throw new Error(
        "In-run liquid substitution fixit requires tiprack labware and next tip well for confirm probe cycle.",
      );
    }
    const confirmWell = hints.confirm_destination_well?.split(".")[1] || destinationWells[0];
    const confirmPlan = planConfirmProbeFixitSteps({
      pipetteId,
      tiprackLabwareId,
      plateLabwareId,
      tipWell: nextTipWell,
      confirmWell,
      trashSlot: hints.trash_slot || "A3",
      idempotencyKeyPrefix,
    });
    steps.push(...confirmPlan.steps);
  }

  return {
    pipette_id: pipetteId,
    source_labware_id: sourceLabwareId,
    plate_labware_id: plateLabwareId,
    tiprack_labware_id: tiprackLabwareId,
    replacement_well: replacement.well_name,
    replacement_source_key: replacement.key,
    destination_wells: destinationWells,
    transfer_volume: transferVolume,
    confirm_tip_well: nextTipWell,
    tiprack_slot: resolvedTiprackSlot,
    steps,
  };
}

export async function executeInRunLiquidSourceSubstitutionFixitSteps({
  steps = [],
  enqueueAndPollCommand,
  robotIp,
  runId,
  timeoutMs = 120000,
  pollIntervalMs = 500,
  assertCommandSucceeded,
} = {}) {
  if (typeof enqueueAndPollCommand !== "function") {
    throw new Error("executeInRunLiquidSourceSubstitutionFixitSteps requires enqueueAndPollCommand.");
  }
  if (typeof assertCommandSucceeded !== "function") {
    throw new Error("executeInRunLiquidSourceSubstitutionFixitSteps requires assertCommandSucceeded.");
  }

  const executed = [];
  for (const step of steps) {
    const result = await enqueueAndPollCommand({
      robotIp,
      contextType: "protocol",
      contextId: runId,
      commandPayload: step.payload,
      timeoutMs,
      pollIntervalMs,
    });
    assertCommandSucceeded(result, step.name);
    executed.push({
      name: step.name,
      terminal: result.terminal,
    });
  }
  return executed;
}
