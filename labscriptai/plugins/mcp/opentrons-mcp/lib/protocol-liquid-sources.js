/**
 * Parse agent-recovery liquid source map and deck hints from protocol docstrings.
 */

function normalizeUpper(value) {
  return String(value || "").trim().toUpperCase();
}

function normalizeLiquidName(description = "") {
  let name = String(description || "").trim();
  name = name.replace(/\s*[—–-].*$/u, "").trim();
  name = name.replace(/\s*\(.*$/u, "").trim();
  name = name.replace(/^(primary|reserve)\s+/iu, "").trim();
  return name || null;
}

/**
 * Parse deck slot → labware lines from the protocol docstring, e.g. `C2  nest_12_reservoir_15ml`.
 */
export function parseProtocolDeckLabware(protocolSource = "") {
  const map = {};
  for (const match of String(protocolSource || "").matchAll(/^\s*([A-D]\d+)\s+([a-z0-9_.]+)/gim)) {
    map[normalizeUpper(match[1])] = match[2];
  }
  return map;
}

/**
 * Parse liquid source map entries from protocol comments/docstring.
 *
 * Example lines:
 *   C2.A1  primary Assay Buffer
 *   C2.A2  reserve Assay Buffer (same identity)
 */
export function parseProtocolLiquidSourceMap(protocolSource = "") {
  const source = String(protocolSource || "");
  const sectionMatch = source.match(
    /Liquid source map[^:\n]*:([\s\S]*?)(?:\n\n|\n"""|\nfrom\s|\nimport\s|$)/i,
  );
  if (!sectionMatch) {
    return { entries: [], deck_labware: parseProtocolDeckLabware(source) };
  }

  const deckLabware = parseProtocolDeckLabware(source);
  const entries = [];
  for (const line of sectionMatch[1].split("\n")) {
    const match = line.match(/^\s*([A-D]\d+)\.([A-H](?:1[0-2]|[1-9]))\s+(.+?)\s*$/i);
    if (!match) {
      continue;
    }
    const slotName = normalizeUpper(match[1]);
    const wellName = normalizeUpper(match[2]);
    const description = match[3].trim();
    entries.push({
      slot_name: slotName,
      well_name: wellName,
      key: `${slotName}.${wellName}`,
      liquid_name: normalizeLiquidName(description),
      expected_presence: true,
      trust_level: "declared",
      role: "source",
      notes: description,
      labware_load_name: deckLabware[slotName] || null,
    });
  }

  return { entries, deck_labware: deckLabware };
}

/**
 * Infer pipette/tiprack args for substitution recovery tools from protocol source.
 */
export function parseProtocolDeckHints(protocolSource = "") {
  const source = String(protocolSource || "");
  const tiprackMatch = source.match(
    /load_labware\(\s*["']([^"']*tiprack[^"']*)["']\s*,\s*["']([A-D]\d+)["']/i,
  );
  const pipetteMatch = source.match(
    /load_instrument\(\s*["']([^"']+)["']\s*,\s*["'](left|right)"/i,
  );
  return {
    tiprack_load_name: tiprackMatch?.[1] || null,
    tiprack_slot: tiprackMatch?.[1] ? normalizeUpper(tiprackMatch[2]) : null,
    pipette_name: pipetteMatch?.[1] || null,
    mount: pipetteMatch?.[2] || null,
  };
}

/**
 * Parse transfer/confirm hints from an experiment protocol for attached-tip continuation.
 */
export function parseProtocolTransferContinuationHints(protocolSource = "") {
  const source = String(protocolSource || "");
  const deckLabware = parseProtocolDeckLabware(source);
  const reservoirMatch = source.match(
    /reservoir\s*=\s*protocol\.load_labware\(\s*["']([^"']+)["']\s*,\s*["']([A-D]\d+)["']/i,
  );
  const plateMatch = source.match(
    /plate\s*=\s*protocol\.load_labware\(\s*["']([^"']+)["']\s*,\s*["']([A-D]\d+)["']/i,
  );
  const trashMatch = source.match(/load_trash_bin\(\s*["']([A-D]\d+)["']/i);
  const volumeMatch = source.match(/transfer_with_liquid_class\([\s\S]*?volume\s*=\s*(\d+(?:\.\d+)?)/i);
  const liquidClassMatch = source.match(/get_liquid_class\(\s*name\s*=\s*["']([^"']+)["']/i);
  const destinationWells = [];
  for (const match of source.matchAll(/plate\[\s*["']([A-H]\d+)["']\s*\]/gi)) {
    const well = normalizeUpper(match[1]);
    if (!destinationWells.includes(well)) {
      destinationWells.push(well);
    }
  }
  const confirmMatch = source.match(/Confirm\s+([A-D]\d+)\.([A-H]\d+)/i);
  const pickUpCount = (source.match(/pick_up_tip\s*\(/g) || []).length;
  return {
    reservoir_load_name: reservoirMatch?.[1] || null,
    reservoir_slot: reservoirMatch?.[2] ? normalizeUpper(reservoirMatch[2]) : null,
    plate_load_name: plateMatch?.[1] || null,
    plate_slot: plateMatch?.[2] ? normalizeUpper(plateMatch[2]) : null,
    trash_slot: trashMatch?.[1] ? normalizeUpper(trashMatch[1]) : "A3",
    transfer_volume: volumeMatch ? Number(volumeMatch[1]) : null,
    liquid_class_name: liquidClassMatch?.[1] || "water",
    destination_wells: destinationWells,
    confirm_destination_well: confirmMatch
      ? `${normalizeUpper(confirmMatch[1])}.${normalizeUpper(confirmMatch[2])}`
      : destinationWells[0]
        ? `${plateMatch?.[2]?.toUpperCase() || "D2"}.${destinationWells[0]}`
        : null,
    has_confirm_probe_cycle: pickUpCount >= 2,
  };
}

/**
 * Seed session liquid source map from protocol file contents when entries are absent.
 */
export function seedProtocolLiquidSourceMap(sessionState, protocolSource = {}) {
  const parsed = parseProtocolLiquidSourceMap(protocolSource);
  if (parsed.entries.length === 0) {
    return { seeded: [], skipped: 0 };
  }

  const existing = sessionState?.liquid_tracking?.sources || {};
  const seeded = [];
  for (const entry of parsed.entries) {
    if (existing[entry.key]) {
      continue;
    }
    sessionState.liquid_tracking = sessionState.liquid_tracking || { containers: {}, sources: {} };
    sessionState.liquid_tracking.sources[entry.key] = {
      ...entry,
      why: "protocol_liquid_source_map_seed",
    };
    sessionState.liquid_tracking.containers[entry.key] = {
      ...entry,
      container_key: entry.key,
      why: "protocol_liquid_source_map_seed",
    };
    seeded.push(entry.key);
  }
  return { seeded, skipped: parsed.entries.length - seeded.length };
}
