/**
 * Protocol time-window detection for timed multi-phase protocols.
 *
 * Declared windows look like:
 *   TIME WINDOW: complete Phase 2 within 10 minutes of Phase 1 ...
 * including protocol.comment("...") strings that may span lines.
 *
 * Anchor selection (findTimeWindowAnchor):
 *   Prefer the last succeeded `dispenseInPlace` that completed before the
 *   second succeeded `pickUpTip` (Phase 1 ends before Phase 2 picks up a tip).
 *   If fewer than two succeeded pickups exist yet, use the last succeeded
 *   `dispenseInPlace` overall. If none exist, anchor fields stay null and
 *   expired stays false.
 */

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

function commandTypeOf(command) {
  return String(command?.commandType || command?.command_type || "").trim();
}

function commandStatusOf(command) {
  return String(command?.status || "").toLowerCase();
}

function commandCompletedAt(command) {
  return command?.completedAt || command?.completed_at || null;
}

function emptyTimeWindow({ declared = false, sourceLine = null, windowMinutes = null } = {}) {
  return {
    declared,
    window_minutes: windowMinutes,
    anchor_command_id: null,
    anchor_completed_at: null,
    elapsed_minutes: null,
    expired: false,
    source_line: sourceLine,
  };
}

/**
 * Parse TIME WINDOW declarations from protocol comments / comment() strings.
 * Matches "within N minute(s)|min" after a TIME WINDOW marker (case-insensitive).
 */
export function parseProtocolTimeWindow(protocolSource = "") {
  const source = String(protocolSource || "");
  // Flatten adjacent string literals inside protocol.comment(...) so multi-line
  // comments still match "within N minutes".
  const flattened = source.replace(/"\s*\n\s*"/g, " ").replace(/'\s*\n\s*'/g, " ");
  const windowMatch = flattened.match(
    /TIME\s+WINDOW\b[\s\S]{0,240}?within\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|min)\b/i,
  );
  if (!windowMatch) {
    return emptyTimeWindow({ declared: false });
  }

  const windowMinutes = Number(windowMatch[1]);
  const sourceLine = windowMatch[0].replace(/\s+/g, " ").trim();
  return {
    declared: true,
    window_minutes: Number.isFinite(windowMinutes) ? windowMinutes : null,
    anchor_command_id: null,
    anchor_completed_at: null,
    elapsed_minutes: null,
    expired: false,
    source_line: sourceLine,
  };
}

/**
 * Locate the Phase-1 anchor command among run history commands.
 * See module docstring for the selection rule.
 */
export function findTimeWindowAnchor(commands = []) {
  const list = unwrapCommandList(commands);
  const succeededPickUpIndexes = [];
  for (let index = 0; index < list.length; index += 1) {
    const command = list[index];
    if (commandTypeOf(command) === "pickUpTip" && commandStatusOf(command) === "succeeded") {
      succeededPickUpIndexes.push(index);
    }
  }

  const phase1EndExclusive =
    succeededPickUpIndexes.length >= 2 ? succeededPickUpIndexes[1] : list.length;

  let anchor = null;
  for (let index = 0; index < phase1EndExclusive; index += 1) {
    const command = list[index];
    if (commandTypeOf(command) === "dispenseInPlace" && commandStatusOf(command) === "succeeded") {
      anchor = command;
    }
  }

  if (!anchor) {
    return {
      anchor_command_id: null,
      anchor_completed_at: null,
    };
  }

  return {
    anchor_command_id: anchor.id || anchor.command_id || null,
    anchor_completed_at: commandCompletedAt(anchor),
  };
}

/**
 * Assess whether a declared protocol time window has expired relative to now.
 */
export function assessTimeWindow({
  protocolSource = "",
  commands = null,
  now = null,
} = {}) {
  const parsed = parseProtocolTimeWindow(protocolSource);
  if (!parsed.declared || parsed.window_minutes === null) {
    return emptyTimeWindow({ declared: parsed.declared, sourceLine: parsed.source_line });
  }

  const anchor = findTimeWindowAnchor(commands);
  const result = {
    ...parsed,
    anchor_command_id: anchor.anchor_command_id,
    anchor_completed_at: anchor.anchor_completed_at,
    elapsed_minutes: null,
    expired: false,
  };

  if (!anchor.anchor_completed_at) {
    return result;
  }

  const anchorMs = Date.parse(anchor.anchor_completed_at);
  if (!Number.isFinite(anchorMs)) {
    return result;
  }

  const nowMs = now === null || now === undefined ? Date.now() : Number(now);
  const elapsedMinutes = Math.max(0, (nowMs - anchorMs) / 60000);
  result.elapsed_minutes = Number(elapsedMinutes.toFixed(3));
  result.expired = elapsedMinutes > parsed.window_minutes;
  return result;
}
