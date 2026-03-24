import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SESSION_STATE_DIR = path.resolve(__dirname, "../data/session-state");

export const DEFAULT_SESSION_ID = "default";
export const FLEX_SLOT_NAMES = [
  "A1",
  "A2",
  "A3",
  "B1",
  "B2",
  "B3",
  "C1",
  "C2",
  "C3",
  "D1",
  "D2",
  "D3",
];

export const COLUMN_MAJOR_WELL_ORDER_96 = Array.from({ length: 12 }, (_, columnIndex) =>
  ["A", "B", "C", "D", "E", "F", "G", "H"].map(row => `${row}${columnIndex + 1}`),
).flat();

function sanitizeSessionId(sessionId = DEFAULT_SESSION_ID) {
  return String(sessionId || DEFAULT_SESSION_ID).replace(/[^a-zA-Z0-9._-]/g, "_");
}

function buildDefaultSessionState(sessionId = DEFAULT_SESSION_ID) {
  return {
    session_id: sanitizeSessionId(sessionId),
    state_revision: 0,
    robot_serial: null,
    last_run_id: null,
    needs_reconciliation: false,
    deck: {
      slots: {},
    },
    pipettes: {},
    tip_tracking: {
      tipracks: {},
    },
    cleanup: {
      pending_actions: [],
      auto_home_allowed: null,
    },
    updated_at: new Date().toISOString(),
  };
}

function ensureStateDirectory() {
  fs.mkdirSync(SESSION_STATE_DIR, { recursive: true });
}

function sessionStatePath(sessionId = DEFAULT_SESSION_ID) {
  return path.join(SESSION_STATE_DIR, `${sanitizeSessionId(sessionId)}.json`);
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function uniqueStrings(values = []) {
  return [...new Set(values.filter(Boolean).map(value => String(value)))];
}

export function uniqueSessionStrings(values = []) {
  return uniqueStrings(values);
}

export function readSessionState(sessionId = DEFAULT_SESSION_ID) {
  ensureStateDirectory();
  const filePath = sessionStatePath(sessionId);
  const fallback = buildDefaultSessionState(sessionId);

  if (!fs.existsSync(filePath)) {
    return fallback;
  }

  try {
    const parsed = JSON.parse(fs.readFileSync(filePath, "utf8"));
    return {
      ...fallback,
      ...parsed,
      deck: {
        ...fallback.deck,
        ...(parsed.deck || {}),
        slots: {
          ...fallback.deck.slots,
          ...(parsed.deck?.slots || {}),
        },
      },
      pipettes: {
        ...fallback.pipettes,
        ...(parsed.pipettes || {}),
      },
      tip_tracking: {
        ...fallback.tip_tracking,
        ...(parsed.tip_tracking || {}),
        tipracks: {
          ...fallback.tip_tracking.tipracks,
          ...(parsed.tip_tracking?.tipracks || {}),
        },
      },
      cleanup: {
        ...fallback.cleanup,
        ...(parsed.cleanup || {}),
        pending_actions: uniqueStrings(parsed.cleanup?.pending_actions || []),
      },
    };
  } catch {
    return fallback;
  }
}

export function writeSessionState(sessionState) {
  ensureStateDirectory();
  const normalized = {
    ...buildDefaultSessionState(sessionState?.session_id),
    ...clone(sessionState),
    session_id: sanitizeSessionId(sessionState?.session_id),
    updated_at: new Date().toISOString(),
  };
  fs.writeFileSync(sessionStatePath(normalized.session_id), `${JSON.stringify(normalized, null, 2)}\n`);
  return normalized;
}

export function updateSessionState(sessionId, updater) {
  const currentState = readSessionState(sessionId);
  const draft = clone(currentState);
  const nextState = updater(draft) || draft;
  nextState.session_id = sanitizeSessionId(nextState.session_id || currentState.session_id || sessionId);
  nextState.state_revision = Number(currentState.state_revision || 0) + 1;
  nextState.updated_at = new Date().toISOString();
  return writeSessionState(nextState);
}

export function mutateSessionState(sessionId, mutator) {
  const currentState = readSessionState(sessionId);
  const draft = clone(currentState);
  const before = JSON.stringify(draft);
  const mutated = mutator(draft) || draft;
  const after = JSON.stringify(mutated);

  if (before === after) {
    return {
      state: currentState,
      changed: false,
    };
  }

  return {
    state: updateSessionState(sessionId, () => mutated),
    changed: true,
  };
}

export function ensureTiprackState(sessionState, { slotName, loadName = null } = {}) {
  if (!slotName) {
    return null;
  }

  sessionState.tip_tracking ||= { tipracks: {} };
  sessionState.tip_tracking.tipracks ||= {};

  const current = sessionState.tip_tracking.tipracks[slotName] || {
    slot_name: slotName,
    load_name: loadName,
    search_order: COLUMN_MAJOR_WELL_ORDER_96,
    missing_wells: [],
    depleted_wells: [],
    unknown_blocked_wells: [],
    last_suggested_well: null,
  };

  current.load_name ||= loadName;
  current.search_order = Array.isArray(current.search_order) && current.search_order.length > 0
    ? current.search_order
    : COLUMN_MAJOR_WELL_ORDER_96;
  current.missing_wells = uniqueStrings(current.missing_wells);
  current.depleted_wells = uniqueStrings(current.depleted_wells);
  current.unknown_blocked_wells = uniqueStrings(current.unknown_blocked_wells);

  sessionState.tip_tracking.tipracks[slotName] = current;
  return current;
}

export function markTipWellStatus(sessionState, { slotName, wellName, status } = {}) {
  if (!slotName || !wellName || !status) {
    return null;
  }

  const tiprackState = ensureTiprackState(sessionState, { slotName });
  const groups = {
    missing: "missing_wells",
    depleted: "depleted_wells",
    "unknown-blocked": "unknown_blocked_wells",
  };
  const targetKey = groups[status];

  if (!targetKey) {
    return tiprackState;
  }

  for (const key of Object.values(groups)) {
    tiprackState[key] = uniqueStrings(
      (tiprackState[key] || []).filter(existingWell => existingWell !== wellName),
    );
  }

  tiprackState[targetKey] = uniqueStrings([...(tiprackState[targetKey] || []), wellName]);
  return tiprackState;
}

export function setDeckSlotState(sessionState, slotName, slotState) {
  if (!slotName) {
    return;
  }
  sessionState.deck ||= { slots: {} };
  sessionState.deck.slots ||= {};
  sessionState.deck.slots[slotName] = {
    slot_name: slotName,
    ...(slotState || {}),
  };
}

export function setPipetteState(sessionState, mount, pipetteState) {
  if (!mount) {
    return;
  }
  sessionState.pipettes ||= {};
  sessionState.pipettes[mount] = {
    ...(sessionState.pipettes[mount] || {}),
    ...(pipetteState || {}),
  };
}

export function setCleanupState(sessionState, cleanupState) {
  sessionState.cleanup ||= {
    pending_actions: [],
    auto_home_allowed: null,
  };
  sessionState.cleanup = {
    ...sessionState.cleanup,
    ...(cleanupState || {}),
    pending_actions: uniqueStrings(
      cleanupState?.pending_actions ?? sessionState.cleanup.pending_actions ?? [],
    ),
  };
}
