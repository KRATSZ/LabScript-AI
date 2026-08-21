import {
  COLUMN_MAJOR_WELL_ORDER_96,
  FLEX_SLOT_NAMES,
  computeStartingTip,
  ensureTiprackState,
  markTipWellStatus,
  normalizeLiquidTracking,
  setDeckSlotState,
  setLiquidContainerState,
} from "./state.js";
import { buildErrorTaxonomy, mapRobotBlockerToLeaf } from "./error-taxonomy.js";
import { assessTipRecoveryBudget, decideTipRecoveryRoute } from "./protocol-tips.js";
import {
  buildLiquidSourceSubstitutionPlan,
  evaluateReuseAttachedTipEligibility,
  findSameLiquidSourceCandidates,
  isSubstituteVolumeUnverified,
} from "./liquid-source-substitution.js";
import { readPendingInRunLiquidSubstitutionConfirm } from "./liquid-source-fixit-recovery.js";

export const HARD_STOP_ERROR_CATEGORIES = ["HARDWARE_FAULT", "DECK_COLLISION", "UNKNOWN"];

export function isHardStopErrorCategory(errorCategory) {
  return HARD_STOP_ERROR_CATEGORIES.includes(String(errorCategory || "").toUpperCase());
}

function unwrapData(payload) {
  if (payload && typeof payload === "object" && "data" in payload) {
    return payload.data;
  }
  return payload;
}

function asArray(value) {
  if (Array.isArray(value)) {
    return value;
  }
  if (value && typeof value === "object") {
    return Object.values(value);
  }
  return [];
}

function readNested(value, candidates, fallback = null) {
  for (const candidate of candidates) {
    let current = value;
    let found = true;
    for (const part of candidate) {
      if (current && typeof current === "object" && part in current) {
        current = current[part];
      } else {
        found = false;
        break;
      }
    }
    if (found && current !== undefined) {
      return current;
    }
  }
  return fallback;
}

