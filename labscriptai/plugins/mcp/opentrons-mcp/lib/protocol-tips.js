const TIP_BINDING_MODES = new Set(["auto", "explicit", "starting_tip"]);

function stripPythonComments(source = "") {
  let out = "";
  let quote = null;
  let tripleQuote = null;
  let escape = false;

  for (let index = 0; index < source.length; index += 1) {
    const ch = source[index];
    const next3 = source.slice(index, index + 3);

    if (tripleQuote) {
      out += ch === "\n" ? "\n" : " ";
      if (next3 === tripleQuote) {
        out += "  ";
        index += 2;
        tripleQuote = null;
      }
      continue;
    }

    if (quote) {
      out += " ";
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

    if (next3 === "'''" || next3 === '"""') {
      tripleQuote = next3;
      out += "   ";
      index += 2;
      continue;
    }

    if (ch === "'" || ch === '"') {
      quote = ch;
      out += " ";
      continue;
    }

    if (ch === "#") {
      while (index < source.length && source[index] !== "\n") {
        out += " ";
        index += 1;
      }
      if (index < source.length) {
        out += "\n";
      }
      continue;
    }

    out += ch;
  }

  return out;
}

function isNameChar(value) {
  return /[A-Za-z0-9_]/.test(value || "");
}

function extractCallArgumentsWithName(source, functionName) {
  const calls = [];
  let cursor = 0;
  const token = functionName;

  while (cursor < source.length) {
    const found = source.indexOf(token, cursor);
    if (found === -1) {
      break;
    }

    const before = found > 0 ? source[found - 1] : "";
    const afterName = source[found + token.length] || "";
    const beforeAllowsMethod = before === "." || !isNameChar(before);
    if (!beforeAllowsMethod || isNameChar(afterName)) {
      cursor = found + token.length;
      continue;
    }

    let index = found + token.length;
    while (index < source.length && /\s/.test(source[index])) {
      index += 1;
    }
    if (source[index] !== "(") {
      cursor = index;
      continue;
    }

    index += 1;
    let depth = 1;
    let bracketDepth = 0;
    let braceDepth = 0;
    let quote = null;
    let tripleQuote = null;
    let escape = false;
    const start = index;

    for (; index < source.length; index += 1) {
      const ch = source[index];
      const next3 = source.slice(index, index + 3);

      if (tripleQuote) {
        if (next3 === tripleQuote) {
          index += 2;
          tripleQuote = null;
        }
        continue;
      }

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

      if (next3 === "'''" || next3 === '"""') {
        tripleQuote = next3;
        index += 2;
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
        if (depth === 0 && bracketDepth === 0 && braceDepth === 0) {
          calls.push(source.slice(start, index));
          cursor = index + 1;
          break;
        }
      } else if (ch === "[") {
        bracketDepth += 1;
      } else if (ch === "]") {
        bracketDepth = Math.max(0, bracketDepth - 1);
      } else if (ch === "{") {
        braceDepth += 1;
      } else if (ch === "}") {
        braceDepth = Math.max(0, braceDepth - 1);
      }
    }

    if (depth !== 0) {
      break;
    }
  }

  return calls;
}

function normalizeTipBindingMode(value) {
  const normalized = String(value || "").trim().toLowerCase();
  return TIP_BINDING_MODES.has(normalized) ? normalized : null;
}

export function classifyTipBindingModeDetail(protocolSource = "") {
  const source = stripPythonComments(String(protocolSource || ""));
  const startingTipDetected =
    /\bstarting_tip\s*=/.test(source) ||
    /\.\s*starting_tip\b/.test(source);

  const pickUpTipArgs = extractCallArgumentsWithName(source, "pick_up_tip");
  const explicitCalls = pickUpTipArgs.filter(args => args.trim().length > 0);
  const autoCalls = pickUpTipArgs.filter(args => args.trim().length === 0);

  if (startingTipDetected) {
    return {
      mode: "starting_tip",
      reason: "starting_tip_detected",
      starting_tip_detected: true,
      explicit_pick_up_tip_calls: explicitCalls.length,
      auto_pick_up_tip_calls: autoCalls.length,
      total_pick_up_tip_calls: pickUpTipArgs.length,
    };
  }

  if (explicitCalls.length > 0) {
    return {
      mode: "explicit",
      reason: "pick_up_tip_has_location_argument",
      starting_tip_detected: false,
      explicit_pick_up_tip_calls: explicitCalls.length,
      auto_pick_up_tip_calls: autoCalls.length,
      total_pick_up_tip_calls: pickUpTipArgs.length,
    };
  }

  return {
    mode: "auto",
    reason: autoCalls.length > 0 ? "pick_up_tip_without_arguments" : "no_explicit_tip_binding_detected",
    starting_tip_detected: false,
    explicit_pick_up_tip_calls: 0,
    auto_pick_up_tip_calls: autoCalls.length,
    total_pick_up_tip_calls: pickUpTipArgs.length,
  };
}

export function classifyTipBindingMode(protocolSource = "") {
  return classifyTipBindingModeDetail(protocolSource).mode;
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

function countSucceededPickUpTips(commands) {
  return unwrapCommandList(commands).filter(command => {
    const commandType = String(command?.commandType || command?.command_type || "");
    const status = String(command?.status || "").toLowerCase();
    return commandType === "pickUpTip" && status === "succeeded";
  }).length;
}

function normalizeWellName(value) {
  const match = String(value || "")
    .trim()
    .toUpperCase()
    .match(/([A-H](?:1[0-2]|[1-9]))$/);
  return match ? match[1] : null;
}

/**
 * Parse tip-budget hints from protocol comments/docstrings.
 * Supports lines like:
 *   tip_budget: pick_up_tip_count=3; tips_loaded=3 (B2.A1, B2.B1, B2.C1); spares=0
 */
export function parseProtocolTipBudget(protocolSource = "") {
  const source = String(protocolSource || "");
  const pickUpMatch = source.match(/pick_up_tip_count\s*=\s*(\d+)/i);
  const loadedMatch = source.match(/tips_loaded\s*=\s*(\d+)/i);
  const sparesMatch = source.match(/spares\s*=\s*(\d+)/i);

  const loadedWells = [];
  const wellsBlock =
    source.match(/tips_loaded\s*=\s*\d+\s*\(([^)]+)\)/i) ||
    source.match(/wells\s+((?:[A-D]\d+(?:\s*,\s*)?)+)\s+only/i);
  if (wellsBlock) {
    for (const token of wellsBlock[1].split(/,\s*/)) {
      const well = normalizeWellName(token);
      if (well) {
        loadedWells.push(well);
      }
    }
  }

  const tipsLoaded = loadedMatch ? Number(loadedMatch[1]) : loadedWells.length > 0 ? loadedWells.length : null;
  const spares = sparesMatch ? Number(sparesMatch[1]) : null;
  const constrained = tipsLoaded !== null || spares === 0 || loadedWells.length > 0;

  return {
    constrained,
    pick_up_tip_count: pickUpMatch ? Number(pickUpMatch[1]) : null,
    tips_loaded: tipsLoaded,
    spares,
    loaded_wells: loadedWells,
  };
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

/**
 * Decide whether a tip recovery retry can still finish remaining pick_up_tip steps.
 * Returns sufficient=false when deck tips cannot cover remaining protocol pickups.
 */
export function assessTipRecoveryBudget({
  protocolSource = "",
  commands = null,
  viableCandidates = [],
  tipBindingClassification = null,
} = {}) {
  const budget = parseProtocolTipBudget(protocolSource);
  const binding = tipBindingClassification || classifyTipBindingModeDetail(protocolSource);
  const totalPickups = budget.pick_up_tip_count ?? binding.total_pick_up_tip_calls ?? null;

  if (!totalPickups || totalPickups <= 0) {
    return {
      enforced: false,
      sufficient: true,
      reason: "no_pick_up_tip_budget_metadata",
      total_pickups: totalPickups,
    };
  }

  if (!budget.constrained) {
    return {
      enforced: false,
      sufficient: true,
      reason: "no_hard_tip_budget_constraint",
      total_pickups: totalPickups,
      parsed_budget: budget,
    };
  }

  const succeededPickups = countSucceededPickUpTips(commands);
  const pickupsRemaining = Math.max(0, totalPickups - succeededPickups);

  let availableCandidates = asArray(viableCandidates);
  if (budget.loaded_wells.length > 0) {
    const allowed = new Set(budget.loaded_wells);
    availableCandidates = availableCandidates.filter(candidate =>
      allowed.has(normalizeWellName(candidate?.well_name)),
    );
  } else if (budget.tips_loaded !== null) {
    availableCandidates = availableCandidates.slice(0, budget.tips_loaded);
  }

  const availableTips = availableCandidates.length;
  const sufficient = availableTips >= pickupsRemaining;

  return {
    enforced: true,
    sufficient,
    reason: sufficient ? "tip_budget_ok" : "tip_budget_insufficient_for_remaining_pickups",
    total_pickups: totalPickups,
    succeeded_pickups: succeededPickups,
    pickups_remaining: pickupsRemaining,
    available_tips: availableTips,
    parsed_budget: budget,
    allowed_viable_wells: availableCandidates.map(candidate => ({
      tiprack_slot: candidate.tiprack_slot,
      well_name: candidate.well_name,
    })),
    message: sufficient
      ? `Tip budget OK: ${availableTips} viable tip(s) for ${pickupsRemaining} remaining pickup(s).`
      : `Tip budget insufficient: ${availableTips} viable tip(s) on deck but ${pickupsRemaining} pickup(s) still required. Stop and escalate; do not auto-retry or resume.`,
  };
}

export function decideTipRecoveryRoute({
  errorLeaf,
  errorCategory,
  tipBindingMode,
} = {}) {
  const leaf = String(errorLeaf || errorCategory || "").toUpperCase();
  const category = String(errorCategory || "").toUpperCase();
  const mode = normalizeTipBindingMode(tipBindingMode);

  if (leaf === "OUT_OF_TIPS" || category === "OUT_OF_TIPS" || leaf === "TIP_RACK_EXHAUSTED") {
    return "human";
  }

  if (leaf !== "TIP_PHYSICALLY_MISSING" && category !== "TIP_PHYSICALLY_MISSING") {
    return "human";
  }

  if (mode === "auto") {
    return "fixit";
  }
  if (mode === "explicit" || mode === "starting_tip") {
    return "replan";
  }

  // Unclassified source: allow L0 fixit retry (next tip well) for missing-tip only.
  // Explicit/starting_tip modes are still enforced when protocol source is available.
  if (leaf === "TIP_PHYSICALLY_MISSING" || category === "TIP_PHYSICALLY_MISSING") {
    return "fixit";
  }

  return "human";
}
