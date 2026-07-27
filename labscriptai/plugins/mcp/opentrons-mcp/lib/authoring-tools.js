import fs from "fs";
import path from "path";

import { PLUGIN_ROOT } from "./paths.js";

const FLEX_PIPETTE_MAX_VOLUME = {
  flex_1channel_50: 50,
  flex_8channel_50: 50,
  flex_1channel_1000: 1000,
  flex_8channel_1000: 1000,
  flex_96channel_1000: 1000,
};

function normalizeText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function normalizeLoadName(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/_/g, "-");
}

function versionKey(pathname) {
  const parsed = Number.parseInt(path.basename(pathname, ".json"), 10);
  return Number.isFinite(parsed) ? parsed : -1;
}

function toFiniteNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function findLabwareDefinitionsDir() {
  const envDir = process.env.OPENTRONS_LABWARE_DEFINITIONS_DIR;
  if (envDir && fs.existsSync(envDir)) {
    return envDir;
  }

  let current = PLUGIN_ROOT;
  for (let i = 0; i < 10; i += 1) {
    const venv = path.join(current, ".venv");
    if (fs.existsSync(venv)) {
      for (const entry of fs.readdirSync(path.join(venv, "lib"), { withFileTypes: true })) {
        if (!entry.isDirectory() || !entry.name.startsWith("python")) {
          continue;
        }
        const candidate = path.join(
          venv,
          "lib",
          entry.name,
          "site-packages",
          "opentrons_shared_data",
          "data",
          "labware",
          "definitions",
          "2",
        );
        if (fs.existsSync(candidate)) {
          return candidate;
        }
      }
    }
    current = path.dirname(current);
  }

  return null;
}

function loadLatestDefinition(definitionsDir, entryName) {
  const entryDir = path.join(definitionsDir, entryName);
  if (!fs.existsSync(entryDir)) {
    return null;
  }
  const jsonFiles = fs
    .readdirSync(entryDir)
    .filter((file) => file.endsWith(".json"))
    .sort((a, b) => versionKey(a) - versionKey(b));
  const chosen = jsonFiles.at(-1);
  if (!chosen) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(path.join(entryDir, chosen), "utf8"));
  } catch {
    return null;
  }
}

function loadDefinitionRecordByLoadName(definitionsDir, loadName) {
  const normalizedQuery = normalizeLoadName(loadName);
  for (const entry of fs.readdirSync(definitionsDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) {
      continue;
    }
    const defn = loadLatestDefinition(definitionsDir, entry.name);
    if (!defn || typeof defn !== "object") {
      continue;
    }
    const params = defn.parameters || {};
    const meta = defn.metadata || {};
    const candidateLoadName = String(params.loadName || entry.name);
    if (normalizeLoadName(candidateLoadName) !== normalizedQuery) {
      continue;
    }
    return {
      definition: defn,
      loadName: candidateLoadName,
      displayName: String(meta.displayName || ""),
      displayCategory: String(meta.displayCategory || ""),
      namespace: params.namespace || null,
      version: params.version || null,
      isTiprack: Boolean(params.isTiprack),
    };
  }
  return null;
}

function scoreLabwareMatch(query, loadName, displayName, displayCategory) {
  const q = normalizeText(query);
  const load = normalizeText(loadName);
  const display = normalizeText(displayName);
  const category = normalizeText(displayCategory);
  if (!q) return 0;
  if (q === load) return 3;
  if (load.includes(q)) return 2;
  if (display.includes(q) || category.includes(q)) return 1;
  return 0;
}

