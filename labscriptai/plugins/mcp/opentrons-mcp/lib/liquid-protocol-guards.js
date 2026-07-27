function stripComment(line) {
  let quote = null;
  let escaped = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === "\\") {
      escaped = true;
      continue;
    }
    if ((char === "\"" || char === "'") && !quote) {
      quote = char;
      continue;
    }
    if (char === quote) {
      quote = null;
      continue;
    }
    if (char === "#" && !quote) {
      return line.slice(0, index);
    }
  }
  return line;
}

function collectCalls(protocolSource, pattern) {
  return String(protocolSource || "")
    .split(/\r?\n/)
    .map((line, index) => ({ line, code: stripComment(line), line_number: index + 1 }))
    .filter(item => pattern.test(item.code))
    .map(item => ({
      line_number: item.line_number,
      line: item.line.trim(),
    }));
}

export function analyzeLiquidProtocolGuards(protocolSource) {
  const requireLiquidPresenceCalls = collectCalls(
    protocolSource,
    /\.require_liquid_presence\s*\(/,
  );
  const aspirateCalls = collectCalls(protocolSource, /\.aspirate\s*\(/);
  const dispenseCalls = collectCalls(protocolSource, /\.dispense\s*\(/);
  const firstGuardLine = requireLiquidPresenceCalls[0]?.line_number || null;
  const firstAspirateLine = aspirateCalls[0]?.line_number || null;
  const noAspirateOrDispense = aspirateCalls.length === 0 && dispenseCalls.length === 0;
  const firstAspirateGuarded =
    firstAspirateLine === null ||
    (firstGuardLine !== null && firstGuardLine < firstAspirateLine);

  return {
    status: firstAspirateGuarded ? "pass" : "blocked",
    require_liquid_presence_count: requireLiquidPresenceCalls.length,
    aspirate_count: aspirateCalls.length,
    dispense_count: dispenseCalls.length,
    no_aspirate_or_dispense: noAspirateOrDispense,
    first_require_liquid_presence_line: firstGuardLine,
    first_aspirate_line: firstAspirateLine,
    first_aspirate_guarded: firstAspirateGuarded,
    require_liquid_presence_calls: requireLiquidPresenceCalls,
    aspirate_calls: aspirateCalls,
    dispense_calls: dispenseCalls,
    blocked_reason: firstAspirateGuarded
      ? null
      : "first_aspirate_occurs_before_require_liquid_presence",
  };
}
