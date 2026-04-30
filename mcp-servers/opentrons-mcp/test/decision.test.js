import test from "node:test";
import assert from "node:assert/strict";

import {
  applyObservedDeckToSessionState,
  buildActionSummary,
  buildHomeSafetyResult,
  buildObservedDeckState,
  buildReconciliationResult,
  buildRecoverySuggestion,
  classifyRecoveryError,
  getSlotOccupationSummary,
  isHardStopErrorCategory,
  listAvailableSlots,
  listTipCandidates,
  parseRuntimeError,
  suggestAlternativeSlots,
  suggestNextTipWell,
} from "../lib/decision.js";

function buildSessionState() {
  return {
    session_id: "test-session",
    state_revision: 0,
    robot_serial: "FLX-TEST",
    last_run_id: null,
    needs_reconciliation: false,
    deck: { slots: {} },
    pipettes: {},
    tip_tracking: { tipracks: {} },
    cleanup: { pending_actions: [], auto_home_allowed: null },
    updated_at: "2026-03-24T00:00:00.000Z",
  };
}

test("buildObservedDeckState marks modules, trash, and run labware", () => {
  const observed = buildObservedDeckState({
    deckConfiguration: {
      data: {
        cutoutFixtures: [
          { cutoutFixtureId: "thermocyclerModuleV2Rear", cutoutId: "cutoutA1" },
          { cutoutFixtureId: "trashBinAdapter", cutoutId: "cutoutA3" },
          { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutC2" },
        ],
      },
    },
    modules: {
      data: [{ serialNumber: "TC123", moduleModel: "thermocyclerModuleV2", moduleOffset: { slot: "A1" } }],
    },
    run: {
      data: {
        id: "run-1",
        labware: [
          {
            id: "tiprack-1",
            loadName: "opentrons_flex_96_tiprack_1000ul",
            location: { slotName: "C2" },
          },
        ],
      },
    },
  });

  assert.equal(observed.slots.A1.occupant_type, "module");
  assert.equal(observed.slots.A3.occupant_type, "trash_bin");
  assert.equal(observed.slots.C2.occupant_type, "labware");
});

test("getSlotOccupationSummary reports mismatched committed state", () => {
  const sessionState = buildSessionState();
  sessionState.deck.slots.C2 = {
    slot_name: "C2",
    observed_status: "occupied",
    occupant_type: "labware",
    occupant_name: "old_plate",
  };
  const observed = buildObservedDeckState({
    deckConfiguration: {
      data: { cutoutFixtures: [{ cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutC2" }] },
    },
    run: {
      data: {
        labware: [{ id: "plate-1", loadName: "new_plate", location: { slotName: "C2" } }],
      },
    },
  });

  const summary = getSlotOccupationSummary({
    slotName: "C2",
    observedDeckState: observed,
    sessionState,
  });

  assert.equal(summary.status, "mismatched");
  assert.equal(summary.mismatched_against_committed, true);
});

test("listTipCandidates follows column-major order and skips tracked wells", () => {
  const sessionState = buildSessionState();
  sessionState.tip_tracking.tipracks.C2 = {
    slot_name: "C2",
    load_name: "opentrons_flex_96_tiprack_1000ul",
    search_order: ["A1", "B1", "C1"],
    missing_wells: ["A1"],
    depleted_wells: ["B1"],
    unknown_blocked_wells: [],
  };

  const candidates = listTipCandidates({
    sessionState,
    tiprackSlots: ["C2"],
  });

  assert.equal(candidates.viable_candidates[0].well_name, "C1");
  assert.equal(candidates.blocked_candidates.length, 2);
});

test("suggestNextTipWell marks failed well and proposes next viable well", () => {
  const sessionState = buildSessionState();
  const suggestion = suggestNextTipWell({
    sessionState,
    tiprackSlots: ["C2"],
    tiprackSlot: "C2",
    failedWell: "A1",
  });

  assert.equal(suggestion.failed_well, "A1");
  assert.equal(suggestion.next_candidate.well_name, "B1");
  assert.deepEqual(sessionState.tip_tracking.tipracks.C2.missing_wells, ["A1"]);
});

test("buildHomeSafetyResult blocks home when tip attached or reconciliation pending", () => {
  const sessionState = buildSessionState();
  sessionState.needs_reconciliation = true;
  const result = buildHomeSafetyResult({
    sessionState,
    robotStatusSnapshot: {
      blockers: [],
      instruments_summary: [{ mount: "left", tip_detected: true }],
    },
  });

  assert.equal(result.auto_home_allowed, false);
  assert.deepEqual(result.minimum_cleanup_actions, ["drop_tip:left"]);
  assert.ok(result.blockers.includes("needs_reconciliation"));
});

test("buildHomeSafetyResult keeps a clear safe-home matrix with deduped cleanup actions", () => {
  const sessionState = buildSessionState();
  sessionState.cleanup.pending_actions = ["drop_tip:left", "move_to_maintenance_position", "drop_tip:left"];
  const result = buildHomeSafetyResult({
    sessionState,
    robotStatusSnapshot: {
      blockers: ["door_open"],
      instruments_summary: [{ mount: "left", tip_detected: true }],
    },
  });

  assert.equal(result.auto_home_allowed, false);
  assert.ok(result.blockers.includes("door_open"));
  assert.ok(result.blockers.includes("tip_attached:left"));
  assert.deepEqual(result.minimum_cleanup_actions, ["drop_tip:left", "move_to_maintenance_position"]);
});

test("buildReconciliationResult reports tip mismatch and can apply observed state", () => {
  const sessionState = buildSessionState();
  sessionState.pipettes.left = { tip_attached: true };

  const observedDeckState = buildObservedDeckState({
    deckConfiguration: {
      data: {
        cutoutFixtures: [
          { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutC2" },
          { cutoutFixtureId: "trashBinAdapter", cutoutId: "cutoutA3" },
        ],
      },
    },
    run: {
      data: {
        id: "run-2",
        labware: [
          {
            id: "tiprack-1",
            loadName: "opentrons_flex_96_tiprack_1000ul",
            location: { slotName: "C2" },
          },
        ],
      },
    },
  });

  const reconciliation = buildReconciliationResult({
    sessionState,
    robotStatusSnapshot: {
      health_summary: { robot_serial: "FLX-TEST" },
      instruments_summary: [{ mount: "left", instrument_name: "p1000_single_flex", tip_detected: false }],
    },
    moduleStatusSnapshot: { blockers: [] },
    observedDeckState,
    run: { data: { id: "run-2" } },
  });

  assert.equal(reconciliation.confidence, "high");
  assert.ok(reconciliation.diffs.some(diff => diff.type === "tip_attachment_mismatch"));

  applyObservedDeckToSessionState(sessionState, reconciliation.proposed_commit);
  assert.equal(sessionState.pipettes.left.tip_attached, false);
  assert.equal(sessionState.deck.slots.C2.occupant_name, "opentrons_flex_96_tiprack_1000ul");
});

test("classifyRecoveryError and buildRecoverySuggestion handle tip recovery", () => {
  const classification = classifyRecoveryError({
    run: {
      data: {
        id: "run-3",
        status: "awaiting-recovery",
      },
    },
    commands: {
      data: [
        {
          commandType: "pickUpTip",
          status: "failed",
          error: { detail: "No Tip Detected" },
          params: { wellName: "A1" },
        },
      ],
    },
    moduleStatusSnapshot: { blockers: [] },
    robotStatusSnapshot: { blockers: [] },
  });

  const suggestion = buildRecoverySuggestion({
    errorCategory: classification.error_category,
    run: { data: { status: "awaiting-recovery" } },
    commands: {
      data: [
        {
          commandType: "pickUpTip",
          status: "failed",
          params: { wellName: "A1" },
        },
      ],
    },
    robotStatusSnapshot: { blockers: [] },
    moduleStatusSnapshot: { blockers: [] },
    nextTipSuggestion: {
      next_candidate: {
        tiprack_slot: "C2",
        well_name: "B1",
      },
    },
    reconciliation: { diffs: [] },
  });

  assert.equal(classification.error_category, "TIP_PHYSICALLY_MISSING");
  assert.equal(suggestion.action, "retry_pick_up_tip_with_next_candidate");
  assert.equal(suggestion.intent, "fixit");
  assert.equal(suggestion.suggested_tip.well_name, "B1");
});

test("classifyRecoveryError prioritizes run-level protocol setup errors", () => {
  const classification = classifyRecoveryError({
    run: {
      data: {
        id: "run-4",
        status: "failed",
        errors: [{ detail: "NoTrashDefinedError: No trash container has been defined in this protocol." }],
      },
    },
    commands: {
      data: [
        {
          commandType: "pickUpTip",
          status: "failed",
          error: { detail: "No Tip Detected" },
        },
      ],
    },
    moduleStatusSnapshot: { blockers: [] },
    robotStatusSnapshot: { blockers: [] },
  });

  assert.equal(classification.error_category, "PROTOCOL_SETUP_ERROR");
  assert.equal(classification.error_leaf, "MISSING_TRASH_OR_SETUP");
});

test("parseRuntimeError extracts move destination and escalation", () => {
  const parsed = parseRuntimeError({
    run: {
      data: {
        id: "run-occupied",
        status: "failed",
      },
    },
    commands: {
      data: [
        {
          id: "cmd-move-1",
          commandType: "moveLabware",
          status: "failed",
          params: {
            labwareId: "labware-1",
            newLocation: { slotName: "B1" },
          },
          error: {
            errorType: "LocationIsOccupiedError",
            detail: "LocationIsOccupiedError: destination occupied",
          },
        },
      ],
    },
    moduleStatusSnapshot: { blockers: [] },
    robotStatusSnapshot: { blockers: [] },
  });

  assert.equal(parsed.error_category, "DESTINATION_OCCUPIED");
  assert.equal(parsed.error_leaf, "DESTINATION_OCCUPIED");
  assert.equal(parsed.target_slot, "B1");
  assert.equal(parsed.source_labware_id, "labware-1");
  assert.equal(parsed.escalate_to_human, true);
  assert.equal(parsed.hard_stop, false);
  assert.equal(parsed.actionability, "manual_only");
  assert.equal(parsed.auto_executable, false);
});

test("listAvailableSlots groups slots by availability", () => {
  const sessionState = buildSessionState();
  const observed = buildObservedDeckState({
    deckConfiguration: {
      data: {
        cutoutFixtures: [
          { cutoutFixtureId: "thermocyclerModuleV2Rear", cutoutId: "cutoutA1" },
          { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutA2" },
          { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutB2" },
          { cutoutFixtureId: "trashBinAdapter", cutoutId: "cutoutA3" },
        ],
      },
    },
    modules: {
      data: [{ serialNumber: "TC123", moduleModel: "thermocyclerModuleV2", moduleOffset: { slot: "A1" } }],
    },
    run: {
      data: {
        labware: [
          { id: "plate-1", loadName: "plate_96", location: { slotName: "A2" } },
        ],
      },
    },
  });

  const result = listAvailableSlots({ observedDeckState: observed, sessionState, filter: "all" });

  assert.equal(result.all_slots.length, 12);
  assert.equal(result.occupied_slots.length, 3);
  assert.equal(result.empty_slots.length, 0);
  assert.equal(result.unknown_slots.length, 9);
  assert.ok(result.by_slot.A1.occupant_type === "module");
  assert.ok(result.by_slot.A2.occupant_type === "labware");
  assert.ok(result.by_slot.A3.occupant_type === "trash_bin");
});

test("listAvailableSlots with empty filter returns unoccupied slots including unknown", () => {
  const sessionState = buildSessionState();
  const observed = buildObservedDeckState({
    deckConfiguration: {
      data: {
        cutoutFixtures: [
          { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutA2" },
          { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutB2" },
        ],
      },
    },
    run: {
      data: {
        labware: [{ id: "plate-1", loadName: "plate_96", location: { slotName: "A2" } }],
      },
    },
  });

  const result = listAvailableSlots({ observedDeckState: observed, sessionState, filter: "empty" });

  // empty filter returns both unknown and empty slots (all non-occupied)
  assert.equal(result.length, 11);
  assert.ok(result.every(slot => slot.observed_status !== "occupied"));
});

test("buildActionSummary extracts actionable parameters from recovery", () => {
  const recoverySuggestion = {
    error_category: "TIP_PHYSICALLY_MISSING",
    action: "retry_pick_up_tip_with_next_candidate",
    escalate_to_human: false,
    rationale: "run_is_awaiting_recovery",
    suggested_tip: { well_name: "B1", tiprack_slot: "C2" },
    intent: "fixit",
    should_resume_run: true,
  };

  const summary = buildActionSummary({
    recoverySuggestion,
    nextTipSuggestion: {
      next_candidate: { well_name: "B1", tiprack_slot: "C2" },
    },
  });

  assert.equal(summary.do_what, "retry_pick_up_tip_with_next_candidate");
  assert.equal(summary.params.well, "B1");
  assert.equal(summary.params.tiprack_slot, "C2");
  assert.equal(summary.params.intent, "fixit");
  assert.equal(summary.then_resume, true);
  assert.equal(summary.if_fails, "escalate_tip_search_exhausted");
  assert.equal(summary.escalate_to_human, false);
});

test("buildActionSummary includes candidate slots for destination recovery", () => {
  const recoverySuggestion = {
    error_category: "DESTINATION_OCCUPIED",
    action: "suggest_new_destination_slot",
    escalate_to_human: true,
    rationale: "protocol_context_destination_occupied",
    slot_occupation: {
      slot_name: "B1",
    },
    candidate_destination_slots: [
      { slot_name: "C2", confidence: "high" },
      { slot_name: "D2", confidence: "low" },
    ],
  };

  const summary = buildActionSummary({
    recoverySuggestion,
  });

  assert.equal(summary.do_what, "suggest_new_destination_slot");
  assert.equal(summary.params.target_slot, "B1");
  assert.equal(summary.params.candidate_destination_slots[0].slot_name, "C2");
  assert.equal(summary.then_resume, true);
  assert.equal(summary.if_fails, "human_choose_destination_slot");
});

test("suggestAlternativeSlots returns addressable non-occupied slots with confidence", () => {
  const sessionState = buildSessionState();
  const observed = buildObservedDeckState({
    deckConfiguration: {
      data: {
        cutoutFixtures: [
          { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutA1" },
          { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutA2" },
          { cutoutFixtureId: "singleCenterSlot", cutoutId: "cutoutB1" },
        ],
      },
    },
    run: {
      data: {
        labware: [{ id: "plate-1", loadName: "plate_96", location: { slotName: "A1" } }],
      },
    },
  });

  const alternatives = suggestAlternativeSlots({
    observedDeckState: observed,
    sessionState,
    targetSlot: "A1",
  });

  assert.equal(alternatives[0].slot_name, "A2");
  assert.equal(alternatives[0].confidence, "low");
  assert.ok(alternatives.every(slot => slot.slot_name !== "A1"));
});

test("buildRecoverySuggestion recommends alternative destination slots when available", () => {
  const suggestion = buildRecoverySuggestion({
    errorCategory: "DESTINATION_OCCUPIED",
    errorLeaf: "DESTINATION_OCCUPIED",
    run: { data: { status: "running" } },
    commands: { data: [] },
    robotStatusSnapshot: { blockers: [] },
    moduleStatusSnapshot: { blockers: [] },
    slotOccupation: {
      slot_name: "B1",
      status: "occupied",
      occupant_type: "labware",
      occupant_name: "plate_96",
    },
    reconciliation: { diffs: [] },
    alternativeSlots: [
      { slot_name: "C2", status: "empty", addressable: true, confidence: "high" },
      { slot_name: "D2", status: "unknown", addressable: true, confidence: "low" },
    ],
  });

  assert.equal(suggestion.action, "manual_only");
  assert.equal(suggestion.actionability, "manual_only");
  assert.equal(suggestion.auto_executable, false);
  assert.equal(suggestion.requires_confirmation, true);
  assert.equal(suggestion.required_inputs[0], "destination_slot");
  assert.equal(suggestion.recommended_manual_action, "suggest_new_destination_slot");
  assert.equal(suggestion.escalate_to_human, true);
  assert.equal(suggestion.candidate_destination_slots[0].slot_name, "C2");
  assert.equal(suggestion.hard_stop, false);
});

test("buildRecoverySuggestion keeps protocol destination recovery human-reviewed even with confident slot", () => {
  const suggestion = buildRecoverySuggestion({
    errorCategory: "DESTINATION_OCCUPIED",
    errorLeaf: "DESTINATION_OCCUPIED",
    run: { data: { status: "awaiting-recovery", currentlyRecoveringFrom: "cmd-1" } },
    commands: { data: [] },
    robotStatusSnapshot: { blockers: [] },
    moduleStatusSnapshot: { blockers: [] },
    slotOccupation: {
      slot_name: "B1",
      status: "occupied",
      occupant_type: "labware",
      occupant_name: "plate_96",
    },
    reconciliation: { diffs: [] },
    alternativeSlots: [{ slot_name: "C2", status: "empty", addressable: true, confidence: "high" }],
  });

  assert.equal(suggestion.action, "suggest_new_destination_slot");
  assert.equal(suggestion.actionability, "manual_confirmation_required");
  assert.equal(suggestion.auto_executable, true);
  assert.equal(suggestion.requires_confirmation, true);
  assert.equal(suggestion.escalate_to_human, true);
  assert.equal(suggestion.rationale, "protocol_context_destination_occupied");
  assert.equal(suggestion.hard_stop, false);
});

test("buildRecoverySuggestion escalates when destination recovery has no candidates", () => {
  const suggestion = buildRecoverySuggestion({
    errorCategory: "DESTINATION_OCCUPIED",
    errorLeaf: "DESTINATION_OCCUPIED",
    run: { data: { status: "running" } },
    commands: { data: [] },
    robotStatusSnapshot: { blockers: [] },
    moduleStatusSnapshot: { blockers: [] },
    slotOccupation: {
      slot_name: "B1",
      status: "occupied",
      occupant_type: "labware",
      occupant_name: "plate_96",
    },
    reconciliation: { diffs: [] },
    alternativeSlots: [],
  });

  assert.equal(suggestion.action, "manual_only");
  assert.equal(suggestion.actionability, "manual_only");
  assert.equal(suggestion.recommended_manual_action, "choose_new_slot_or_escalate");
  assert.equal(suggestion.escalate_to_human, true);
  assert.equal(suggestion.hard_stop, false);
});

test("buildRecoverySuggestion keeps liquid issues manual-only when no supported fixit exists", () => {
  const suggestion = buildRecoverySuggestion({
    errorCategory: "INSUFFICIENT_VOLUME",
    errorLeaf: "INSUFFICIENT_VOLUME",
    run: { data: { status: "awaiting-recovery" } },
    commands: { data: [] },
    robotStatusSnapshot: { blockers: [] },
    moduleStatusSnapshot: { blockers: [] },
    reconciliation: { diffs: [] },
  });

  assert.equal(suggestion.action, "manual_only");
  assert.equal(suggestion.actionability, "manual_only");
  assert.equal(suggestion.auto_executable, false);
  assert.equal(suggestion.recommended_manual_action, "probe_or_reduce_volume_then_retry");
});

test("collision and unknown classes are explicit hard stops", () => {
  const collisionSuggestion = buildRecoverySuggestion({
    errorCategory: "DECK_COLLISION",
    run: { data: { status: "failed" } },
    commands: { data: [] },
    robotStatusSnapshot: { blockers: [] },
    moduleStatusSnapshot: { blockers: [] },
    reconciliation: { diffs: [] },
  });
  const unknownSuggestion = buildRecoverySuggestion({
    errorCategory: "UNKNOWN",
    run: { data: { status: "failed" } },
    commands: { data: [] },
    robotStatusSnapshot: { blockers: [] },
    moduleStatusSnapshot: { blockers: [] },
    reconciliation: { diffs: [] },
  });

  assert.equal(isHardStopErrorCategory("DECK_COLLISION"), true);
  assert.equal(isHardStopErrorCategory("UNKNOWN"), true);
  assert.equal(isHardStopErrorCategory("DESTINATION_OCCUPIED"), false);
  assert.equal(collisionSuggestion.hard_stop, true);
  assert.equal(collisionSuggestion.escalate_to_human, true);
  assert.equal(unknownSuggestion.hard_stop, true);
  assert.equal(unknownSuggestion.escalate_to_human, true);
});

test("parseRuntimeError marks collision-class failures as hard stops", () => {
  const parsed = parseRuntimeError({
    run: { data: { id: "run-collision", status: "failed" } },
    commands: {
      data: [
        {
          id: "cmd-collision-1",
          commandType: "moveLabware",
          status: "failed",
          error: {
            errorType: "StallOrCollisionError",
            detail: "stallOrCollision while moving labware",
          },
        },
      ],
    },
    moduleStatusSnapshot: { blockers: [] },
    robotStatusSnapshot: { blockers: [] },
  });

  assert.equal(parsed.error_category, "DECK_COLLISION");
  assert.equal(parsed.hard_stop, true);
  assert.equal(parsed.escalate_to_human, true);
});
