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
  startingTip = null,
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
    ...(startingTip ? [`    pipette.starting_tip = tiprack[${pythonLiteral(String(startingTip).toUpperCase())}]`] : []),
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

const APPROXIMATE_LABWARE_GEOMETRY = {
  nest_96_wellplate_200ul_flat: {
    well_depth_mm: 10.8,
    capacity_ul: 200,
    shape: "conical",
    bottom_diameter_mm: 6.32,
    top_diameter_mm: 6.85,
    approximate: true,
  },
  corning_96_wellplate_360ul_flat: {
    well_depth_mm: 10.67,
    capacity_ul: 360,
    shape: "cylinder",
    diameter_mm: 6.86,
    approximate: true,
  },
  nest_96_wellplate_2ml_deep: {
    well_depth_mm: 38,
    capacity_ul: 2000,
    shape: "segmented",
    sections: [
      {
        shape: "cuboidal",
        bottom_x_mm: 2.63,
        bottom_y_mm: 2.63,
        top_x_mm: 7.4,
        top_y_mm: 7.4,
        height_mm: 1.67,
      },
      {
        shape: "cuboidal",
        bottom_x_mm: 7.4,
        bottom_y_mm: 7.4,
        top_x_mm: 8.2,
        top_y_mm: 8.2,
        height_mm: 36.33,
      },
    ],
    approximate: true,
  },
  nest_96_wellplate_100ul_pcr_full_skirt: {
    well_depth_mm: 14.95,
    capacity_ul: 100,
    shape: "conical",
    bottom_diameter_mm: 5.49,
    top_diameter_mm: 5.49,
    approximate: true,
  },
  opentrons_96_wellplate_200ul_pcr_full_skirt: {
    well_depth_mm: 14.95,
    capacity_ul: 200,
    shape: "conical",
    bottom_diameter_mm: 5.49,
    top_diameter_mm: 5.49,
    approximate: true,
  },
};

function hasUsableGeometry(geometry) {
  if (!geometry || typeof geometry !== "object") {
    return false;
  }
  if (geometry.well_depth_mm != null) {
    return true;
  }
  if (geometry.cross_section_area_mm2 != null) {
    return true;
  }
  if (geometry.diameter_mm != null || geometry.radius_mm != null) {
    return true;
  }
  if (geometry.bottom_diameter_mm != null || geometry.top_diameter_mm != null) {
    return true;
  }
  if (Array.isArray(geometry.sections) && geometry.sections.length > 0) {
    return true;
  }
  if (geometry.shape === "cylinder" || geometry.shape === "conical" || geometry.shape === "segmented") {
    return true;
  }
  return false;
}

function radiusFromDiameter(diameterMm) {
  return Number(diameterMm) / 2;
}

function cylinderVolumeUl(radiusMm, heightMm) {
  return Math.PI * radiusMm * radiusMm * heightMm;
}

function coneVolumeUl(radiusMm, heightMm) {
  return (Math.PI * radiusMm * radiusMm * heightMm) / 3;
}

function conicalFrustumVolumeUl(bottomRadiusMm, topRadiusMm, heightMm) {
  if (heightMm <= 0) {
    return 0;
  }
  return (
    (Math.PI * heightMm) /
    3 *
    (bottomRadiusMm * bottomRadiusMm +
      bottomRadiusMm * topRadiusMm +
      topRadiusMm * topRadiusMm)
  );
}

function conicalColumnVolumeUl({ bottom_diameter_mm, top_diameter_mm, well_depth_mm }, heightMm) {
  const depth = Number(well_depth_mm);
  const rBottom = radiusFromDiameter(bottom_diameter_mm);
  const rTop = radiusFromDiameter(top_diameter_mm);
  if (!Number.isFinite(depth) || depth <= 0) {
    return cylinderVolumeUl(rTop || rBottom, heightMm);
  }
  const filledHeight = Math.min(heightMm, depth);
  const radiusAtFill = rBottom + ((rTop - rBottom) * filledHeight) / depth;
  return conicalFrustumVolumeUl(rBottom, radiusAtFill, filledHeight);
}

function cuboidalSectionVolumeUl({ bottom_x_mm, bottom_y_mm, top_x_mm, top_y_mm, height_mm }, fillHeightMm) {
  const sectionHeight = Number(height_mm);
  const filled = Math.min(fillHeightMm, sectionHeight);
  if (filled <= 0) {
    return 0;
  }
  const bottomArea = Number(bottom_x_mm) * Number(bottom_y_mm);
  const fraction = filled / sectionHeight;
  const topX = Number(bottom_x_mm) + (Number(top_x_mm) - Number(bottom_x_mm)) * fraction;
  const topY = Number(bottom_y_mm) + (Number(top_y_mm) - Number(bottom_y_mm)) * fraction;
  const topArea = topX * topY;
  return (filled / 3) * (bottomArea + Math.sqrt(bottomArea * topArea) + topArea);
}

