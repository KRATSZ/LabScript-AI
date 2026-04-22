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

function pythonLiteral(value) {
  return JSON.stringify(value);
}

export function buildProbeWellsProtocol({
  pipetteName,
  mount,
  tiprackLoadName,
  tiprackSlot,
  labwareLoadName,
  labwareSlot,
  wells = [],
  mode = "detect_presence",
  apiLevel = "2.24",
  robotType = "Flex",
  tiprackNamespace = "opentrons",
  tiprackVersion = 1,
  labwareNamespace = "opentrons",
  labwareVersion = 1,
  liquidPresenceDetection = true,
  trashSlot = null,
} = {}) {
  const normalizedWells = wells.map(well => String(well).toUpperCase());
  const usedSlots = new Set([tiprackSlot, labwareSlot].filter(Boolean).map(slot => String(slot).toUpperCase()));
  const resolvedTrashSlot =
    trashSlot ||
    ["A3", "B3", "C3", "D3"].find(candidate => !usedSlots.has(candidate)) ||
    "A3";
  const probeLinesByMode = {
    detect_presence: [
      "            probe_success = True",
      "            probe_value = pipette.detect_liquid_presence(target_well)",
    ],
    require_presence: [
      "            pipette.require_liquid_presence(target_well)",
      "            probe_success = True",
      "            probe_value = True",
    ],
    measure_height: [
      "            probe_success = True",
      "            probe_value = pipette.measure_liquid_height(target_well)",
    ],
  };
  const probeLines = probeLinesByMode[mode];
  if (!probeLines) {
    throw new Error(`Unsupported probe mode: ${mode}`);
  }

  return [
    "from opentrons import protocol_api",
    "import json",
    "",
    `metadata = {"protocolName": "Probe Wells", "author": "Opentrons Lab MCP"}`,
    `requirements = {"robotType": ${pythonLiteral(robotType)}, "apiLevel": ${pythonLiteral(apiLevel)}}`,
    "",
    "def run(protocol: protocol_api.ProtocolContext) -> None:",
    `    protocol.load_trash_bin(${pythonLiteral(resolvedTrashSlot)})`,
    `    target_labware = protocol.load_labware(${pythonLiteral(labwareLoadName)}, ${pythonLiteral(labwareSlot)}, namespace=${pythonLiteral(labwareNamespace)}, version=${labwareVersion})`,
    `    tiprack = protocol.load_labware(${pythonLiteral(tiprackLoadName)}, ${pythonLiteral(tiprackSlot)}, namespace=${pythonLiteral(tiprackNamespace)}, version=${tiprackVersion})`,
    "    pipette = protocol.load_instrument(",
    `        instrument_name=${pythonLiteral(pipetteName)},`,
    `        mount=${pythonLiteral(mount)},`,
    "        tip_racks=[tiprack],",
    `        liquid_presence_detection=${liquidPresenceDetection ? "True" : "False"},`,
    "    )",
    `    probe_mode = ${pythonLiteral(mode)}`,
    `    wells = ${pythonLiteral(normalizedWells)}`,
    "    for well_name in wells:",
    "        pipette.pick_up_tip()",
    "        target_well = target_labware[well_name]",
    "        probe_success = False",
    "        probe_value = None",
    "        try:",
    ...probeLines,
    "            protocol.comment(",
    '                "PROBE_RESULT:" + json.dumps({',
    '                    "well": well_name,',
    '                    "mode": probe_mode,',
    '                    "success": probe_success,',
    '                    "value": probe_value,',
    "                })",
    "            )",
    "        finally:",
    "            pipette.drop_tip()",
    "",
  ].join("\n");
}

export function extractProbeResultsFromCommands(commandsPayload) {
  return asArray(unwrapData(commandsPayload))
    .filter(command => readNested(command, [["commandType"], ["command_type"]]) === "comment")
    .map(command => readNested(command, [["params", "message"], ["data", "params", "message"]], null))
    .filter(message => String(message || "").startsWith("PROBE_RESULT:"))
    .map(message => {
      try {
        return JSON.parse(String(message).slice("PROBE_RESULT:".length));
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}
