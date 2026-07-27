import fs from "fs";
import path from "path";

import { buildHomeSafetyResult, buildObservedDeckState } from "./decision.js";
import { buildErrorTaxonomy, mapRobotBlockerToLeaf } from "./error-taxonomy.js";
import {
  compareDeclaredLoadsToObservedDeck,
  extractDeclaredProtocolLoads,
  extractRobotTypeFromProtocolSource,
} from "./protocol-deck.js";

function isOt2RobotType(robotType) {
  const t = String(robotType || "").toLowerCase();
  return t.includes("ot-2") || t.includes("ot2");
}

function inferDeckModel(robotType) {
  return isOt2RobotType(robotType) ? "ot2_numeric" : "flex_12_slot";
}

function mapPreflightCodeToLeaf(code, item = {}) {
  switch (code) {
    case "needs_reconciliation":
      return "SESSION_NEEDS_RECONCILIATION";
    case "module_blockers_present":
      return "MODULE_NOT_READY";
    case "slot_not_addressable":
    case "slot_not_in_flex_model":
      return "SLOT_NOT_ADDRESSABLE";
    case "labware_load_name_mismatch":
    case "module_slot_labware_conflict":
    case "trash_slot_conflict":
    case "labware_slot_wrong_occupant":
    case "expected_labware_slot_empty":
    case "expected_labware_not_visible_pre_play":
    case "labware_placement_unknown":
    case "trash_slot_unconfirmed":
    case "module_slot_unconfirmed":
      return "LABWARE_MISMATCH";
    case "protocol_file_unreadable":
      return "UNKNOWN_NEEDS_HUMAN";
    case "deck_diff_skipped_ot2":
      return "UNKNOWN_NEEDS_HUMAN";
    case "home_not_auto_safe":
      if ((item.blockers || []).includes("needs_reconciliation")) {
        return "SESSION_NEEDS_RECONCILIATION";
      }
      if ((item.blockers || []).includes("door_open")) {
        return "DOOR_OPEN";
      }
      if ((item.blockers || []).includes("estop_engaged")) {
        return "ESTOP_ENGAGED";
      }
      return "UNKNOWN_NEEDS_HUMAN";
    default:
      return "UNKNOWN_NEEDS_HUMAN";
  }
}

function buildPreflightCheck(status, item = {}, { errorLeaf = null, evidenceSources = null } = {}) {
  const resolvedLeaf = errorLeaf || mapPreflightCodeToLeaf(item.code, item);
  return {
    status,
    code: item.code || null,
    message: item.message || null,
    blockers: item.blockers || [],
    ...buildErrorTaxonomy({
      phase: "preflight",
      errorLeaf: resolvedLeaf,
      overrides: {
        auto_executable: false,
        evidence_sources:
          evidenceSources || ["protocol_source", "session_state", "robot_status", "module_status"],
      },
    }),
  };
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
  const warningChecks = [];
  const blockingChecks = [];
  const robotModel = robotStatusSnapshot?.health_summary?.robot_model || null;

  if (sessionState.needs_reconciliation === true) {
    const item = {
      code: "needs_reconciliation",
      message: "Session needs_reconciliation is true; run reconcile_state before playing a protocol.",
    };
    errors.push(item);
    blockingChecks.push(buildPreflightCheck("fail", item, { evidenceSources: ["session_state"] }));
  }

  if (robotStatusSnapshot.ready_for_physical_action === false) {
    const item = {
      code: "robot_not_ready",
      blockers: robotStatusSnapshot.blockers || [],
      message: "Robot reports blockers; clear door/estop/instrument issues before play.",
    };
    errors.push(item);
    for (const blocker of robotStatusSnapshot.blockers || []) {
      blockingChecks.push(
        buildPreflightCheck(
          "fail",
          { ...item, code: `robot_blocker:${blocker}`, message: item.message },
          {
            errorLeaf: mapRobotBlockerToLeaf(blocker),
            evidenceSources: ["robot_status"],
          },
        ),
      );
    }
  }

  const moduleBlockers = moduleStatusSnapshot.blockers || [];
  if (Array.isArray(moduleBlockers) && moduleBlockers.length > 0) {
    const item = {
      code: "module_blockers_present",
      blockers: moduleBlockers,
      message: "One or more modules are not ready; verify this is acceptable for the protocol.",
    };
    warnings.push(item);
    warningChecks.push(buildPreflightCheck("warn", item, { evidenceSources: ["module_status"] }));
  }

  const homeSafety = buildHomeSafetyResult({
    robotStatusSnapshot,
    sessionState,
  });
  if (homeSafety.auto_home_allowed === false) {
    const item = {
      code: "home_not_auto_safe",
      blockers: homeSafety.blockers || [],
      minimum_cleanup_actions: homeSafety.minimum_cleanup_actions || [],
      message: "Live state suggests homing/cleanup may be unsafe; protocol play may still proceed, but review cleanup and is_home_safe before homing.",
    };
    warnings.push(item);
    warningChecks.push(buildPreflightCheck("warn", item, { evidenceSources: ["robot_status", "session_state"] }));
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
      const item = {
        code: "protocol_file_unreadable",
        path: resolved,
        message: `Could not read protocol file for deck preflight: ${resolved}`,
      };
      errors.push(item);
      blockingChecks.push(buildPreflightCheck("fail", item, { evidenceSources: ["filesystem"] }));
    }

    if (source) {
      robotType = extractRobotTypeFromProtocolSource(source);
      if (isOt2RobotType(robotType)) {
        const item = {
          code: "deck_diff_skipped_ot2",
          robot_type: robotType,
          message: "Deck load diff is skipped for OT-2 protocols in this MCP build (Flex 12-slot model only).",
        };
        warnings.push(item);
        warningChecks.push(buildPreflightCheck("warn", item, { evidenceSources: ["protocol_source"] }));
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
          warningChecks.push(buildPreflightCheck("warn", w));
        }
        for (const e of deckDiff.errors || []) {
          errors.push(e);
          blockingChecks.push(buildPreflightCheck("fail", e));
        }
      }
    }
  }

  const ok = errors.length === 0;
  return {
    ok,
    allowed_to_play: ok,
    robot_type: robotType,
    robot_model: robotModel,
    deck_model: inferDeckModel(robotType),
    declared_loads: declaredLoads,
    deck_diff: deckDiff,
    home_safety: {
      auto_home_allowed: homeSafety.auto_home_allowed,
      blockers: homeSafety.blockers || [],
      minimum_cleanup_actions: homeSafety.minimum_cleanup_actions || [],
    },
    blocking_checks: blockingChecks,
    warning_checks: warningChecks,
    errors,
    warnings,
    summary: ok
      ? "Preflight passed; review warnings before play if any."
      : `Preflight blocked: ${errors.map(e => e.code || e.message).join("; ")}`,
  };
}