export function searchLabwareDefinitions(query, { limit = 10 } = {}) {
  const definitionsDir = findLabwareDefinitionsDir();
  if (!definitionsDir) {
    return {
      ok: false,
      error: "Could not locate opentrons_shared_data labware definitions.",
      query,
      search_root: null,
      results: [],
    };
  }

  const normalized = normalizeText(query);
  const results = [];

  for (const entry of fs.readdirSync(definitionsDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) {
      continue;
    }
    const defn = loadLatestDefinition(definitionsDir, entry.name);
    if (!defn || typeof defn !== "object") {
      continue;
    }

    const params = defn.parameters || {};
    const meta = defn.metadata || {};
    const loadName = String(params.loadName || entry.name);
    const displayName = String(meta.displayName || "");
    const displayCategory = String(meta.displayCategory || "");
    const score = scoreLabwareMatch(normalized, loadName, displayName, displayCategory);
    if (!score) {
      continue;
    }

    const wells = defn.wells || {};
    const wellCount = wells && typeof wells === "object" ? Object.keys(wells).length : 0;
    const maxVolumeUl = wells && typeof wells === "object"
      ? Math.max(
          0,
          ...Object.values(wells)
            .filter((well) => well && typeof well === "object")
            .map((well) => Number(well.totalLiquidVolume || 0)),
        )
      : 0;

    results.push({
      loadName,
      displayName,
      displayCategory,
      namespace: params.namespace || null,
      version: params.version || null,
      isTiprack: Boolean(params.isTiprack),
      wellCount,
      maxVolumeUl,
      _score: score,
    });
  }

  results.sort((a, b) => {
    if (b._score !== a._score) return b._score - a._score;
    return a.loadName.localeCompare(b.loadName);
  });

  const trimmed = results.slice(0, Math.max(1, limit)).map((entry) => {
    const copy = { ...entry };
    delete copy._score;
    return copy;
  });

  return {
    ok: true,
    query,
    search_root: definitionsDir,
    count: trimmed.length,
    results: trimmed,
  };
}

export function validateLabwareLoadName(loadName, { limit = 5 } = {}) {
  const query = String(loadName || "").trim();
  const search = searchLabwareDefinitions(query, { limit });
  const normalizedQuery = normalizeLoadName(query);
  const exactMatches = search.results.filter(
    (entry) => normalizeLoadName(entry.loadName) === normalizedQuery,
  );

  return {
    ...search,
    known: exactMatches.length > 0,
    exact_matches: exactMatches,
    suggestions: search.results,
  };
}

function summarizeRepresentativeWell(definition) {
  const wells = definition?.wells || {};
  const sample = Object.values(wells).find((well) => well && typeof well === "object");
  if (!sample) {
    return null;
  }

  const diameter = toFiniteNumber(sample.diameter);
  const xDimension = toFiniteNumber(sample.xDimension);
  const yDimension = toFiniteNumber(sample.yDimension);
  const depth = toFiniteNumber(sample.depth);
  const totalLiquidVolume = toFiniteNumber(sample.totalLiquidVolume);
  const shape = diameter !== null
    ? "circular"
    : xDimension !== null && yDimension !== null
      ? "rectangular"
      : "unknown";

  return {
    shape,
    depth_mm: depth,
    diameter_mm: diameter,
    x_dimension_mm: xDimension,
    y_dimension_mm: yDimension,
    total_liquid_volume_ul: totalLiquidVolume,
  };
}

