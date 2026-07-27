import fs from "fs";
import path from "path";

import {
  COLUMN_MAJOR_WELL_ORDER_96,
  computeStartingTip,
  ensureTiprackState,
  markTipWellStatus,
} from "./state.js";

const TIP_ONLY_ALLOWED_COMMANDS = new Set([
  "home",
  "loadLabware",
  "loadPipette",
  "pickUpTip",
  "comment",
  "moveToAddressableAreaForDropTip",
  "dropTipInPlace",
]);

const FLEX_PIPETTE_NAME_ALIASES = new Map([
  ["p50_single_flex", "flex_1channel_50"],
  ["p50_multi_flex", "flex_8channel_50"],
  ["p50_96_flex", "flex_96channel_50"],
  ["p1000_single_flex", "flex_1channel_1000"],
  ["p1000_multi_flex", "flex_8channel_1000"],
  ["p1000_96_flex", "flex_96channel_1000"],
]);

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

function normalizeWell(wellName) {
  return wellName ? String(wellName).toUpperCase() : null;
}

function normalizePipetteProtocolName(pipetteName) {
  const normalized = String(pipetteName || "").trim();
  return FLEX_PIPETTE_NAME_ALIASES.get(normalized.toLowerCase()) || normalized || null;
}

function extractRunRecord(runPayload) {
  return runPayload?.data || runPayload || {};
}

function extractTiprackLoad(run) {
  const runRecord = extractRunRecord(run);
  const tiprack = asArray(runRecord.labware).find(item =>
    String(item?.loadName || "").toLowerCase().includes("tiprack"),
  );
  if (!tiprack) {
    return null;
  }
  return {
    slot_name: readNested(tiprack, [["location", "slotName"]], null),
    load_name: tiprack.loadName || null,
  };
}

function extractPipetteLoad(run) {
  const runRecord = extractRunRecord(run);
  const pipette = asArray(runRecord.pipettes)[0] || null;
  if (!pipette) {
    return null;
  }
  return {
    pipette_name: normalizePipetteProtocolName(pipette.pipetteName),
    source_pipette_name: pipette.pipetteName || null,
    mount: pipette.mount || null,
  };
}

function extractCommentAfterPick(commands, pickIndex) {
  for (let index = pickIndex + 1; index < commands.length; index += 1) {
    const command = commands[index];
    if (command.commandType === "pickUpTip") {
      break;
    }
    if (command.commandType === "comment") {
      return readNested(command, [["params", "message"]], null);
    }
  }
  return null;
}

function extractTipOnlyPlan(analysisCommands = []) {
  const unsupported = asArray(analysisCommands)
    .filter(command => !TIP_ONLY_ALLOWED_COMMANDS.has(command.commandType))
    .map(command => command.commandType);
  if (unsupported.length > 0) {
    throw new Error(
      `Continuation generator only supports tip-only protocols; unsupported commands: ${[
        ...new Set(unsupported),
      ].join(", ")}`,
    );
  }

  const picks = [];
  for (let index = 0; index < analysisCommands.length; index += 1) {
    const command = analysisCommands[index];
    if (command.commandType !== "pickUpTip") {
      continue;
    }
    picks.push({
      original_well: normalizeWell(readNested(command, [["params", "wellName"]], null)),
      comment: extractCommentAfterPick(analysisCommands, index),
    });
  }

  return picks;
}

export function buildTipContinuationLedger({ run, commands, sessionState } = {}) {
  const tiprackLoad = extractTiprackLoad(run);
  if (!tiprackLoad?.slot_name) {
    throw new Error("Cannot build continuation ledger without a tiprack slot in the run record.");
  }

  const state = sessionState || {
    session_id: "continuation-preview",
    tip_tracking: { tipracks: {} },
  };
  const tiprackState = ensureTiprackState(state, {
    slotName: tiprackLoad.slot_name,
    loadName: tiprackLoad.load_name,
  });
  const completedCycles = [];
  let pendingPick = null;

  for (const command of asArray(commands)) {
    if (command.commandType !== "pickUpTip" && command.commandType !== "dropTipInPlace") {
      continue;
    }

    if (command.commandType === "pickUpTip") {
      const wellName = normalizeWell(readNested(command, [["params", "wellName"]], null));
      const status = command.status;
      if (!wellName) {
        continue;
      }
      if (status === "succeeded") {
        markTipWellStatus(state, {
          slotName: tiprackLoad.slot_name,
          wellName,
          status: "depleted",
        });
        pendingPick = wellName;
      } else if (status === "failed") {
        const depleted = new Set(tiprackState.depleted_wells || []);
        markTipWellStatus(state, {
          slotName: tiprackLoad.slot_name,
          wellName,
          status: depleted.has(wellName) ? "depleted" : "missing",
        });
      }
    }

    if (command.commandType === "dropTipInPlace" && command.status === "succeeded" && pendingPick) {
      completedCycles.push({ consumed_well: pendingPick });
      pendingPick = null;
    }
  }

  return {
    tiprack_slot: tiprackLoad.slot_name,
    tiprack_load_name: tiprackLoad.load_name,
    completed_cycles: completedCycles.length,
    completed_cycle_wells: completedCycles.map(item => item.consumed_well),
    missing_wells: tiprackState.missing_wells || [],
    depleted_wells: tiprackState.depleted_wells || [],
    last_good_tip: tiprackState.last_good_tip || null,
    starting_tip: computeStartingTip(tiprackState),
    search_order: tiprackState.search_order || COLUMN_MAJOR_WELL_ORDER_96,
  };
}