function segmentedVolumeUl(geometry, heightMm) {
  let remaining = heightMm;
  let volume = 0;
  for (const section of geometry.sections) {
    if (remaining <= 0) {
      break;
    }
    const sectionFill = Math.min(remaining, Number(section.height_mm));
    if (section.shape === "cuboidal") {
      volume += cuboidalSectionVolumeUl(section, sectionFill);
    } else if (section.shape === "cylinder") {
      const radius = radiusFromDiameter(section.diameter_mm ?? section.top_diameter_mm);
      volume += cylinderVolumeUl(radius, sectionFill);
    } else if (section.shape === "conical") {
      volume += conicalColumnVolumeUl(
        {
          bottom_diameter_mm: section.bottom_diameter_mm,
          top_diameter_mm: section.top_diameter_mm,
          well_depth_mm: section.height_mm,
        },
        sectionFill,
      );
    }
    remaining -= sectionFill;
  }
  return volume;
}

function volumeFromGeometry(geometry, heightMm) {
  if (heightMm <= 0) {
    return 0;
  }

  if (geometry.shape === "segmented" && Array.isArray(geometry.sections)) {
    return segmentedVolumeUl(geometry, heightMm);
  }

  if (geometry.cross_section_area_mm2 != null) {
    return Number(geometry.cross_section_area_mm2) * heightMm;
  }

  if (geometry.shape === "conical" || geometry.bottom_diameter_mm != null || geometry.top_diameter_mm != null) {
    return conicalColumnVolumeUl(geometry, heightMm);
  }

  const radius =
  geometry.radius_mm != null
    ? Number(geometry.radius_mm)
    : geometry.diameter_mm != null
      ? radiusFromDiameter(geometry.diameter_mm)
      : null;

  if (radius != null && Number.isFinite(radius)) {
    return cylinderVolumeUl(radius, heightMm);
  }

  if (Array.isArray(geometry.sections) && geometry.sections.length > 0) {
    return segmentedVolumeUl(geometry, heightMm);
  }

  return null;
}

function roundVolumeUl(volumeUl) {
  if (volumeUl == null || !Number.isFinite(volumeUl)) {
    return null;
  }
  return Math.round(volumeUl * 10) / 10;
}

export function lookupLabwareGeometry(labware_load_name) {
  if (!labware_load_name) {
    return null;
  }
  const key = String(labware_load_name).trim();
  const geometry = APPROXIMATE_LABWARE_GEOMETRY[key];
  if (!geometry) {
    return null;
  }
  return { ...geometry };
}

export function heightMmToVolumeUl({ height_mm, labware_load_name, well_name, geometry }) {
  void well_name;

  let resolvedGeometry = null;
  let method = "unknown";

  if (hasUsableGeometry(geometry)) {
    resolvedGeometry = geometry;
    method = "geometry:explicit";
  } else if (labware_load_name) {
    const lookedUp = lookupLabwareGeometry(labware_load_name);
    if (lookedUp) {
      resolvedGeometry = lookedUp;
      method = `geometry:approximate:${String(labware_load_name).trim()}`;
    }
  }

  if (!resolvedGeometry) {
    return { volume_ul: null, method: "unknown", confidence: null };
  }

  const heightMm = Number(height_mm);
  if (!Number.isFinite(heightMm) || heightMm <= 0) {
    return { volume_ul: 0, method, confidence: "observed" };
  }

  const wellDepth = resolvedGeometry.well_depth_mm != null ? Number(resolvedGeometry.well_depth_mm) : null;
  let effectiveHeight = heightMm;
  const notes = [];

  if (wellDepth != null && Number.isFinite(wellDepth) && heightMm > wellDepth) {
    effectiveHeight = wellDepth;
    notes.push("height_exceeds_well_depth_clamped");
  }

  const rawVolume = volumeFromGeometry(resolvedGeometry, effectiveHeight);
  if (rawVolume == null || !Number.isFinite(rawVolume)) {
    return { volume_ul: null, method: "unknown", confidence: null };
  }

  let volumeUl = roundVolumeUl(rawVolume);
  const capacity = resolvedGeometry.capacity_ul != null ? Number(resolvedGeometry.capacity_ul) : null;
  if (capacity != null && Number.isFinite(capacity) && volumeUl > capacity) {
    volumeUl = capacity;
    if (!notes.includes("height_exceeds_well_depth_clamped")) {
      notes.push("height_exceeds_well_depth_clamped");
    }
  }

  const result = {
    volume_ul: volumeUl,
    method,
    confidence: "observed",
  };
  if (notes.length > 0) {
    result.notes = notes.join(";");
  }
  return result;
}