function estimateDeadVolumeHint(definition, representativeWell) {
  const params = definition?.parameters || {};
  const meta = definition?.metadata || {};
  const normalizedLabel = normalizeText([params.loadName, meta.displayName, meta.displayCategory].join(" "));
  const wellCount = Object.keys(definition?.wells || {}).length;
  const capacity = representativeWell?.total_liquid_volume_ul ?? null;
  const isTiprack = Boolean(params.isTiprack) || normalizedLabel.includes("tip rack") || normalizedLabel.includes("tiprack");

  if (isTiprack) {
    return {
      estimated_ul: 0,
      range_ul: [0, 0],
      reason: "Tip racks do not hold source liquid, so dead-volume guidance does not apply.",
    };
  }

  if (normalizedLabel.includes("reservoir")) {
    if (wellCount === 1 && capacity !== null && capacity >= 100000) {
      return {
        estimated_ul: 19000,
        range_ul: [15000, 25000],
        reason: "Single-well reservoir rule of thumb: roughly 10% of capacity remains unusable.",
      };
    }
    if (wellCount >= 12 && capacity !== null && capacity >= 10000) {
      return {
        estimated_ul: 1900,
        range_ul: [1500, 2500],
        reason: "12-well 15 mL reservoir rule of thumb.",
      };
    }
  }

  if (normalizedLabel.includes("tube")) {
    if (capacity !== null && capacity >= 40000) {
      return {
        estimated_ul: 500,
        range_ul: [400, 600],
        reason: "50 mL tube rule of thumb.",
      };
    }
    if (capacity !== null && capacity >= 10000) {
      return {
        estimated_ul: 200,
        range_ul: [150, 250],
        reason: "15 mL tube rule of thumb.",
      };
    }
    if (capacity !== null && capacity <= 2000) {
      return {
        estimated_ul: 10,
        range_ul: [5, 15],
        reason: "Microcentrifuge tube rule of thumb.",
      };
    }
  }

  if (wellCount >= 96 && capacity !== null) {
    if (representativeWell?.shape === "circular") {
      return {
        estimated_ul: 8,
        range_ul: [5, 10],
        reason: "96-well circular/v-bottom plate rule of thumb.",
      };
    }
    return {
      estimated_ul: 18,
      range_ul: [15, 20],
      reason: "96-well flat or rectangular plate rule of thumb.",
    };
  }

  return null;
}

function extractProtocolSource(args = {}) {
  if (typeof args.protocol_source === "string" && args.protocol_source.trim()) {
    return args.protocol_source;
  }
  if (typeof args.file_path === "string" && args.file_path.trim()) {
    const resolved = path.resolve(args.file_path);
    if (!fs.existsSync(resolved)) {
      throw new Error(`protocol file not found: ${resolved}`);
    }
    return fs.readFileSync(resolved, "utf8");
  }
  throw new Error("provide either protocol_source or file_path");
}

function countMatches(source, pattern) {
  return (source.match(pattern) || []).length;
}

function extractCallArgumentsWithPrefix(source, prefix) {
  const out = [];
  let cursor = 0;

  while (cursor < source.length) {
    const found = source.indexOf(prefix, cursor);
    if (found === -1) {
      break;
    }

    const before = found > 0 ? source[found - 1] : "";
    const after = source[found + prefix.length] || "";
    if ((before && /[A-Za-z0-9_]/.test(before)) || (after && /[A-Za-z0-9_]/.test(after))) {
      cursor = found + prefix.length;
      continue;
    }

    let index = found + prefix.length;
    while (index < source.length && /\s/.test(source[index])) {
      index += 1;
    }
    if (source[index] !== "(") {
      cursor = index;
      continue;
    }

    index += 1;
    let depth = 1;
    let quote = null;
    let escape = false;
    const start = index;

    for (; index < source.length; index += 1) {
      const ch = source[index];
      if (quote) {
        if (escape) {
          escape = false;
          continue;
        }
        if (ch === "\\") {
          escape = true;
          continue;
        }
        if (ch === quote) {
          quote = null;
        }
        continue;
      }

      if (ch === "'" || ch === '"') {
        quote = ch;
        continue;
      }
      if (ch === "(") {
        depth += 1;
      } else if (ch === ")") {
        depth -= 1;
        if (depth === 0) {
          out.push(source.slice(start, index));
          cursor = index + 1;
          break;
        }
      }
    }

    if (depth !== 0) {
      break;
    }
  }

  return out;
}

function extractCallArguments(source, functionName) {
  return extractCallArgumentsWithPrefix(source, functionName);
}

function extractQualifiedCallArguments(source, qualifier, functionName) {
  return extractCallArgumentsWithPrefix(source, `${qualifier}.${functionName}`);
}