function nextWellsFrom(startingTip, count, searchOrder = COLUMN_MAJOR_WELL_ORDER_96) {
  const startIndex = searchOrder.indexOf(startingTip);
  if (startIndex < 0 || count < 1) {
    return [];
  }
  return searchOrder.slice(startIndex, startIndex + count);
}

export function renderTipContinuationProtocol({
  protocolName = "Tip Iterator Probe Continuation",
  tiprackLoadName,
  tiprackSlot,
  pipetteName,
  mount,
  startingTip,
  remainingCycles,
  cycleComments = [],
  sourceRunId = null,
} = {}) {
  if (!tiprackLoadName || !tiprackSlot || !pipetteName || !mount || !startingTip) {
    throw new Error("Continuation protocol requires tiprack, pipette, mount, and startingTip.");
  }
  if (!Number.isInteger(remainingCycles) || remainingCycles < 1) {
    throw new Error("Continuation protocol requires at least one remaining cycle.");
  }

  const commentsLiteral = JSON.stringify(cycleComments);
  return `from opentrons import protocol_api

metadata = {
    "protocolName": ${JSON.stringify(protocolName)},
    "author": "LabscriptAI OT",
    "description": "Generated continuation protocol. Uses starting_tip and skips completed tip cycles.",
    "apiLevel": "2.22",
}

requirements = {"robotType": "Flex"}


def run(protocol: protocol_api.ProtocolContext) -> None:
    protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware(${JSON.stringify(tiprackLoadName)}, ${JSON.stringify(tiprackSlot)})
    pipette = protocol.load_instrument(${JSON.stringify(pipetteName)}, ${JSON.stringify(mount)}, tip_racks=[tiprack])
    pipette.starting_tip = tiprack[${JSON.stringify(startingTip)}]
    comments = ${commentsLiteral}
    protocol.comment(${JSON.stringify(`continuation_from_run=${sourceRunId || "unknown"} starting_tip=${startingTip}`)})
    for index in range(${remainingCycles}):
        pipette.pick_up_tip()
        if index < len(comments) and comments[index]:
            protocol.comment(comments[index])
        else:
            protocol.comment(f"continuation_tip_cycle_{index + 1}_ok")
        pipette.drop_tip()
`;
}

export function generateTipContinuationProtocol({
  run,
  runCommands,
  analysisCommands,
  sessionState = null,
  outputPath,
  protocolName = null,
} = {}) {
  const plan = extractTipOnlyPlan(asArray(analysisCommands));
  if (plan.length === 0) {
    throw new Error("Continuation generator found no pickUpTip cycles in analysis commands.");
  }

  const ledger = buildTipContinuationLedger({
    run,
    commands: runCommands,
    sessionState,
  });
  const remainingPlan = plan.slice(ledger.completed_cycles);
  if (remainingPlan.length === 0) {
    throw new Error("Continuation generator found no remaining cycles after completed history.");
  }

  const pipette = extractPipetteLoad(run);
  const plannedWells = nextWellsFrom(
    ledger.starting_tip,
    remainingPlan.length,
    ledger.search_order,
  );
  if (plannedWells.length < remainingPlan.length) {
    throw new Error("Not enough remaining tips to render continuation protocol.");
  }

  const sourceRunId = readNested(extractRunRecord(run), [["id"]], null);
  const sourceProtocolName = readNested(extractRunRecord(run), [["protocolId"]], null);
  const rendered = renderTipContinuationProtocol({
    protocolName: protocolName || `Continuation for ${sourceProtocolName || sourceRunId || "tip protocol"}`,
    tiprackLoadName: ledger.tiprack_load_name,
    tiprackSlot: ledger.tiprack_slot,
    pipetteName: pipette?.pipette_name,
    mount: pipette?.mount,
    startingTip: ledger.starting_tip,
    remainingCycles: remainingPlan.length,
    cycleComments: remainingPlan.map((step, index) =>
      step.comment || `continuation_replaces_${step.original_well || plannedWells[index]}`,
    ),
    sourceRunId,
  });

  const operations = remainingPlan.map((step, index) => ({
    type: "tip_cycle",
    original_well: step.original_well,
    continuation_well: plannedWells[index],
    comment: step.comment || null,
  }));

  const result = {
    protocol_source: rendered,
    output_path: outputPath ? path.resolve(outputPath) : null,
    ledger,
    operations,
    remaining_cycles: remainingPlan.length,
    starting_tip: ledger.starting_tip,
  };

  if (outputPath) {
    fs.mkdirSync(path.dirname(path.resolve(outputPath)), { recursive: true });
    fs.writeFileSync(path.resolve(outputPath), rendered);
  }

  return result;
}
