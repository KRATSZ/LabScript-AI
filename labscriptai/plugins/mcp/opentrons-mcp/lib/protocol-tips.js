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

  return "human";
}