function extractPipetteBindings(source) {
  const bindings = [];
  const regex = /(^|[^A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:[A-Za-z_][A-Za-z0-9_]*\s*\.\s*)?load_instrument\s*\(\s*["']([^"']+)["']/g;
  let match;
  while ((match = regex.exec(source)) !== null) {
    bindings.push({
      variable_name: match[2],
      instrument_name: match[3],
    });
  }
  return bindings;
}

function splitTopLevelArguments(argText) {
  const out = [];
  let current = "";
  let depthParen = 0;
  let depthBracket = 0;
  let depthBrace = 0;
  let quote = null;
  let escape = false;

  for (let index = 0; index < argText.length; index += 1) {
    const ch = argText[index];
    if (quote) {
      current += ch;
      if (escape) {
        escape = false;
        continue;
      }
      if (ch === "\\") {
        escape = true;
        continue;
      }
      if (ch === quote) {
        quote = null;
      }
      continue;
    }

    if (ch === "'" || ch === '"') {
      quote = ch;
      current += ch;
      continue;
    }

    if (ch === "(") {
      depthParen += 1;
    } else if (ch === ")") {
      depthParen = Math.max(0, depthParen - 1);
    } else if (ch === "[") {
      depthBracket += 1;
    } else if (ch === "]") {
      depthBracket = Math.max(0, depthBracket - 1);
    } else if (ch === "{") {
      depthBrace += 1;
    } else if (ch === "}") {
      depthBrace = Math.max(0, depthBrace - 1);
    }

    if (ch === "," && depthParen === 0 && depthBracket === 0 && depthBrace === 0) {
      if (current.trim()) {
        out.push(current.trim());
      }
      current = "";
      continue;
    }

    current += ch;
  }

  if (current.trim()) {
    out.push(current.trim());
  }

  return out;
}

function extractFirstNumericVolume(argText) {
  const named = argText.match(/(?:^|[,(]\s*)volume\s*=\s*([0-9]+(?:\.[0-9]+)?)/i);
  if (named) {
    return Number(named[1]);
  }
  const positional = argText.match(/^\s*([0-9]+(?:\.[0-9]+)?)(?=\s*[,\)])?/);
  if (positional) {
    return Number(positional[1]);
  }
  return null;
}

function extractPipetteNames(source) {
  const names = new Set();
  const regex = /load_instrument\s*\(\s*["']([^"']+)["']/g;
  let match;
  while ((match = regex.exec(source)) !== null) {
    names.add(match[1]);
  }
  return [...names];
}

function countTipRacks(source) {
  return countMatches(source, /load_labware\s*\(\s*["'][^"']*tiprack[^"']*["']/gi);
}

function countListEntries(expression) {
  const trimmed = String(expression || "").trim();
  if (!trimmed.startsWith("[") || !trimmed.endsWith("]")) {
    return 1;
  }
  const inner = trimmed.slice(1, -1);
  const items = splitTopLevelArguments(inner);
  return Math.max(1, items.length);
}

function estimateTipUsageForCall(functionName, argText) {
  const newTipNever = /\bnew_tip\s*=\s*["']never["']/i.test(argText);
  if (newTipNever) {
    return 0;
  }

  const newTipOnce = /\bnew_tip\s*=\s*["']once["']/i.test(argText);
  if (newTipOnce) {
    return 1;
  }

  const positionalArgs = splitTopLevelArguments(argText);
  if (functionName === "transfer" && positionalArgs.length >= 3) {
    const destinationExpr = positionalArgs[2];
    return countListEntries(destinationExpr);
  }

  return 1;
}

function countTipBearingCalls(source) {
  let count = 0;
  for (const fn of ["transfer_with_liquid_class", "transfer", "distribute", "consolidate"]) {
    for (const argText of extractCallArguments(source, fn)) {
      count += estimateTipUsageForCall(fn, argText);
    }
  }
  return count;
}

function estimatePrecisionWarnings(source, pipetteNames) {
  const warnings = [];
  const pipetteBindings = extractPipetteBindings(source)
    .map((binding) => ({
      ...binding,
      max: FLEX_PIPETTE_MAX_VOLUME[String(binding.instrument_name).toLowerCase()] || null,
    }))
    .filter((item) => item.max !== null);

  if (pipetteBindings.length === 0) {
    return warnings;
  }

  for (const fn of ["transfer_with_liquid_class", "transfer", "distribute", "consolidate"]) {
    for (const pipette of pipetteBindings) {
      for (const argText of extractQualifiedCallArguments(source, pipette.variable_name, fn)) {
        const volume = extractFirstNumericVolume(argText);
        if (volume === null) {
          continue;
        }
        const threshold = pipette.max * 0.1;
        if (volume < threshold) {
          warnings.push({
            pipette_name: pipette.instrument_name,
            variable_name: pipette.variable_name,
            max_volume_ul: pipette.max,
            threshold_ul: Number(threshold.toFixed(2)),
            volume_ul: volume,
            warning:
              `${volume} uL is below the recommended 10% floor for ${pipette.instrument_name} (max ${pipette.max} uL).`,
          });
        }
      }
    }
  }

  return warnings;
}

export function estimateTipBudget(args = {}) {
  const source = extractProtocolSource(args);
  const pickUpTipCalls = countMatches(source, /\bpick_up_tip\s*\(/g);
  const dropTipCalls = countMatches(source, /\bdrop_tip\s*\(/g);
  const highLevelTipCalls = countTipBearingCalls(source);
  const tipRackCount = Number.isFinite(Number(args.tip_rack_count))
    ? Number(args.tip_rack_count)
    : countTipRacks(source);
  const tipRackCapacity = Number.isFinite(Number(args.tip_rack_capacity))
    ? Number(args.tip_rack_capacity)
    : 96;
  const estimatedTipUses = pickUpTipCalls + highLevelTipCalls;
  const capacity = tipRackCount > 0 ? tipRackCount * tipRackCapacity : null;
  const pipetteNames = extractPipetteNames(source);
  const precisionWarnings = estimatePrecisionWarnings(source, pipetteNames);

  return {
    ok: true,
    estimated_tip_uses: estimatedTipUses,
    explicit_pick_up_tip_calls: pickUpTipCalls,
    explicit_drop_tip_calls: dropTipCalls,
    transfer_like_calls: highLevelTipCalls,
    detected_pipettes: pipetteNames,
    tip_rack_count: tipRackCount,
    tip_rack_capacity: tipRackCapacity,
    capacity,
    within_budget: capacity === null ? null : estimatedTipUses <= capacity,
    precision_warnings: precisionWarnings,
    note:
      "Heuristic estimate only. High-level transfer/distribute/consolidate calls are counted as tip-bearing unless new_tip='never'; transfer() with a list of destinations is counted per destination, new_tip='once' is honored, and precision warnings only follow pipette objects that actually make the call.",
  };
}

export function inspectLabwareDefinition(loadName, { limit = 5 } = {}) {
  const query = String(loadName || "").trim();
  const search = validateLabwareLoadName(query, { limit });
  const exactMatch = search.exact_matches[0];
  if (!exactMatch) {
    return {
      ...search,
      known: false,
      exact_match: null,
      definition: null,
      geometry: null,
      dead_volume_hint: null,
    };
  }

  const definitionsDir = findLabwareDefinitionsDir();
  if (!definitionsDir) {
    return {
      ...search,
      known: false,
      exact_match: exactMatch,
      definition: null,
      geometry: null,
      dead_volume_hint: null,
      error: "Could not locate opentrons_shared_data labware definitions.",
    };
  }

  const record = loadDefinitionRecordByLoadName(definitionsDir, exactMatch.loadName);
  if (!record) {
    return {
      ...search,
      known: false,
      exact_match: exactMatch,
      definition: null,
      geometry: null,
      dead_volume_hint: null,
      error: "Exact load name was found in search results but the definition file could not be loaded.",
    };
  }

  const representativeWell = summarizeRepresentativeWell(record.definition);
  const deadVolumeHint = estimateDeadVolumeHint(record.definition, representativeWell);
  const wellCount = Object.keys(record.definition.wells || {}).length;

  return {
    ...search,
    known: true,
    exact_match: exactMatch,
    definition: {
      loadName: record.loadName,
      displayName: record.displayName,
      displayCategory: record.displayCategory,
      namespace: record.namespace,
      version: record.version,
      isTiprack: record.isTiprack,
      wellCount,
    },
    geometry: {
      well_count: wellCount,
      representative_well: representativeWell,
      dead_volume_hint: deadVolumeHint,
    },
  };
}
