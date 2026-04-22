import fs from "fs";
import path from "path";

import { buildHomeSafetyResult, buildObservedDeckState } from "./decision.js";
import {
  compareDeclaredLoadsToObservedDeck,
  extractDeclaredProtocolLoads,
  extractRobotTypeFromProtocolSource,
} from "./protocol-deck.js";

function isOt2RobotType(robotType) {
  const t = String(robotType || "").toLowerCase();
  return t.includes("ot-2") || t.includes("ot2");
}

/**
 * Build a structured preflight result before playing a protocol run.
 * Does not mutate session state.
 *
 * @param {object} [options]
 * @param {object} [options.robotStatusSnapshot] - `readRobotStatus().data` (buildRobotStatusSnapshot)
 * @param {object} [options.deckConfigurationPayload] - raw `/deck_configuration` JSON (same as `readRobotStatus().hardwareSnapshot.deck_configuration`)
 * @param {object} [options.modulesPayload] - raw `/modules` JSON (same as `readModuleStatus().hardwareSnapshot.modules`)
 * @param {object} [options.moduleStatusSnapshot] - `readModuleStatus().data` (module blockers / summaries)
 */
export function buildPreflightRunSetupResult({
  filePath,
  sessionState = {},
  robotStatusSnapshot = {},
  deckConfigurationPayload = null,
  modulesPayload = null,
  moduleStatusSnapshot = {},
  runRecord = null,
  skipDeckDiff = false,
  strictEmptyLabwareSlots = false,
} = {}) {
  const warnings = [];
  const errors = [];

  if (sessionState.needs_reconciliation === true) {
    errors.push({
      code: "needs_reconciliation",
      message: "Session needs_reconciliation is true; run reconcile_state before playing a protocol.",
    });
  }

  if (robotStatusSnapshot.ready_for_physical_action === false) {
    errors.push({
      code: "robot_not_ready",
      blockers: robotStatusSnapshot.blockers || [],
      message: "Robot reports blockers; clear door/estop/instrument issues before play.",
    });
  }

  const moduleBlockers = moduleStatusSnapshot.blockers || [];
  if (Array.isArray(moduleBlockers) && moduleBlockers.length > 0) {
    warnings.push({
      code: "module_blockers_present",
      blockers: moduleBlockers,
      message: "One or more modules are not ready; verify this is acceptable for the protocol.",
    });
  }

  const homeSafety = buildHomeSafetyResult({
    robotStatusSnapshot,
    sessionState,
  });
  if (homeSafety.auto_home_allowed === false) {
    warnings.push({
      code: "home_not_auto_safe",
      blockers: homeSafety.blockers || [],
      minimum_cleanup_actions: homeSafety.minimum_cleanup_actions || [],
      message: "Live state suggests homing/cleanup may be unsafe; protocol play may still proceed, but review cleanup and is_home_safe before homing.",
    });
  }

  let declaredLoads = [];
  let robotType = null;
  let deckDiff = null;

  if (!skipDeckDiff && filePath) {
    const resolved = path.resolve(filePath);
    let source;
    try {
      source = fs.readFileSync(resolved, "utf8");
    } catch {
      errors.push({
        code: "protocol_file_unreadable",
        path: resolved,
        message: `Could not read protocol file for deck preflight: ${resolved}`,
      });
    }

    if (source) {
      robotType = extractRobotTypeFromProtocolSource(source);
      if (isOt2RobotType(robotType)) {
        warnings.push({
          code: "deck_diff_skipped_ot2",
          robot_type: robotType,
          message: "Deck load diff is skipped for OT-2 protocols in this MCP build (Flex 12-slot model only).",
        });
      } else {
        declaredLoads = extractDeclaredProtocolLoads(source);
        const observedDeckState = buildObservedDeckState({
          deckConfiguration: deckConfigurationPayload ?? robotStatusSnapshot.deck_configuration,
          modules: modulesPayload,
          run: runRecord,
        });
        deckDiff = compareDeclaredLoadsToObservedDeck({
          declaredLoads,
          observedDeckState,
          strictEmptyLabwareSlots,
        });
        for (const w of deckDiff.warnings || []) {
          warnings.push(w);
        }
        for (const e of deckDiff.errors || []) {
          errors.push(e);
        }
      }
    }
  }

  const ok = errors.length === 0;
  return {
    ok,
    allowed_to_play: ok,
    robot_type: robotType,
    declared_loads: declaredLoads,
    deck_diff: deckDiff,
    home_safety: {
      auto_home_allowed: homeSafety.auto_home_allowed,
      blockers: homeSafety.blockers || [],
      minimum_cleanup_actions: homeSafety.minimum_cleanup_actions || [],
    },
    errors,
    warnings,
    summary: ok
      ? "Preflight passed; review warnings before play if any."
      : `Preflight blocked: ${errors.map(e => e.code || e.message).join("; ")}`,
  };
}
