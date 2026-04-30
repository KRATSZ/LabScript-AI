/**
 * Heuristic extraction of declared deck loads from Opentrons Python protocol source.
 * Used for Flex-oriented preflight: compare declared slots vs live observed deck state.
 * OT-2 numeric deck slots are not modeled here; callers should skip strict diff for OT-2.
 */

export function extractRobotTypeFromProtocolSource(source) {
  if (typeof source !== "string") {
    return null;
  }
  const match = source.match(/robotType["']\s*:\s*["']([^"']+)["']/i);
  return match ? String(match[1]).trim() : null;
}

function normalizeFlexSlot(slot) {
  const s = String(slot || "")
    .trim()
    .toUpperCase();
  return /^[A-D][1-3]$/.test(s) ? s : null;
}

/**
 * @returns {Array<{ kind: string, load_name: string | null, slot: string }>}
 */
export function extractDeclaredProtocolLoads(source) {
  if (typeof source !== "string") {
    return [];
  }

  const loads = [];
  const seen = new Set();

  const push = (kind, loadName, slotRaw) => {
    const slot = normalizeFlexSlot(slotRaw);
    if (!slot) {
      return;
    }
    const key = `${kind}:${slot}:${loadName || ""}`;
    if (seen.has(key)) {
      return;
    }
    seen.add(key);
    loads.push({
      kind,
      load_name: loadName,
      slot,
    });
  };

  // protocol.load_labware("nest_12_reservoir_15ml", "B3")
  // protocol.load_labware('x', "C2", namespace="opentrons", version=1)
  const loadLabwareRe = /load_labware\s*\(\s*["']([^"']+)["']\s*,\s*["']?([A-Da-d][1-3])["']?/g;
  let m;
  while ((m = loadLabwareRe.exec(source)) !== null) {
    push("labware", m[1], m[2]);
  }

  // protocol.load_trash_bin("A3")
  const trashRe = /load_trash_bin\s*\(\s*["']?([A-Da-d][1-3])["']?/g;
  while ((m = trashRe.exec(source)) !== null) {
    push("trash_bin", null, m[1]);
  }

  // protocol.load_module(ModuleType, "D3") — slot only; module identity not compared
  const moduleRe = /load_module\s*\(\s*[^,]+\s*,\s*["']?([A-Da-d][1-3])["']?/g;
  while ((m = moduleRe.exec(source)) !== null) {
    push("module", null, m[1]);
  }

  return loads;
}

function normalizeLoadName(name) {
  return String(name || "")
    .trim()
    .toLowerCase()
    .replace(/_/g, "-");
}

function loadNamesCompatible(declared, observed) {
  if (!declared || !observed) {
    return false;
  }
  const a = normalizeLoadName(declared);
  const b = normalizeLoadName(observed);
  if (a === b) {
    return true;
  }
  // allow substring match for namespace/version suffix noise
  return a.includes(b) || b.includes(a);
}

/**
 * @param {object} options
 * @param {Array<{ kind: string, load_name: string | null, slot: string }>} options.declaredLoads
 * @param {object} options.observedDeckState - from buildObservedDeckState
 * @param {boolean} [options.strictEmptyLabwareSlots]
 */
export function compareDeclaredLoadsToObservedDeck({
  declaredLoads = [],
  observedDeckState = {},
  strictEmptyLabwareSlots = false,
} = {}) {
  const errors = [];
  const warnings = [];
  const slots = observedDeckState?.slots || {};

  for (const item of declaredLoads) {
    const slotName = item.slot;
    const slotState = slots[slotName];
    if (!slotState) {
      warnings.push({
        code: "slot_not_in_flex_model",
        slot: slotName,
        message: `Slot ${slotName} is outside the Flex 12-slot model used by this preflight.`,
      });
      continue;
    }

    if (!slotState.addressable) {
      errors.push({
        code: "slot_not_addressable",
        slot: slotName,
        kind: item.kind,
        message: `Declared ${item.kind} at ${slotName}, but this slot is not addressable on the observed deck.`,
      });
      continue;
    }

    const status = slotState.observed_status;
    const occType = slotState.occupant_type;
    const occName = slotState.occupant_name;

    if (item.kind === "trash_bin") {
      if (occType === "trash_bin") {
        continue;
      }
      if (occType === "labware" || occType === "module") {
        errors.push({
          code: "trash_slot_conflict",
          slot: slotName,
          observed: occType,
          message: `Protocol declares trash at ${slotName}, but observed occupant is ${occType}.`,
        });
        continue;
      }
      warnings.push({
        code: "trash_slot_unconfirmed",
        slot: slotName,
        message: `Protocol declares trash at ${slotName}; live snapshot could not confirm trash fixture (status=${status}).`,
      });
      continue;
    }

    if (item.kind === "module") {
      if (occType === "module") {
        continue;
      }
      if (occType === "labware") {
        errors.push({
          code: "module_slot_labware_conflict",
          slot: slotName,
          message: `Protocol declares a module at ${slotName}, but observed labware there.`,
        });
        continue;
      }
      warnings.push({
        code: "module_slot_unconfirmed",
        slot: slotName,
        message: `Protocol declares a module at ${slotName}; live snapshot could not confirm module placement (status=${status}).`,
      });
      continue;
    }

    // labware
    if (status === "occupied" && occType === "labware") {
      if (item.load_name && occName && !loadNamesCompatible(item.load_name, occName)) {
        errors.push({
          code: "labware_load_name_mismatch",
          slot: slotName,
          declared: item.load_name,
          observed: occName,
          message: `Slot ${slotName}: protocol load "${item.load_name}" vs observed "${occName}".`,
        });
      }
      continue;
    }

    if (status === "occupied" && (occType === "trash_bin" || occType === "module")) {
      errors.push({
        code: "labware_slot_wrong_occupant",
        slot: slotName,
        observed: occType,
        message: `Protocol expects labware at ${slotName}, but observed ${occType}.`,
      });
      continue;
    }

    if (status === "empty") {
      if (strictEmptyLabwareSlots) {
        errors.push({
          code: "expected_labware_slot_empty",
          slot: slotName,
          declared: item.load_name,
          message: `Protocol expects labware at ${slotName}, but the live deck snapshot shows this slot empty.`,
        });
      } else {
        warnings.push({
          code: "expected_labware_not_visible_pre_play",
          slot: slotName,
          declared: item.load_name,
          message: `Protocol expects labware at ${slotName}; deck snapshot is empty or not yet visible pre-play — confirm physical layout.`,
        });
      }
      continue;
    }

    const unknownLabware = {
      code: "labware_placement_unknown",
      slot: slotName,
      declared: item.load_name,
      message: `Protocol expects labware at ${slotName}; observed status is unknown — confirm physical layout.`,
    };
    if (strictEmptyLabwareSlots) {
      errors.push(unknownLabware);
    } else {
      warnings.push(unknownLabware);
    }
  }

  return { errors, warnings };
}