function uniqueBy(values, keyBuilder) {
  const seen = new Set();
  return values.filter(value => {
    const key = keyBuilder(value);
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function extractSlotNameFromCutoutId(cutoutId) {
  const match = String(cutoutId || "").match(/cutout([A-D][1-3])/i);
  return match ? match[1].toUpperCase() : null;
}

function normalizeRunRecord(runPayload) {
  return unwrapData(runPayload) || null;
}

function extractRunLabware(runPayload) {
  const run = normalizeRunRecord(runPayload) || {};
  return asArray(readNested(run, [["labware"]], []));
}

function extractRunModules(runPayload) {
  const run = normalizeRunRecord(runPayload) || {};
  return asArray(readNested(run, [["modules"]], []));
}

function extractTipracksFromRun(runPayload) {
  return extractRunLabware(runPayload)
    .filter(labware => String(readNested(labware, [["loadName"]], "")).toLowerCase().includes("tiprack"))
    .map(labware => ({
      slot_name: readNested(labware, [["location", "slotName"]]),
      load_name: readNested(labware, [["loadName"]]),
      labware_id: readNested(labware, [["id"]]),
    }))
    .filter(tiprack => tiprack.slot_name);
}

function extractFailedCommand(commandsPayload) {
  const commands = asArray(unwrapData(commandsPayload));
  return commands.findLast
    ? commands.findLast(command => readNested(command, [["status"]]) === "failed")
    : [...commands].reverse().find(command => readNested(command, [["status"]]) === "failed");
}

function upsertObservedSlot(slots, slotName, patch) {
  if (!slotName) {
    return;
  }

  const current = slots[slotName] || {
    slot_name: slotName,
    observed_status: "unknown",
    addressable: true,
    occupant_type: null,
    occupant_name: null,
    occupant_id: null,
    observed_sources: [],
    notes: [],
  };

  slots[slotName] = {
    ...current,
    ...patch,
    observed_sources: uniqueBy(
      [...(current.observed_sources || []), ...(patch?.observed_sources || [])],
      value => value,
    ),
    notes: uniqueBy([...(current.notes || []), ...(patch?.notes || [])], value => value),
  };
}

export function buildObservedDeckState({ deckConfiguration, modules, run } = {}) {
  const deck = unwrapData(deckConfiguration) || deckConfiguration || {};
  const fixtures = (() => {
    const candidates = [
      readNested(deck, [["cutoutFixtures"]], undefined),
      readNested(deck, [["cutout_fixtures"]], undefined),
      readNested(deck, [["raw", "cutoutFixtures"]], undefined),
      readNested(deck, [["raw", "cutout_fixtures"]], undefined),
    ];
    for (const candidate of candidates) {
      if (candidate !== undefined && candidate !== null) {
        return asArray(candidate);
      }
    }
    return [];
  })();

  const slots = Object.fromEntries(
    FLEX_SLOT_NAMES.map(slotName => [
      slotName,
      {
        slot_name: slotName,
        observed_status: "unknown",
        addressable: true,
        occupant_type: null,
        occupant_name: null,
        occupant_id: null,
        observed_sources: [],
        notes: [],
      },
    ]),
  );

  for (const fixture of fixtures) {
    const slotName = extractSlotNameFromCutoutId(readNested(fixture, [["cutoutId"]]));
    if (!slotName) {
      continue;
    }

    const fixtureId = String(readNested(fixture, [["cutoutFixtureId"]], ""));
    const lowerFixtureId = fixtureId.toLowerCase();
    const basePatch = {
      addressable: true,
      observed_sources: ["deck_configuration"],
    };

    if (lowerFixtureId.includes("trashbinadapter")) {
      upsertObservedSlot(slots, slotName, {
        ...basePatch,
        observed_status: "occupied",
        occupant_type: "trash_bin",
        occupant_name: fixtureId,
        occupant_id: readNested(fixture, [["opentronsModuleSerialNumber"]], "trash-bin"),
      });
      continue;
    }

    if (lowerFixtureId.includes("module")) {
      upsertObservedSlot(slots, slotName, {
        ...basePatch,
        observed_status: "occupied",
        occupant_type: "module",
        occupant_name: fixtureId,
        occupant_id: readNested(fixture, [["opentronsModuleSerialNumber"]]),
      });
      continue;
    }

    upsertObservedSlot(slots, slotName, {
      ...basePatch,
      observed_status: "unknown",
      occupant_type: null,
      occupant_name: null,
      occupant_id: null,
    });
  }

  for (const moduleRecord of asArray(unwrapData(modules))) {
    const slotName = readNested(moduleRecord, [["location", "slotName"], ["moduleOffset", "slot"]]);
    if (!slotName) {
      continue;
    }

    upsertObservedSlot(slots, slotName, {
      addressable: true,
      observed_status: "occupied",
      occupant_type: "module",
      occupant_name: readNested(moduleRecord, [["moduleModel"], ["moduleType"], ["model"]]),
      occupant_id: readNested(moduleRecord, [["serialNumber"], ["id"]]),
      observed_sources: ["modules"],
    });
  }

  for (const moduleRecord of extractRunModules(run)) {
    const slotName = readNested(moduleRecord, [["location", "slotName"]]);
    if (!slotName) {
      continue;
    }

    upsertObservedSlot(slots, slotName, {
      addressable: true,
      observed_status: "occupied",
      occupant_type: "module",
      occupant_name: readNested(moduleRecord, [["model"], ["moduleModel"]]),
      occupant_id: readNested(moduleRecord, [["serialNumber"], ["id"]]),
      observed_sources: ["run"],
    });
  }

  for (const labware of extractRunLabware(run)) {
    const slotName = readNested(labware, [["location", "slotName"]]);
    if (!slotName) {
      continue;
    }

    const existingSlot = slots[slotName];
    const notes = [];
    if (existingSlot?.occupant_type && existingSlot.occupant_type !== "labware") {
      notes.push(`run_labware_conflicts_with_${existingSlot.occupant_type}`);
    }

    upsertObservedSlot(slots, slotName, {
      addressable: true,
      observed_status: "occupied",
      occupant_type: "labware",
      occupant_name: readNested(labware, [["loadName"]]),
      occupant_id: readNested(labware, [["id"]]),
      observed_sources: ["run"],
      notes,
    });
  }

  return {
    slots,
  };
}

export function getSlotOccupationSummary({ slotName, observedDeckState, sessionState } = {}) {
  const normalizedSlot = String(slotName || "").toUpperCase();
  const observedSlot = observedDeckState?.slots?.[normalizedSlot] || null;
  const committedSlot = sessionState?.deck?.slots?.[normalizedSlot] || null;

  const mismatch =
    committedSlot &&
    observedSlot &&
    (committedSlot.occupant_type !== observedSlot.occupant_type ||
      committedSlot.occupant_name !== observedSlot.occupant_name ||
      committedSlot.observed_status !== observedSlot.observed_status);

  return {
    slot_name: normalizedSlot,
    status: mismatch ? "mismatched" : observedSlot?.observed_status || "unknown",
    addressable: observedSlot?.addressable ?? false,
    occupant_type: observedSlot?.occupant_type || null,
    occupant_name: observedSlot?.occupant_name || null,
    occupant_id: observedSlot?.occupant_id || null,
    observed_sources: observedSlot?.observed_sources || [],
    notes: observedSlot?.notes || [],
    committed_state: committedSlot,
    mismatched_against_committed: Boolean(mismatch),
  };
}

function deriveTiprackSlots({ sessionState, run, tiprackSlots } = {}) {
  const explicitSlots = asArray(tiprackSlots).map(slot => String(slot).toUpperCase());
  if (explicitSlots.length > 0) {
    return uniqueBy(explicitSlots.map(slotName => ({ slot_name: slotName, load_name: null })), value => value.slot_name);
  }

  const fromSession = Object.values(sessionState?.tip_tracking?.tipracks || {}).map(tiprack => ({
    slot_name: String(tiprack.slot_name || "").toUpperCase(),
    load_name: tiprack.load_name || null,
  }));
  const fromRun = extractTipracksFromRun(run).map(tiprack => ({
    slot_name: String(tiprack.slot_name || "").toUpperCase(),
    load_name: tiprack.load_name || null,
  }));

  return uniqueBy(
    [...fromSession, ...fromRun].filter(tiprack => tiprack.slot_name),
    value => value.slot_name,
  );
}

export function listTipCandidates({ sessionState, run, tiprackSlots } = {}) {
  const trackedTipracks = deriveTiprackSlots({ sessionState, run, tiprackSlots });
  const viableCandidates = [];
  const blockedCandidates = [];
  const tipracks = [];

  for (const tiprack of trackedTipracks) {
    const state = ensureTiprackState(sessionState, {
      slotName: tiprack.slot_name,
      loadName: tiprack.load_name,
    });
    const missing = new Set(state.missing_wells || []);
    const depleted = new Set(state.depleted_wells || []);
    const unknownBlocked = new Set(state.unknown_blocked_wells || []);

    for (const wellName of state.search_order || COLUMN_MAJOR_WELL_ORDER_96) {
      const candidate = {
        tiprack_slot: tiprack.slot_name,
        well_name: wellName,
      };

      if (missing.has(wellName)) {
        blockedCandidates.push({ ...candidate, status: "missing", reason: "previous_pickup_failed" });
      } else if (depleted.has(wellName)) {
        blockedCandidates.push({ ...candidate, status: "depleted", reason: "already_consumed" });
      } else if (unknownBlocked.has(wellName)) {
        blockedCandidates.push({ ...candidate, status: "unknown-blocked", reason: "manually_blocked" });
      } else {
        viableCandidates.push({ ...candidate, status: "viable" });
      }
    }

    tipracks.push({
      slot_name: tiprack.slot_name,
      load_name: state.load_name || tiprack.load_name,
      viable_count: viableCandidates.filter(candidate => candidate.tiprack_slot === tiprack.slot_name).length,
      missing_wells: state.missing_wells || [],
      depleted_wells: state.depleted_wells || [],
      unknown_blocked_wells: state.unknown_blocked_wells || [],
      last_good_tip: state.last_good_tip || null,
      starting_tip: computeStartingTip(state),
    });
  }

  return {
    tipracks,
    viable_candidates: viableCandidates,
    blocked_candidates: blockedCandidates,
  };
}

export function suggestNextTipWell({
  sessionState,
  run,
  tiprackSlots,
  tiprackSlot,
  failedWell,
  failureStatus = "missing",
} = {}) {
  const normalizedTiprackSlot = tiprackSlot ? String(tiprackSlot).toUpperCase() : null;
  const normalizedFailedWell = failedWell ? String(failedWell).toUpperCase() : null;

  if (normalizedFailedWell) {
    const resolvedTipracks = deriveTiprackSlots({ sessionState, run, tiprackSlots });
    const resolvedSlot =
      normalizedTiprackSlot ||
      (resolvedTipracks.length === 1 ? resolvedTipracks[0].slot_name : null);

    if (resolvedSlot) {
      markTipWellStatus(sessionState, {
        slotName: resolvedSlot,
        wellName: normalizedFailedWell,
        status: failureStatus,
      });
    }
  }

  const summary = listTipCandidates({ sessionState, run, tiprackSlots });
  const nextCandidate = summary.viable_candidates[0] || null;

  if (nextCandidate) {
    const tiprackState = ensureTiprackState(sessionState, {
      slotName: nextCandidate.tiprack_slot,
    });
    tiprackState.last_suggested_well = nextCandidate.well_name;
  }

  return {
    failed_well: normalizedFailedWell,
    next_candidate: nextCandidate,
    skipped_candidates: summary.blocked_candidates,
    tipracks: summary.tipracks,
  };
}

export function buildHomeSafetyResult({ robotStatusSnapshot, sessionState } = {}) {
  const blockers = [...(robotStatusSnapshot?.blockers || [])];
  const minimumCleanupActions = [...(sessionState?.cleanup?.pending_actions || [])];

  for (const instrument of robotStatusSnapshot?.instruments_summary || []) {
    if (instrument.tip_detected === true) {
      blockers.push(`tip_attached:${instrument.mount}`);
      minimumCleanupActions.push(`drop_tip:${instrument.mount}`);
    }
  }

  if (sessionState?.needs_reconciliation) {
    blockers.push("needs_reconciliation");
  }

  return {
    auto_home_allowed: blockers.length === 0 && minimumCleanupActions.length === 0,
    blockers: uniqueBy(blockers, value => value),
    minimum_cleanup_actions: uniqueBy(minimumCleanupActions, value => value),
  };
}

function summarizeAttachedTipCleanup(robotStatusSnapshot) {
  return uniqueBy(
    asArray(robotStatusSnapshot?.instruments_summary)
      .filter(instrument => instrument?.tip_detected === true && instrument?.mount)
      .map(instrument => `drop_tip:${instrument.mount}`),
    value => value,
  );
}

function findRunLabwareById(run, labwareId) {
  if (!labwareId) {
    return null;
  }
  return extractRunLabware(run).find(labware => readNested(labware, [["id"]], null) === labwareId) || null;
}

function sourceMapEntryForFailure({ failedCommand, run, sessionState } = {}) {
  const failedWell = readNested(failedCommand, [["params", "wellName"]], null);
  const sourceLabwareId = readNested(failedCommand, [["params", "labwareId"]], null);
  const runLabware = findRunLabwareById(run, sourceLabwareId);
  const sourceSlot = readNested(runLabware, [["location", "slotName"], ["location", "addressableAreaName"]], null);
  const key = sourceSlot && failedWell ? `${String(sourceSlot).toUpperCase()}.${String(failedWell).toUpperCase()}` : null;
  return {
    key,
    source_slot: sourceSlot ? String(sourceSlot).toUpperCase() : null,
    run_labware: runLabware,
    liquid_source: key ? sessionState?.liquid_tracking?.sources?.[key] || null : null,
  };
}

function normalizeObservedLiquidTracking(observedLiquidTracking) {
  if (!observedLiquidTracking) {
    return null;
  }
  if (Array.isArray(observedLiquidTracking)) {
    const containers = {};
    for (const container of observedLiquidTracking) {
      const key = container?.container_key || container?.containerKey || container?.key ||
        (container?.slot_name || container?.slotName
          ? `${String(container.slot_name || container.slotName).toUpperCase()}.${String(container.well_name || container.wellName || "").toUpperCase()}`
          : null);
      if (key) {
        containers[key] = container;
      }
    }
    return normalizeLiquidTracking({ containers });
  }
  return normalizeLiquidTracking(observedLiquidTracking);
}

function compareLiquidTracking({ sessionState, observedLiquidTracking, proposedCommit, diffs }) {
  const observed = normalizeObservedLiquidTracking(observedLiquidTracking);
  if (!observed) {
    return;
  }

  proposedCommit.liquid_tracking = {
    containers: {},
    sources: {},
  };

  const committed = normalizeLiquidTracking(sessionState?.liquid_tracking || {});
  for (const [key, observedContainer] of Object.entries(observed.containers || {})) {
    const committedContainer = committed.containers?.[key] || null;
    proposedCommit.liquid_tracking.containers[key] = {
      ...observedContainer,
      trust_level: observedContainer.trust_level || "reconciled",
    };

    if (!committedContainer) {
      diffs.push({
        type: "liquid_container_missing",
        container_key: key,
        observed: observedContainer,
      });
      continue;
    }

    if (
      observedContainer.volume_ul !== null &&
      committedContainer.volume_ul !== null &&
      Math.abs(Number(committedContainer.volume_ul) - Number(observedContainer.volume_ul)) > 0.1
    ) {
      diffs.push({
        type: "liquid_volume_mismatch",
        container_key: key,
        committed: committedContainer.volume_ul,
        observed: observedContainer.volume_ul,
      });
    }

    if (
      observedContainer.trust_level &&
      committedContainer.trust_level &&
      committedContainer.trust_level !== observedContainer.trust_level
    ) {
      diffs.push({
        type: "liquid_trust_mismatch",
        container_key: key,
        committed: committedContainer.trust_level,
        observed: observedContainer.trust_level,
      });
    }
  }

  proposedCommit.liquid_tracking = normalizeLiquidTracking(proposedCommit.liquid_tracking);
}

function summarizeAttachedTipsForReuse(robotStatusSnapshot) {
  return asArray(robotStatusSnapshot?.instruments_summary)
    .filter(
      instrument =>
        instrument?.tip_detected === true && instrument?.mount && instrument.mount !== "extension",
    )
    .map(instrument => ({
      mount: instrument.mount,
      instrument_name: instrument.instrument_name || null,
    }));
}

function normalizeCommandsForReuseEligibility(commandsPayload) {
  return asArray(unwrapData(commandsPayload)).map(command => ({
    ...command,
    command_type:
      command?.command_type || command?.commandType || readNested(command, [["commandType"]], null),
  }));
}

function buildLiquidManualRecoveryContext({
  failedCommand,
  robotStatusSnapshot,
  run,
  sessionState,
  commands = [],
  protocolSource = "",
} = {}) {
  const failedWell = readNested(failedCommand, [["params", "wellName"]], null);
  const sourceLabwareId = readNested(failedCommand, [["params", "labwareId"]], null);
  const commandId = readNested(failedCommand, [["id"]], null);
  const commandType = readNested(failedCommand, [["commandType"], ["command_type"]], null);
  const sourceMap = sourceMapEntryForFailure({ failedCommand, run, sessionState });
  const sourceIdentity = sourceMap.liquid_source
    ? [
        sourceMap.liquid_source.liquid_name,
        sourceMap.liquid_source.sample_id ? `sample ${sourceMap.liquid_source.sample_id}` : null,
      ].filter(Boolean).join(" / ")
    : null;
  const expectedPresence = sourceMap.liquid_source?.expected_presence;
  const hasRecordedPresenceExpectation = typeof expectedPresence === "boolean";
  const expectedAbsent = expectedPresence === false;
  const expectedPresent = expectedPresence === true;
  const sourceMapExpectationMismatch = hasRecordedPresenceExpectation;
  const sameLiquidSourceCandidates = findSameLiquidSourceCandidates({
    sources: sessionState?.liquid_tracking?.sources || {},
    failedKey: sourceMap.key,
    failedSource: sourceMap.liquid_source,
  });
  const preferredCandidate = sameLiquidSourceCandidates[0] || null;
  const substitutionPlan = sameLiquidSourceCandidates.length > 0
    ? buildLiquidSourceSubstitutionPlan({
        sessionState,
        failedSourceKey: sourceMap.key,
        preferredSourceKey: preferredCandidate?.source_map_key || null,
        protocolSource: protocolSource || "",
      })
    : null;
  const volumeCheck = substitutionPlan?.volume_check || null;
  // Conclusive shortfall only. Missing volume data stays on the human / live-LPD
  // path (recover probes reserve height) so 03 FIX still suggests substitution.
  const volumeInsufficient =
    volumeCheck?.sufficient === false &&
    (volumeCheck?.basis === "declared_source_map" ||
      volumeCheck?.basis === "approximate_lpd_height" ||
      substitutionPlan?.blocked_reason === "substitute_volume_insufficient");
  const hasSameLiquidSourceCandidates =
    sameLiquidSourceCandidates.length > 0 &&
    !volumeInsufficient &&
    substitutionPlan?.blocked_reason !== "substitute_volume_insufficient";
  const attachedTips = summarizeAttachedTipsForReuse(robotStatusSnapshot);
  const reuseAttachedTipContext = evaluateReuseAttachedTipEligibility({
    failedCommand,
    recentCommands: normalizeCommandsForReuseEligibility(commands),
    substitutionPlan: hasSameLiquidSourceCandidates ? substitutionPlan : null,
    attachedTips,
  });
  const cleanupRequired = reuseAttachedTipContext.eligible
    ? []
    : summarizeAttachedTipCleanup(robotStatusSnapshot);
  const blockedAutoRecoveryReason = volumeInsufficient
    ? "substitute_volume_insufficient"
    : hasSameLiquidSourceCandidates
    ? "same_liquid_source_substitution_requires_prepared_recovery_bundle_and_live_gate"
    : "liquid_source_change_requires_human_confirmation";
  const operatorSteps = [
    expectedAbsent
      ? `Source map says ${sourceMap.key || "the failed source well"} is expected to be empty; inspect the protocol source or update the source map before retry.`
      : expectedPresent
      ? `Source map says ${sourceMap.key || "the failed source well"} should contain liquid, but the runtime liquid probe did not find liquid; verify fill height, well identity, and source-map freshness before retry.`
      : failedWell
      ? `Verify or refill the intended source well ${failedWell}.`
      : "Verify or refill the intended source well.",
    sourceIdentity
      ? `Preserve source identity: ${sourceIdentity}.`
      : null,
    sourceLabwareId
      ? `Confirm the source labware ${sourceLabwareId} is still the intended liquid source.`
      : "Confirm the source labware is still the intended liquid source.",
    volumeInsufficient
      ? `Substitute source ${volumeCheck.candidate_key} has insufficient usable volume (${volumeCheck.usable_ul} uL usable vs ${volumeCheck.required_ul} uL required). Refill source or escalate.`
      : hasSameLiquidSourceCandidates
      ? `Same-liquid alternatives are recorded: ${sameLiquidSourceCandidates.map(source => source.source_map_key).join(", ")}.`
      : "Do not change source wells unless the operator provides a confirmed source map.",
    reuseAttachedTipContext.eligible
      ? `Keep the attached tip and call recover_liquid_source_substitution to fixit-probe ${preferredCandidate?.source_map_key || "the reserve source"} and complete transfers on the same run (do not stop the run first or start a new run_protocol with pick_up_tip).`
      : cleanupRequired.length > 0
        ? `Clear attached tips before homing or continuing: ${cleanupRequired.join(", ")}.`
        : null,
    "After physical correction, rerun through simulation or in-run fixit recovery on the same run_id.",
  ].filter(Boolean);

  return {
    failed_well: failedWell,
    source_labware_id: sourceLabwareId,
    source_slot: sourceMap.source_slot,
    source_map_key: sourceMap.key,
    liquid_source: sourceMap.liquid_source,
    source_map_expected_presence: expectedPresence ?? null,
    observed_liquid_presence: false,
    source_map_expectation_mismatch: sourceMapExpectationMismatch,
    same_liquid_source_candidates: sameLiquidSourceCandidates,
    same_liquid_source_candidate_count: sameLiquidSourceCandidates.length,
    same_liquid_source_substitution_allowed: hasSameLiquidSourceCandidates,
    same_liquid_source_substitution_next_tool: reuseAttachedTipContext.eligible
      ? "recover_liquid_source_substitution"
      : null,
    same_liquid_source_substitution_playbook: hasSameLiquidSourceCandidates && reuseAttachedTipContext.eligible
      ? "substitute_liquid_source_with_attached_tip"
      : null,
    same_liquid_source_substitution_required_gates: [],
    same_liquid_auto_resume_eligible: false,
    same_liquid_auto_resume_blocker: hasSameLiquidSourceCandidates && !reuseAttachedTipContext.eligible
      ? "attached_tip_reuse_required_for_same_liquid_substitution"
      : null,
    volume_check: volumeCheck,
    blocked_reason: volumeInsufficient ? "substitute_volume_insufficient" : null,
    required_next_step: volumeInsufficient ? "refill_source_or_escalate" : null,
    substitution_plan: substitutionPlan,
    failed_command_id: commandId,
    failed_command_type: commandType,
    blocked_auto_recovery_reason: blockedAutoRecoveryReason,
    cleanup_required: cleanupRequired,
    reuse_attached_tip_eligible: reuseAttachedTipContext.eligible,
    recommended_validation_run_time_parameters:
      reuseAttachedTipContext.recommended_validation_run_time_parameters,
    reuse_attached_tip_context: reuseAttachedTipContext,
    blockers: asArray(robotStatusSnapshot?.blockers),
    operator_steps: operatorSteps,
  };
}

function extractRuntimeErrorStrings({ run, commands } = {}) {
  const values = [];
  const normalizedRun = normalizeRunRecord(run) || {};

  for (const error of asArray(readNested(normalizedRun, [["errors"], ["commandErrors"]], []))) {
    const detail = readNested(error, [["detail"], ["error", "detail"]]);
    const errorType = readNested(error, [["errorType"], ["error", "errorType"]]);
    if (errorType) {
      values.push(errorType);
    }
    if (detail) {
      values.push(detail);
    }
  }

  const failedCommand = extractFailedCommand(commands);
  const commandErrorType = readNested(failedCommand, [["error", "errorType"]]);
  if (commandErrorType) {
    values.push(commandErrorType);
  }
  const commandDetail = readNested(failedCommand, [["error", "detail"]]);
  if (commandDetail) {
    values.push(commandDetail);
  }

  const notes = asArray(readNested(failedCommand, [["notes"]], []))
    .map(note => readNested(note, [["shortMessage"], ["longMessage"]]))
    .filter(Boolean);

  return {
    failed_command: failedCommand || null,
    joined_error_text: values.join("\n"),
    notes,
  };
}

function isAwaitingRecoveryRun(run) {
  const normalizedRun = normalizeRunRecord(run) || {};
  const runStatus = readNested(normalizedRun, [["status"]], null);
  return (
    String(runStatus || "").toLowerCase() === "awaiting-recovery" ||
    Boolean(readNested(normalizedRun, [["currentlyRecoveringFrom"]], null))
  );
}

function buildParsedErrorCapability({ errorLeaf, run } = {}) {
  const awaitingRecovery = isAwaitingRecoveryRun(run);

  switch (errorLeaf) {
    case "TIP_PHYSICALLY_MISSING":
      return {
        actionability: awaitingRecovery ? "auto_executable" : "manual_only",
        auto_executable: awaitingRecovery,
        required_inputs: awaitingRecovery ? ["tiprack_slots"] : [],
        requires_confirmation: false,
        supported_in_runtime: awaitingRecovery,
      };

    case "MODULE_NOT_READY":
      return {
        actionability: awaitingRecovery ? "auto_executable" : "manual_only",
        auto_executable: awaitingRecovery,
        required_inputs: [],
        requires_confirmation: false,
        supported_in_runtime: awaitingRecovery,
      };

    case "DESTINATION_OCCUPIED":
      return {
        actionability: awaitingRecovery ? "manual_confirmation_required" : "manual_only",
        auto_executable: awaitingRecovery,
        required_inputs: awaitingRecovery ? ["destination_slot"] : [],
        requires_confirmation: awaitingRecovery,
        supported_in_runtime: awaitingRecovery,
      };

    case "MISSING_TRASH_OR_SETUP":
    case "SYNTAX_OR_IMPORT":
    case "API_MISUSE":
    case "LABWARE_OR_MODULE_COMPAT":
    case "VOLUME_OR_RANGE_VIOLATION":
    case "OUT_OF_TIPS":
      return {
        actionability: "protocol_edit_required",
        auto_executable: false,
        required_inputs: [],
        requires_confirmation: false,
        supported_in_runtime: false,
      };

    default:
      return {
        actionability: "manual_only",
        auto_executable: false,
        required_inputs: [],
        requires_confirmation: false,
        supported_in_runtime: false,
      };
  }
}

export function classifyRecoveryError({ run, commands, moduleStatusSnapshot, robotStatusSnapshot } = {}) {
  const { failed_command, joined_error_text } = extractRuntimeErrorStrings({ run, commands });
  const lowerError = joined_error_text.toLowerCase();

  if ((moduleStatusSnapshot?.blockers || []).length > 0) {
    return {
      error_category: "MODULE_NOT_READY",
      error_leaf: "MODULE_NOT_READY",
      reason: "module_status_has_blockers",
      failed_command,
    };
  }

  if ((robotStatusSnapshot?.blockers || []).includes("estop_engaged")) {
    return {
      error_category: "HARDWARE_FAULT",
      error_leaf: "ESTOP_ENGAGED",
      reason: "estop_engaged",
      failed_command,
    };
  }

  if ((robotStatusSnapshot?.blockers || []).includes("door_open")) {
    return {
      error_category: "HARDWARE_FAULT",
      error_leaf: "DOOR_OPEN",
      reason: "door_open",
      failed_command,
    };
  }

  if ((robotStatusSnapshot?.blockers || []).includes("instrument_not_ready")) {
    return {
      error_category: "HARDWARE_FAULT",
      error_leaf: "INSTRUMENT_NOT_READY",
      reason: "instrument_not_ready",
      failed_command,
    };
  }

  if (lowerError.includes("notrashdefinederror")) {
    return {
      error_category: "PROTOCOL_SETUP_ERROR",
      error_leaf: "MISSING_TRASH_OR_SETUP",
      reason: "runtime_error_match",
      failed_command,
    };
  }

  if (
    lowerError.includes("areanotindeckconfigurationerror") ||
    lowerError.includes("not provided by deck configuration")
  ) {
    return {
      error_category: "DESTINATION_UNAVAILABLE",
      error_leaf: "DESTINATION_UNAVAILABLE",
      reason: "runtime_error_match",
      failed_command,
    };
  }

  if (lowerError.includes("locationisoccupiederror")) {
    return {
      error_category: "DESTINATION_OCCUPIED",
      error_leaf: "DESTINATION_OCCUPIED",
      reason: "runtime_error_match",
      failed_command,
    };
  }

  if (
    lowerError.includes("insufficient_volume") ||
    lowerError.includes("liquidnotfound") ||
    lowerError.includes("liquid not found") ||
    lowerError.includes("pipetteliquidnotfounderror") ||
    lowerError.includes("liquid not found during probe") ||
    lowerError.includes("out of liquid") ||
    lowerError.includes("not enough liquid") ||
    lowerError.includes("invalidaspiratevolumeerror")
  ) {
    return {
      error_category: "INSUFFICIENT_VOLUME",
      error_leaf: "INSUFFICIENT_VOLUME",
      reason: "runtime_error_match",
      failed_command,
    };
  }

  if (lowerError.includes("air bubble") || lowerError.includes("bubble")) {
    return {
      error_category: "AIR_BUBBLE",
      error_leaf: "AIR_BUBBLE",
      reason: "runtime_error_match",
      failed_command,
    };
  }

  if (
    lowerError.includes("clog") ||
    lowerError.includes("overpressure") ||
    lowerError.includes("over pressure") ||
    lowerError.includes("pressureoutsidelimits") ||
    lowerError.includes("pipetteoverpressure")
  ) {
    return {
      error_category: "TIP_CLOG",
      error_leaf: "TIP_CLOG",
      reason: "runtime_error_match",
      failed_command,
    };
  }

  if (lowerError.includes("collision") || lowerError.includes("stallorcollision")) {
    return {
      error_category: "DECK_COLLISION",
      error_leaf: "DECK_COLLISION",
      reason: "runtime_error_match",
      failed_command,
    };
  }

  if (
    lowerError.includes("viscous") ||
    lowerError.includes("foaming") ||
    lowerError.includes("liquid class")
  ) {
    return {
      error_category: "LIQUID_PROPERTY_ERROR",
      error_leaf: "LIQUID_PROPERTY_ERROR",
      reason: "runtime_error_match",
      failed_command,
    };
  }

  if (lowerError.includes("tipphysicallymissing") || lowerError.includes("no tip detected")) {
    return {
      error_category: "TIP_PHYSICALLY_MISSING",
      error_leaf: "TIP_PHYSICALLY_MISSING",
      reason: "runtime_error_match",
      failed_command,
    };
  }

  return {
    error_category: "UNKNOWN",
    error_leaf: "UNKNOWN_NEEDS_HUMAN",
    reason: "no_known_pattern",
    failed_command,
  };
}

export function parseRuntimeError({ run, commands, moduleStatusSnapshot, robotStatusSnapshot } = {}) {
  const classification = classifyRecoveryError({
    run,
    commands,
    moduleStatusSnapshot,
    robotStatusSnapshot,
  });
  const { failed_command, joined_error_text, notes } = extractRuntimeErrorStrings({ run, commands });
  const primaryMessage = joined_error_text
    .split("\n")
    .map(line => line.trim())
    .find(Boolean);
  const targetSlot =
    readNested(failed_command, [["params", "newLocation", "slotName"]], null) ||
    readNested(failed_command, [["params", "location", "slotName"]], null);
  const sourceLabwareId = readNested(failed_command, [["params", "labwareId"]], null);
  const failedWell = readNested(failed_command, [["params", "wellName"]], null);
  const errorDetail = readNested(failed_command, [["error", "detail"]], null);
  const capability = buildParsedErrorCapability({
    errorLeaf: classification.error_leaf,
    run,
  });
  const taxonomy = buildErrorTaxonomy({
    phase: "runtime",
    errorLeaf: classification.error_leaf,
    overrides: {
      actionability: capability.actionability,
      auto_executable: capability.auto_executable,
      required_inputs: capability.required_inputs,
      requires_confirmation: capability.requires_confirmation,
      evidence_sources: ["run_history", "commands", "robot_status", "module_status"],
    },
  });

  return {
    error_category: classification.error_category,
    ...taxonomy,
    reason: classification.reason,
    summary_message: primaryMessage || errorDetail || "No runtime error detail available.",
    severity: taxonomy.severity,
    failed_command: failed_command
      ? {
          id: readNested(failed_command, [["id"]], null),
          command_type: readNested(failed_command, [["commandType"]], null),
          status: readNested(failed_command, [["status"]], null),
        }
      : null,
    failed_well: failedWell,
    source_labware_id: sourceLabwareId,
    target_slot: targetSlot,
    notes,
    raw_error_text: joined_error_text,
    likely_fixable_by_runtime_action: capability.supported_in_runtime,
    hard_stop: isHardStopErrorCategory(classification.error_category),
    escalate_to_human: [
      "HARDWARE_FAULT",
      "DECK_COLLISION",
      "DESTINATION_OCCUPIED",
      "UNKNOWN",
    ].includes(classification.error_category),
  };
}

export function buildReconciliationResult({
  sessionState,
  robotStatusSnapshot,
  moduleStatusSnapshot,
  observedDeckState,
  observedLiquidTracking = null,
  run,
} = {}) {
  const diffs = [];
  const proposedCommit = {
    robot_serial: robotStatusSnapshot?.health_summary?.robot_serial || sessionState?.robot_serial || null,
    last_run_id: readNested(normalizeRunRecord(run) || {}, [["id"]], null),
    needs_reconciliation: false,
    deck: {
      slots: {},
    },
    pipettes: {},
    liquid_tracking: {
      containers: {},
      sources: {},
    },
    cleanup: {
      pending_actions: uniqueBy([...(sessionState?.cleanup?.pending_actions || [])], value => value),
      auto_home_allowed: null,
    },
  };

  for (const slotName of FLEX_SLOT_NAMES) {
    const observedSlot = observedDeckState?.slots?.[slotName] || {
      slot_name: slotName,
      observed_status: "unknown",
      addressable: false,
      occupant_type: null,
      occupant_name: null,
      occupant_id: null,
      observed_sources: [],
      notes: [],
    };
    const committedSlot = sessionState?.deck?.slots?.[slotName] || null;

    proposedCommit.deck.slots[slotName] = {
      slot_name: slotName,
      observed_status: observedSlot.observed_status,
      addressable: observedSlot.addressable,
      occupant_type: observedSlot.occupant_type,
      occupant_name: observedSlot.occupant_name,
      occupant_id: observedSlot.occupant_id,
      observed_sources: observedSlot.observed_sources,
      notes: observedSlot.notes,
    };

    if (
      committedSlot &&
      (committedSlot.occupant_type !== observedSlot.occupant_type ||
        committedSlot.occupant_name !== observedSlot.occupant_name ||
        committedSlot.observed_status !== observedSlot.observed_status)
    ) {
      diffs.push({
        type: "slot_mismatch",
        slot_name: slotName,
        committed: committedSlot,
        observed: observedSlot,
      });
    }
  }

  for (const instrument of robotStatusSnapshot?.instruments_summary || []) {
    if (!instrument.mount || instrument.mount === "extension") {
      continue;
    }
    const observedTipAttached = instrument.tip_detected === true;
    const committedPipette = sessionState?.pipettes?.[instrument.mount] || null;
    proposedCommit.pipettes[instrument.mount] = {
      tip_attached: observedTipAttached,
      instrument_name: instrument.instrument_name,
    };

    if (
      committedPipette &&
      typeof committedPipette.tip_attached === "boolean" &&
      committedPipette.tip_attached !== observedTipAttached
    ) {
      diffs.push({
        type: "tip_attachment_mismatch",
        mount: instrument.mount,
        committed: committedPipette.tip_attached,
        observed: observedTipAttached,
      });
    }
  }

  if ((moduleStatusSnapshot?.blockers || []).length > 0) {
    diffs.push({
      type: "module_blockers",
      blockers: moduleStatusSnapshot.blockers,
    });
  }

  compareLiquidTracking({
    sessionState,
    observedLiquidTracking,
    proposedCommit,
    diffs,
  });

  const confidence =
    diffs.length === 0
      ? "high"
      : diffs.some(diff => diff.type === "slot_mismatch")
        ? "medium"
        : "high";

  const safeActions = ["robot_status", "module_status", "run_history"];
  if (diffs.length === 0) {
    safeActions.push("normal_execution");
  }

  proposedCommit.needs_reconciliation = diffs.length > 0;

  return {
    diffs,
    confidence,
    safe_actions: uniqueBy(safeActions, value => value),
    proposed_commit: proposedCommit,
    escalate_to_human:
      confidence === "low" ||
      diffs.some(diff => diff.type === "slot_mismatch" && diff.observed?.observed_status === "unknown"),
  };
}

export function applyObservedDeckToSessionState(sessionState, proposedCommit) {
  sessionState.robot_serial = proposedCommit.robot_serial || sessionState.robot_serial || null;
  sessionState.last_run_id = proposedCommit.last_run_id || sessionState.last_run_id || null;
  sessionState.needs_reconciliation = Boolean(proposedCommit.needs_reconciliation);
  sessionState.cleanup ||= {};
  sessionState.cleanup.pending_actions = proposedCommit.cleanup?.pending_actions || [];
  sessionState.cleanup.auto_home_allowed = proposedCommit.cleanup?.auto_home_allowed ?? null;

  for (const [slotName, slotState] of Object.entries(proposedCommit.deck?.slots || {})) {
    setDeckSlotState(sessionState, slotName, slotState);
  }

  sessionState.pipettes = {
    ...(sessionState.pipettes || {}),
    ...(proposedCommit.pipettes || {}),
  };

  for (const [containerKey, container] of Object.entries(proposedCommit.liquid_tracking?.containers || {})) {
    setLiquidContainerState(sessionState, {
      ...container,
      container_key: containerKey,
      trust_level: container.trust_level || "reconciled",
      why: "reconcile_state",
      step: { type: "reconcile_state", id: "reconcile_state" },
    });
  }

  return sessionState;
}

export function buildRecoverySuggestion({
  errorCategory,
  errorLeaf = null,
  run,
  commands,
  robotStatusSnapshot,
  moduleStatusSnapshot,
  nextTipSuggestion,
  slotOccupation,
  reconciliation,
  alternativeSlots = [],
  tipBindingMode = null,
  tipBindingClassification = null,
  sessionState = null,
  protocolSource = null,
  tiprackSlots = null,
} = {}) {
  const normalizedRun = normalizeRunRecord(run) || {};
  const runStatus = readNested(normalizedRun, [["status"]], null);
  const awaitingRecovery = isAwaitingRecoveryRun(run);
  const { failed_command } = extractRuntimeErrorStrings({ run, commands });
  const resolvedErrorLeaf = errorLeaf || errorCategory || "UNKNOWN_NEEDS_HUMAN";
  const robotBlockers = robotStatusSnapshot?.blockers || [];
  const preserveRuntimeFailureContextDespiteRobotBlockers =
    resolvedErrorLeaf === "INSUFFICIENT_VOLUME";
  const onlyModuleBlockerDiffs =
    Array.isArray(reconciliation?.diffs) &&
    reconciliation.diffs.length > 0 &&
    reconciliation.diffs.every(diff => diff?.type === "module_blockers");
  const reconciliationErrorLeaf = onlyModuleBlockerDiffs
    ? "MODULE_NOT_READY"
    : "SESSION_NEEDS_RECONCILIATION";

  const manualOnly = ({
    rationale,
    recommendedManualAction,
    requiredInputs = [],
    requiresConfirmation = false,
    extra = {},
  } = {}) => ({
    ...buildErrorTaxonomy({
      phase: "recovery",
      errorLeaf: resolvedErrorLeaf,
      overrides: {
        actionability: "manual_only",
        auto_executable: false,
        required_inputs: requiredInputs,
        requires_confirmation: requiresConfirmation,
        evidence_sources: ["run_history", "commands", "robot_status", "module_status", "session_state"],
      },
    }),
    error_category: errorCategory,
    action: "manual_only",
    recommended_manual_action: recommendedManualAction || null,
    hard_stop: isHardStopErrorCategory(errorCategory),
    escalate_to_human: true,
    rationale,
    ...extra,
  });

  const protocolEditRequired = ({ rationale, recommendedManualAction = null, extra = {} } = {}) => ({
    ...buildErrorTaxonomy({
      phase: "recovery",
      errorLeaf: resolvedErrorLeaf,
      overrides: {
        actionability: "protocol_edit_required",
        auto_executable: false,
        required_inputs: [],
        requires_confirmation: false,
        evidence_sources: ["run_history", "commands", "protocol_source"],
      },
    }),
    error_category: errorCategory,
    action: "protocol_edit_required",
    recommended_manual_action: recommendedManualAction,
    hard_stop: false,
    escalate_to_human: false,
    rationale,
    ...extra,
  });

  if (robotBlockers.length > 0 && !preserveRuntimeFailureContextDespiteRobotBlockers) {
    const blockerLeaf = mapRobotBlockerToLeaf(robotBlockers[0]);
    return {
      ...manualOnly({
        rationale: "robot_status_has_blockers",
        recommendedManualAction: "stop_and_notify_human",
        extra: {
          blockers: robotBlockers,
        },
      }),
      ...buildErrorTaxonomy({
        phase: "recovery",
        errorLeaf: blockerLeaf,
        overrides: {
          actionability: "manual_only",
          auto_executable: false,
          evidence_sources: ["robot_status"],
        },
      }),
    };
  }

  if (reconciliation?.diffs?.length > 0) {
    if (awaitingRecovery && onlyModuleBlockerDiffs) {
      return {
        ...buildErrorTaxonomy({
          phase: "recovery",
          errorLeaf: reconciliationErrorLeaf,
          overrides: {
            actionability: "auto_executable",
            auto_executable: true,
            required_inputs: [],
            requires_confirmation: false,
            evidence_sources: ["session_state", "module_status"],
          },
        }),
        error_category: errorCategory,
        action: "reconcile_state_first",
        hard_stop: false,
        escalate_to_human: false,
        rationale: "deck_state_diff_detected",
        diffs: reconciliation.diffs,
      };
    }

    return {
      ...manualOnly({
        rationale: "deck_state_diff_detected",
        recommendedManualAction: "reconcile_state_first",
        extra: {
          diffs: reconciliation.diffs,
        },
      }),
      ...buildErrorTaxonomy({
        phase: "recovery",
        errorLeaf: reconciliationErrorLeaf,
        overrides: {
          actionability: "manual_only",
          auto_executable: false,
          evidence_sources: ["session_state", "module_status", "deck_configuration"],
        },
      }),
      escalate_to_human: reconciliation.escalate_to_human,
    };
  }

  switch (resolvedErrorLeaf) {
    case "MODULE_NOT_READY":
      if (awaitingRecovery) {
        return {
          ...buildErrorTaxonomy({
            phase: "recovery",
            errorLeaf: resolvedErrorLeaf,
            overrides: {
              actionability: "auto_executable",
              auto_executable: true,
              required_inputs: [],
              requires_confirmation: false,
              evidence_sources: ["module_status"],
            },
          }),
          error_category: errorCategory,
          action: "wait_and_poll_module_status",
          hard_stop: false,
          escalate_to_human: false,
          rationale: "module_status_has_blockers",
          blockers: moduleStatusSnapshot?.blockers || [],
        };
      }
      return manualOnly({
        rationale: "module_status_has_blockers",
        recommendedManualAction: "wait_and_poll_module_status",
        extra: {
          blockers: moduleStatusSnapshot?.blockers || [],
        },
      });

    case "TIP_PHYSICALLY_MISSING":
      if (!nextTipSuggestion?.next_candidate) {
        return manualOnly({
          rationale: "no_viable_tip_candidates",
          recommendedManualAction: "escalate_tip_search_exhausted",
          extra: {
            tip_binding_mode: tipBindingMode,
            tip_binding_classification: tipBindingClassification,
            route: "human",
          },
        });
      }

      {
        const route = decideTipRecoveryRoute({
          errorLeaf: resolvedErrorLeaf,
          errorCategory,
          tipBindingMode,
        });

        if (route === "human") {
          return manualOnly({
            rationale: "tip_recovery_route_requires_human",
            recommendedManualAction: "inspect_tip_state_before_recovery",
            extra: {
              tip_binding_mode: tipBindingMode,
              tip_binding_classification: tipBindingClassification,
              route,
            },
          });
        }

        if (route === "replan") {
          return protocolEditRequired({
            rationale: "explicit_tip_binding_requires_continuation_protocol",
            recommendedManualAction: "generate_continuation_protocol",
            extra: {
              tip_binding_mode: tipBindingMode,
              tip_binding_classification: tipBindingClassification,
              route,
              failed_command_type: readNested(failed_command, [["commandType"]]),
              failed_well: readNested(failed_command, [["params", "wellName"]], null),
              suggested_starting_tip: nextTipSuggestion.next_candidate,
              should_resume_run: false,
            },
          });
        }
      }

      {
        const tipCandidateSummary = listTipCandidates({
          sessionState,
          run,
          tiprackSlots,
        });
        const tipBudget = assessTipRecoveryBudget({
          protocolSource: protocolSource || "",
          commands,
          viableCandidates: tipCandidateSummary.viable_candidates,
          tipBindingClassification,
        });

        if (tipBudget.enforced && !tipBudget.sufficient) {
          return manualOnly({
            rationale: tipBudget.reason,
            recommendedManualAction: "escalate_tip_search_exhausted",
            extra: {
              tip_budget: tipBudget,
              tip_binding_mode: tipBindingMode,
              tip_binding_classification: tipBindingClassification,
              route: "human",
              suggested_tip: nextTipSuggestion.next_candidate,
              operator_steps: [
                tipBudget.message,
                "Do not execute recover_tip_pickup or resume-from-recovery.",
                "Inspect deck tip loading against protocol tip budget before continuing.",
              ],
            },
          });
        }

        if (awaitingRecovery) {
          const runId = readNested(normalizedRun, [["id"]], null) || sessionState?.last_run_id || null;
          const pendingLiquidConfirm = readPendingInRunLiquidSubstitutionConfirm(sessionState, runId);
          return {
            ...buildErrorTaxonomy({
              phase: "recovery",
              errorLeaf: resolvedErrorLeaf,
              overrides: {
                actionability: "auto_executable",
                auto_executable: true,
                required_inputs: ["tiprack_slots"],
                requires_confirmation: false,
                evidence_sources: ["commands", "session_state", "protocol_source"],
              },
            }),
            error_category: errorCategory,
            action: "retry_pick_up_tip_with_next_candidate",
            hard_stop: false,
            escalate_to_human: false,
            rationale: pendingLiquidConfirm
              ? "post_liquid_substitution_confirm_only"
              : "run_is_awaiting_recovery",
            failed_command_type: readNested(failed_command, [["commandType"]]),
            failed_well: readNested(failed_command, [["params", "wellName"]], null),
            suggested_tip: nextTipSuggestion.next_candidate,
            tip_binding_mode: tipBindingMode,
            tip_binding_classification: tipBindingClassification,
            tip_budget: tipBudget,
            route: "fixit",
            intent: "fixit",
            should_resume_run: !pendingLiquidConfirm,
            post_liquid_substitution_confirm_only: Boolean(pendingLiquidConfirm),
          };
        }
      }
      return manualOnly({
        rationale: "retry_requires_recovery_context",
        recommendedManualAction: "retry_pick_up_tip_with_next_candidate",
        extra: {
          tip_binding_mode: tipBindingMode,
          tip_binding_classification: tipBindingClassification,
          route: "fixit",
        },
      });

    case "DESTINATION_OCCUPIED":
      if (awaitingRecovery && alternativeSlots.length > 0) {
        return {
          ...buildErrorTaxonomy({
            phase: "recovery",
            errorLeaf: resolvedErrorLeaf,
            overrides: {
              actionability: "manual_confirmation_required",
              auto_executable: true,
              required_inputs: ["destination_slot"],
              requires_confirmation: true,
              evidence_sources: ["commands", "deck_state"],
            },
          }),
          error_category: errorCategory,
          action: "suggest_new_destination_slot",
          hard_stop: false,
          escalate_to_human: true,
          rationale: "protocol_context_destination_occupied",
          slot_occupation: slotOccupation,
          candidate_destination_slots: alternativeSlots,
        };
      }
      return manualOnly({
        rationale: alternativeSlots.length > 0
          ? "alternative_destination_slots_available"
          : "destination_slot_is_occupied",
        recommendedManualAction: alternativeSlots.length > 0
          ? "suggest_new_destination_slot"
          : "choose_new_slot_or_escalate",
        requiredInputs: alternativeSlots.length > 0 ? ["destination_slot"] : [],
        requiresConfirmation: alternativeSlots.length > 0,
        extra: {
          slot_occupation: slotOccupation,
          candidate_destination_slots: alternativeSlots,
        },
      });

    case "MISSING_TRASH_OR_SETUP":
      return protocolEditRequired({
        rationale: "simulation_or_protocol_edit_required",
        recommendedManualAction: "stop_and_fix_protocol_source",
      });

    case "DESTINATION_UNAVAILABLE":
      return manualOnly({
        rationale: "slot_not_available_in_current_deck_configuration",
        recommendedManualAction: "fix_deck_configuration_or_protocol",
      });

    case "INSUFFICIENT_VOLUME": {
      const liquidContext = buildLiquidManualRecoveryContext({
        failedCommand: failed_command,
        robotStatusSnapshot,
        run,
        sessionState,
        commands,
        protocolSource: protocolSource || "",
      });
      if (awaitingRecovery && liquidContext.same_liquid_source_substitution_allowed) {
        const preferredCandidate = liquidContext.same_liquid_source_candidates[0] || null;
        if (liquidContext.reuse_attached_tip_eligible) {
          const volumeUnverified = isSubstituteVolumeUnverified(liquidContext.volume_check);
          // Known demand but no usable volume yet: do not auto-execute (04 STOP).
          // recover_liquid_source_substitution still probes reserve and applies the height gate.
          if (volumeUnverified) {
            return {
              ...buildErrorTaxonomy({
                phase: "recovery",
                errorLeaf: resolvedErrorLeaf,
                overrides: {
                  actionability: "manual_confirmation_required",
                  auto_executable: false,
                  required_inputs: ["reserve_volume_verification"],
                  requires_confirmation: true,
                  evidence_sources: ["run_history", "commands", "session_state"],
                },
              }),
              error_category: errorCategory,
              action: "substitute_liquid_source_with_attached_tip",
              hard_stop: false,
              escalate_to_human: true,
              rationale: "same_liquid_reserve_volume_unverified",
              recommended_manual_action: "probe_reserve_volume_via_recover_before_continuing",
              recommended_next_tools: ["recover_liquid_source_substitution"],
              volume_unverified: true,
              failed_source_key: liquidContext.source_map_key,
              preferred_source_key: preferredCandidate?.source_map_key || null,
              ...liquidContext,
            };
          }
          return {
            ...buildErrorTaxonomy({
              phase: "recovery",
              errorLeaf: resolvedErrorLeaf,
              overrides: {
                actionability: "auto_executable",
                auto_executable: true,
                required_inputs: [],
                requires_confirmation: false,
                evidence_sources: ["run_history", "commands", "session_state"],
              },
            }),
            error_category: errorCategory,
            action: "substitute_liquid_source_with_attached_tip",
            hard_stop: false,
            escalate_to_human: false,
            rationale: "same_liquid_reserve_substitution_with_attached_tip",
            recommended_next_tools: ["recover_liquid_source_substitution", "execute_protocol_recovery"],
            volume_unverified: false,
            failed_source_key: liquidContext.source_map_key,
            preferred_source_key: preferredCandidate?.source_map_key || null,
            ...liquidContext,
          };
        }
        return manualOnly({
          rationale: "same_liquid_reserve_requires_attached_tip",
          recommendedManualAction: "refill_primary_or_drop_tip_and_restart",
          extra: liquidContext,
        });
      }
      return manualOnly({
        rationale: "runtime_volume_issue_detected",
        recommendedManualAction: "probe_or_reduce_volume_then_retry",
        extra: liquidContext,
      });
    }

    case "AIR_BUBBLE":
      return manualOnly({
        rationale: "possible_air_bubble",
        recommendedManualAction: "slow_aspirate_and_change_tip",
      });

    case "TIP_CLOG":
      return manualOnly({
        rationale: "possible_tip_clog",
        recommendedManualAction: "change_tip_and_reduce_flow_rate",
      });

    case "LIQUID_PROPERTY_ERROR":
      return manualOnly({
        rationale: "liquid_property_issue_detected",
        recommendedManualAction: "adjust_liquid_class_or_parameters",
      });

    case "DECK_COLLISION":
      return manualOnly({
        rationale: "collision_class_failure",
        recommendedManualAction: "stop_and_request_human_check",
      });

    default:
      return manualOnly({
        rationale: "no_safe_automatic_branch",
        recommendedManualAction: "escalate_unknown_failure",
      });
  }
}

export function suggestAlternativeSlots({
  observedDeckState,
  sessionState,
  targetSlot = null,
  limit = 5,
} = {}) {
  const excludedSlots = new Set(
    [targetSlot].filter(Boolean).map(slotName => String(slotName).toUpperCase()),
  );
  const slotStates = observedDeckState?.slots || {};
  return listAvailableSlots({
    observedDeckState,
    sessionState,
    filter: "all",
  }).all_slots
    .filter(slot => slot.addressable && slot.status !== "occupied" && !excludedSlots.has(slot.slot_name))
    .map(slot => ({
      ...slot,
      confidence: slot.status === "empty" ? "high" : "low",
      known_fixture: (slotStates[slot.slot_name]?.observed_sources || []).includes("deck_configuration"),
    }))
    .sort((a, b) => {
      if (a.confidence !== b.confidence) {
        return a.confidence === "high" ? -1 : 1;
      }
      if (a.known_fixture !== b.known_fixture) {
        return a.known_fixture ? -1 : 1;
      }
      return FLEX_SLOT_NAMES.indexOf(a.slot_name) - FLEX_SLOT_NAMES.indexOf(b.slot_name);
    })
    .map(({ known_fixture, ...slot }) => slot)
    .slice(0, limit);
}

export function listAvailableSlots({ observedDeckState, sessionState, filter = "all" } = {}) {
  const slots = observedDeckState?.slots || {};
  const result = {
    all_slots: [],
    empty_slots: [],
    occupied_slots: [],
    unknown_slots: [],
    addressable_slots: [],
    by_slot: {},
  };

  for (const [slotName, slotState] of Object.entries(slots)) {
    const summary = {
      slot_name: slotName,
      status: slotState.observed_status,
      addressable: slotState.addressable,
      occupant_type: slotState.occupant_type,
      occupant_name: slotState.occupant_name,
      occupant_id: slotState.occupant_id,
    };

    result.all_slots.push(summary);
    result.by_slot[slotName] = summary;

    if (slotState.observed_status === "unknown") {
      result.unknown_slots.push(summary);
    } else if (slotState.observed_status === "occupied") {
      result.occupied_slots.push(summary);
    } else {
      result.empty_slots.push(summary);
    }

    if (slotState.addressable) {
      result.addressable_slots.push(summary);
    }
  }

  // For "empty" filter, include both unknown and actual empty slots
  // since unknown slots are potentially available
  if (filter === "empty") {
    return [...result.empty_slots, ...result.unknown_slots];
  }
  if (filter === "addressable") {
    return result.addressable_slots;
  }
  return result;
}

export function buildActionSummary({
  recoverySuggestion,
  nextTipSuggestion,
  run,
} = {}) {
  const summary = {
    do_what: recoverySuggestion?.action || "unknown",
    error_category: recoverySuggestion?.error_category || "UNKNOWN",
    error_leaf: recoverySuggestion?.error_leaf || "UNKNOWN_NEEDS_HUMAN",
    actionability: recoverySuggestion?.actionability || null,
    auto_executable: recoverySuggestion?.auto_executable || false,
    requires_confirmation: recoverySuggestion?.requires_confirmation || false,
    required_inputs: recoverySuggestion?.required_inputs || [],
    escalate_to_human: recoverySuggestion?.escalate_to_human || false,
    rationale: recoverySuggestion?.rationale || null,
    recovery_channel: recoverySuggestion?.recovery_channel || null,
    recovery_channel_label: recoverySuggestion?.recovery_channel_label || null,
    recommended_next_tools: recoverySuggestion?.recommended_next_tools || [],
    channel_rationale: recoverySuggestion?.channel_rationale || null,
    params: {},
    then_resume: false,
    if_fails: "escalate",
  };

  // Extract action-specific parameters
  switch (summary.do_what) {
    case "retry_pick_up_tip_with_next_candidate":
      if (nextTipSuggestion?.next_candidate) {
        summary.params = {
          well: nextTipSuggestion.next_candidate.well_name,
          tiprack_slot: nextTipSuggestion.next_candidate.tiprack_slot,
          intent: recoverySuggestion?.intent || "normal",
          tip_binding_mode: recoverySuggestion?.tip_binding_mode || null,
          route: recoverySuggestion?.route || null,
          tip_budget: recoverySuggestion?.tip_budget || null,
        };
        summary.then_resume = recoverySuggestion?.should_resume_run || false;
        summary.if_fails = "escalate_tip_search_exhausted";
      }
      break;

    case "substitute_liquid_source_with_attached_tip":
      summary.params = {
        failed_source_key:
          recoverySuggestion?.failed_source_key ||
          recoverySuggestion?.source_map_key ||
          null,
        preferred_source_key:
          recoverySuggestion?.preferred_source_key ||
          recoverySuggestion?.same_liquid_source_candidates?.[0]?.source_map_key ||
          null,
        reuse_attached_tip: true,
        reuse_attached_tip_eligible: recoverySuggestion?.reuse_attached_tip_eligible === true,
        volume_unverified: recoverySuggestion?.volume_unverified === true,
        volume_check: recoverySuggestion?.volume_check || null,
      };
      summary.then_resume = false;
      summary.recommended_next_tools = recoverySuggestion?.volume_unverified
        ? ["recover_liquid_source_substitution"]
        : ["recover_liquid_source_substitution", "execute_protocol_recovery"];
      summary.if_fails = recoverySuggestion?.volume_unverified
        ? "stop_if_reserve_volume_insufficient"
        : "manual_intervention";
      break;

    case "manual_only":
      summary.params = {
        recommended_manual_action: recoverySuggestion?.recommended_manual_action || null,
        tip_budget: recoverySuggestion?.tip_budget || null,
        operator_steps: recoverySuggestion?.operator_steps || [],
        cleanup_required: recoverySuggestion?.cleanup_required || [],
        source_map_key: recoverySuggestion?.source_map_key || null,
        source_map_expected_presence: recoverySuggestion?.source_map_expected_presence ?? null,
        observed_liquid_presence: recoverySuggestion?.observed_liquid_presence ?? null,
        source_map_expectation_mismatch: recoverySuggestion?.source_map_expectation_mismatch ?? null,
        blocked_auto_recovery_reason: recoverySuggestion?.blocked_auto_recovery_reason || null,
        reuse_attached_tip_eligible: recoverySuggestion?.reuse_attached_tip_eligible === true,
      };
      summary.then_resume = false;
      summary.if_fails =
        recoverySuggestion?.recommended_manual_action === "escalate_tip_search_exhausted"
          ? "manual_intervention"
          : "manual_intervention";
      break;

    case "protocol_edit_required":
      summary.params = {
        recommended_manual_action: recoverySuggestion?.recommended_manual_action || null,
        tip_binding_mode: recoverySuggestion?.tip_binding_mode || null,
        route: recoverySuggestion?.route || null,
        starting_tip: recoverySuggestion?.suggested_starting_tip?.well_name || null,
        tiprack_slot: recoverySuggestion?.suggested_starting_tip?.tiprack_slot || null,
      };
      summary.then_resume = false;
      summary.if_fails = "human_generate_continuation_protocol";
      break;

    case "choose_new_slot_or_escalate":
      summary.params = {
        target_slot: recoverySuggestion?.slot_occupation?.slot_name || null,
        current_occupant: recoverySuggestion?.slot_occupation?.occupant_name || null,
      };
      summary.if_fails = "human_clear_slot";
      break;

    case "suggest_new_destination_slot":
      summary.params = {
        target_slot: recoverySuggestion?.slot_occupation?.slot_name || null,
        candidate_destination_slots: recoverySuggestion?.candidate_destination_slots || [],
      };
      summary.then_resume = true;
      summary.if_fails = "human_choose_destination_slot";
      break;

    case "wait_and_poll_module_status":
      summary.params = {
        blockers: recoverySuggestion?.blockers || [],
        poll_interval_ms: 5000,
      };
      summary.if_fails = "escalate_module_timeout";
      break;

    case "stop_and_fix_protocol_source":
      summary.params = {
        protocol_file: "local_protocol.py",
      };
      summary.if_fails = "escalate_runtime_fix";
      break;

    case "stop_and_notify_human":
      summary.params = {
        blockers: recoverySuggestion?.blockers || [],
      };
      summary.if_fails = "manual_intervention";
      break;

    case "stop_and_request_human_check":
      summary.params = {
        reason: "collision_detected",
      };
      summary.if_fails = "manual_intervention";
      break;

    case "slow_aspirate_and_change_tip":
      summary.params = {
        speed_multiplier: 0.5,
        change_tip: true,
      };
      summary.if_fails = "escalate";
      break;

    case "change_tip_and_reduce_flow_rate":
      summary.params = {
        flow_rate_multiplier: 0.7,
      };
      summary.if_fails = "escalate";
      break;

    case "adjust_liquid_class_or_parameters":
      summary.params = {
        reason: "liquid_property_issue",
      };
      summary.if_fails = "human_liquid_setup";
      break;

    case "reconcile_state_first":
      summary.params = {
        diffs: recoverySuggestion?.diffs || [],
      };
      summary.if_fails = "escalate_reconciliation_failed";
      break;

    case "manual_only":
      summary.params = {
        recommended_manual_action: recoverySuggestion?.recommended_manual_action || null,
        failed_well: recoverySuggestion?.failed_well || null,
        source_labware_id: recoverySuggestion?.source_labware_id || null,
        source_slot: recoverySuggestion?.source_slot || null,
        source_map_key: recoverySuggestion?.source_map_key || null,
        liquid_source: recoverySuggestion?.liquid_source || null,
        source_map_expected_presence: recoverySuggestion?.source_map_expected_presence ?? null,
        observed_liquid_presence: recoverySuggestion?.observed_liquid_presence ?? null,
        source_map_expectation_mismatch: recoverySuggestion?.source_map_expectation_mismatch || false,
        same_liquid_source_candidates: recoverySuggestion?.same_liquid_source_candidates || [],
        same_liquid_source_candidate_count: recoverySuggestion?.same_liquid_source_candidate_count || 0,
        same_liquid_source_substitution_allowed:
          recoverySuggestion?.same_liquid_source_substitution_allowed || false,
        same_liquid_source_substitution_next_tool:
          recoverySuggestion?.same_liquid_source_substitution_next_tool || null,
        same_liquid_source_substitution_playbook:
          recoverySuggestion?.same_liquid_source_substitution_playbook || null,
        same_liquid_source_substitution_required_gates:
          recoverySuggestion?.same_liquid_source_substitution_required_gates || [],
        same_liquid_auto_resume_eligible: recoverySuggestion?.same_liquid_auto_resume_eligible || false,
        same_liquid_auto_resume_blocker: recoverySuggestion?.same_liquid_auto_resume_blocker || null,
        failed_command_id: recoverySuggestion?.failed_command_id || null,
        failed_command_type: recoverySuggestion?.failed_command_type || null,
        blocked_auto_recovery_reason: recoverySuggestion?.blocked_auto_recovery_reason || null,
        operator_steps: recoverySuggestion?.operator_steps || [],
        cleanup_required: recoverySuggestion?.cleanup_required || [],
        candidate_destination_slots: recoverySuggestion?.candidate_destination_slots || [],
        blockers: recoverySuggestion?.blockers || [],
      };
      summary.if_fails = "manual_intervention";
      break;

    case "protocol_edit_required":
      summary.params = {
        recommended_manual_action: recoverySuggestion?.recommended_manual_action || null,
      };
      summary.if_fails = "edit_protocol_and_retry_simulation";
      break;

    default:
      summary.params = {
        raw_recovery: recoverySuggestion,
      };
      break;
  }

  return summary;
}
