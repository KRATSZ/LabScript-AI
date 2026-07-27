import fs from "fs";
import path from "path";

import { analyzeLiquidProtocolGuards } from "./liquid-protocol-guards.js";
import {
  buildPlaybookGateSummary,
  summarizeRecoveryPlaybook,
} from "./recovery-playbooks.js";

export const LIQUID_SOURCE_SUBSTITUTION_PLAYBOOK_ID = "liquid_source_substitution_continuation_protocol";

function normalize(value) {
  return String(value || "").trim();
}

function normalizeUpper(value) {
  return normalize(value).toUpperCase();
}

export function normalizeLiquidIdentity(value) {
  return normalize(value).toLowerCase();
}

export function isSpecificLiquidIdentity(value) {
  const normalized = normalizeLiquidIdentity(value);
  return Boolean(
    normalized &&
      !normalized.startsWith("todo") &&
      !["operator-confirmed-liquid", "unknown", "unspecified", "liquid"].includes(normalized),
  );
}

export function isGenericReagentLiquid(value) {
  const normalized = normalizeLiquidIdentity(value).replace(/[_\s]+/g, "-");
  return [
    "water",
    "h2o",
    "distilled-water",
    "deionized-water",
    "di-water",
    "nuclease-free-water",
  ].includes(normalized);
}

export function liquidSourceKey({ slotName, wellName } = {}) {
  const slot = normalizeUpper(slotName);
  const well = normalizeUpper(wellName);
  return slot && well ? `${slot}.${well}` : null;
}

function sourceWithKey(key, source = {}) {
  const [slotName, wellName] = String(key || "").split(".");
  return {
    source_map_key: key,
    slot_name: source.slot_name || slotName || null,
    well_name: source.well_name || wellName || null,
    labware_load_name: source.labware_load_name || null,
    liquid_name: source.liquid_name || null,
    sample_id: source.sample_id || null,
    expected_presence: source.expected_presence ?? null,
    observed_presence: source.observed_presence ?? null,
    observed_at: source.observed_at || null,
    observed_run_id: source.observed_run_id || null,
    observed_source: source.observed_source || null,
  };
}

function pythonLiteral(value) {
  return JSON.stringify(value);
}

function invariantCheck(name, passed, {
  severity = "must_preserve",
  expected = true,
  observed = null,
  detail = null,
} = {}) {
  return {
    name,
    status: passed ? "pass" : "fail",
    severity,
    expected,
    observed,
    detail,
  };
}

function applyFinalAutoResumeGates(plan) {
  const autoResumeEligible = plan.auto_resume_eligible === true;
  const suffixSufficient = plan.suffix_sufficient === true;
  plan.final_auto_resume_eligible = autoResumeEligible && suffixSufficient;
  if (autoResumeEligible && !suffixSufficient) {
    plan.blocked_reason = "suffix_plan_not_sufficient";
  } else if (autoResumeEligible && suffixSufficient) {
    plan.blocked_reason = "liquid_source_substitution_ready_for_registered_executor_after_validation_and_live_gate";
  }
  return plan;
}

export function setSuffixSufficiencyOnPlan(plan, suffixResult) {
  if (!plan) {
    return plan;
  }
  plan.suffix_sufficient = suffixResult?.ok === true;
  plan.suffix_violations = suffixResult?.violations ?? null;
  return applyFinalAutoResumeGates(plan);
}

function sampleIdPolicySatisfied(failedSource = {}, selectedSource = {}) {
  if (isGenericReagentLiquid(failedSource?.liquid_name)) {
    return true;
  }
  const failedSampleId = failedSource?.sample_id || null;
  const selectedSampleId = selectedSource?.sample_id || null;
  return !failedSampleId || !selectedSampleId || failedSampleId === selectedSampleId;
}

export function validateLiquidSourceSubstitutionInvariants({
  plan,
  validationProtocol = null,
  simulationParse = null,
  liveGatePassed = false,
  operatorOptIn = false,
  liveExecutionAllowed = false,
  liveProtocolRunAllowed = false,
} = {}) {
  const failedSource = plan?.failed_source || null;
  const selectedSource = plan?.selected_source || null;
  const liquidNameMatches = Boolean(
    failedSource &&
      selectedSource &&
      normalizeLiquidIdentity(failedSource.liquid_name) === normalizeLiquidIdentity(selectedSource.liquid_name),
  );
  const guard = validationProtocol?.liquid_guard_analysis || null;
  const hasValidationProtocol = Boolean(validationProtocol);
  const noUnapprovedLiveExecution =
    (liveExecutionAllowed !== true && liveProtocolRunAllowed !== true) ||
    (liveGatePassed === true && operatorOptIn === true);

  const checks = [
    invariantCheck("liquid_name_unchanged", liquidNameMatches, {
      observed: {
        failed: failedSource?.liquid_name || null,
        replacement: selectedSource?.liquid_name || null,
      },
    }),
    invariantCheck("sample_id_policy_satisfied", sampleIdPolicySatisfied(failedSource, selectedSource), {
      observed: {
        policy: plan?.patch?.sample_id_policy || null,
        failed: failedSource?.sample_id || null,
        replacement: selectedSource?.sample_id || null,
      },
    }),
    invariantCheck("failed_source_expected_present", failedSource?.expected_presence === true, {
      observed: failedSource?.expected_presence ?? null,
    }),
    invariantCheck("replacement_source_expected_present", selectedSource?.expected_presence === true, {
      observed: selectedSource?.expected_presence ?? null,
    }),
    invariantCheck("replacement_source_not_observed_empty", selectedSource?.observed_presence !== false, {
      observed: selectedSource?.observed_presence ?? null,
    }),
    invariantCheck("first_liquid_action_requires_presence", !hasValidationProtocol || guard?.first_aspirate_guarded === true, {
      observed: guard?.first_aspirate_guarded ?? null,
      detail: hasValidationProtocol ? "validation_protocol_checked" : "not_checked_until_protocol_generation",
    }),
    invariantCheck(
      "validation_protocol_has_no_aspirate_or_dispense",
      !hasValidationProtocol || validationProtocol?.no_aspirate_or_dispense === true,
      {
        observed: validationProtocol?.no_aspirate_or_dispense ?? null,
        detail: hasValidationProtocol ? "validation_protocol_checked" : "not_checked_until_protocol_generation",
      },
    ),
    invariantCheck("no_live_execution_before_gate_and_operator_opt_in", noUnapprovedLiveExecution, {
      observed: {
        liveExecutionAllowed,
        liveProtocolRunAllowed,
        liveGatePassed,
        operatorOptIn,
      },
    }),
    invariantCheck("replacement_source_live_presence_observed", selectedSource?.observed_presence === true, {
      severity: "gate",
      observed: selectedSource?.observed_presence ?? null,
    }),
    invariantCheck("simulation_passed", !simulationParse || simulationParse.status === "passed", {
      severity: "gate",
      observed: simulationParse?.status || null,
    }),
    invariantCheck("live_liquid_recovery_gate_passed", liveGatePassed === true, {
      severity: "gate",
      observed: liveGatePassed,
    }),
    invariantCheck("operator_opt_in", operatorOptIn === true, {
      severity: "gate",
      observed: operatorOptIn,
    }),
  ];

  const failedMustPreserve = checks.filter(check => check.severity === "must_preserve" && check.status !== "pass");
  const failedGates = checks.filter(check => check.severity === "gate" && check.status !== "pass");
  const observedGates = {
    specific_liquid_identity: isSpecificLiquidIdentity(failedSource?.liquid_name),
    same_liquid_identity: liquidNameMatches,
    replacement_source_expected_present: selectedSource?.expected_presence === true,
    replacement_source_live_presence_observed: selectedSource?.observed_presence === true,
    simulate_protocol: simulationParse?.status === "passed",
    live_liquid_recovery_gate: liveGatePassed === true,
    run_protocol_only_after_operator_opt_in: operatorOptIn === true,
  };

  return {
    playbook: summarizeRecoveryPlaybook(LIQUID_SOURCE_SUBSTITUTION_PLAYBOOK_ID),
    status:
      failedMustPreserve.length > 0
        ? "failed"
        : failedGates.length > 0
          ? "blocked"
          : "pass",
    experiment_intent_violation_count: failedMustPreserve.length,
    gate_blocker_count: failedGates.length,
    failed_checks: failedMustPreserve.map(check => check.name),
    missing_gates: failedGates.map(check => check.name),
    checks,
    playbook_gate_summary: buildPlaybookGateSummary(
      LIQUID_SOURCE_SUBSTITUTION_PLAYBOOK_ID,
      observedGates,
    ),
  };
}

export function findSameLiquidSourceCandidates({ sources = {}, failedKey = null, failedSource = null } = {}) {
  const liquidName = failedSource?.liquid_name || null;
  if (!failedKey || !failedSource || !isSpecificLiquidIdentity(liquidName)) {
    return [];
  }

  const genericReagent = isGenericReagentLiquid(liquidName);
  const failedSampleId = failedSource.sample_id || null;
  return Object.entries(sources)
    .filter(([key, source]) => {
      if (key === failedKey) {
        return false;
      }
      if (source?.expected_presence !== true) {
        return false;
      }
      if (source?.observed_presence === false) {
        return false;
      }
      if (normalizeLiquidIdentity(source?.liquid_name) !== normalizeLiquidIdentity(liquidName)) {
        return false;
      }
      const candidateSampleId = source?.sample_id || null;
      if (genericReagent) {
        return true;
      }
      return !failedSampleId || !candidateSampleId || failedSampleId === candidateSampleId;
    })
    .map(([key, source]) => sourceWithKey(key, source));
}

export function buildLiquidSourceSubstitutionPlan({
  sessionState,
  failedSourceKey = null,
  failedSlotName = null,
  failedWellName = null,
  preferredSourceKey = null,
} = {}) {
  const sources = sessionState?.liquid_tracking?.sources || {};
  const resolvedFailedKey =
    failedSourceKey || liquidSourceKey({ slotName: failedSlotName, wellName: failedWellName });
  const failedSource = resolvedFailedKey ? sources[resolvedFailedKey] || null : null;

  const base = {
    status: "blocked",
    ready_for_registered_executor: false,
    auto_resume_eligible: false,
    auto_resume_blocker: null,
    suffix_sufficient: false,
    suffix_violations: null,
    final_auto_resume_eligible: false,
    failed_source_key: resolvedFailedKey || null,
    failed_source: failedSource ? sourceWithKey(resolvedFailedKey, failedSource) : null,
    selected_source_key: null,
    selected_source: null,
    candidates: [],
    candidate_count: 0,
    patch: null,
    blocked_reason: null,
    required_next_step: null,
    no_robot_motion: true,
  };

  if (!resolvedFailedKey) {
    return {
      ...base,
      blocked_reason: "failed_source_key_required",
      required_next_step: "provide_failed_source_key_or_slot_well",
    };
  }
  if (!failedSource) {
    return {
      ...base,
      blocked_reason: "failed_source_not_in_source_map",
      required_next_step: "record_or_correct_liquid_source_map",
    };
  }
  if (failedSource.expected_presence !== true) {
    return {
      ...base,
      blocked_reason: "failed_source_not_expected_present",
      required_next_step: "inspect_protocol_source_or_source_map",
    };
  }
  if (!isSpecificLiquidIdentity(failedSource.liquid_name)) {
    return {
      ...base,
      blocked_reason: "failed_source_liquid_identity_not_specific",
      required_next_step: "record_specific_liquid_name_before_substitution",
    };
  }

  const candidates = findSameLiquidSourceCandidates({
    sources,
    failedKey: resolvedFailedKey,
    failedSource,
  });
  const preferred = preferredSourceKey ? normalizeUpper(preferredSourceKey) : null;
  const selected =
    (preferred && candidates.find(candidate => candidate.source_map_key === preferred)) ||
    candidates[0] ||
    null;
  const autoResumeEligible = Boolean(selected && selected.observed_presence === true);
  const autoResumeBlocker = autoResumeEligible
    ? null
    : "replacement_source_requires_live_presence_observation_before_auto_resume";

  if (!selected) {
    return {
      ...base,
      candidates,
      candidate_count: candidates.length,
      blocked_reason: "no_same_liquid_expected_present_alternative",
      required_next_step: "refill_failed_source_or_record_same_liquid_alternative",
    };
  }

  const patch = {
    recovery_type: "alternative_resource",
    resource_type: "liquid_source",
    playbook_id: LIQUID_SOURCE_SUBSTITUTION_PLAYBOOK_ID,
    failed_source_key: resolvedFailedKey,
    replacement_source_key: selected.source_map_key,
    liquid_name: failedSource.liquid_name,
    sample_id_policy: isGenericReagentLiquid(failedSource.liquid_name)
      ? "generic_reagent_sample_id_may_differ"
      : "sample_id_must_match_or_be_unspecified",
    source_map_revision: sessionState?.state_revision ?? null,
    executor: LIQUID_SOURCE_SUBSTITUTION_PLAYBOOK_ID,
  };

  const planned = applyFinalAutoResumeGates({
    ...base,
    status: "planned",
    ready_for_registered_executor: true,
    auto_resume_eligible: autoResumeEligible,
    auto_resume_blocker: autoResumeBlocker,
    selected_source_key: selected.source_map_key,
    selected_source: selected,
    candidates,
    candidate_count: candidates.length,
    patch,
    blocked_reason: autoResumeEligible
      ? "suffix_plan_not_sufficient"
      : "liquid_source_substitution_requires_validated_presence_before_auto_resume",
    required_next_step: "prepare_liquid_source_substitution_recovery",
  });
  return {
    ...planned,
    playbook: summarizeRecoveryPlaybook(LIQUID_SOURCE_SUBSTITUTION_PLAYBOOK_ID),
    semantic_invariants: validateLiquidSourceSubstitutionInvariants({ plan: planned }),
  };
}

export function renderLiquidSourceSubstitutionValidationProtocol({
  plan,
  pipetteName,
  mount,
  tiprackLoadName,
  tiprackSlot,
  apiLevel = "2.24",
  robotType = "Flex",
  tiprackNamespace = "opentrons",
  tiprackVersion = 1,
  labwareNamespace = "opentrons",
  labwareVersion = 1,
  liquidPresenceDetection = true,
  trashSlot = null,
} = {}) {
  if (plan?.status !== "planned" || !plan.selected_source) {
    throw new Error("Liquid source substitution validation protocol requires a planned substitution.");
  }
  if (!pipetteName || !mount || !tiprackLoadName || !tiprackSlot) {
    throw new Error("Liquid source substitution validation protocol requires pipette and tiprack details.");
  }

  const source = plan.selected_source;
  if (!source.labware_load_name || !source.slot_name || !source.well_name) {
    throw new Error("Liquid source substitution validation protocol requires selected source labware, slot, and well.");
  }

  const usedSlots = new Set([tiprackSlot, source.slot_name].filter(Boolean).map(slot => String(slot).toUpperCase()));
  const resolvedTrashSlot =
    trashSlot ||
    ["A3", "B3", "C3", "D3"].find(candidate => !usedSlots.has(candidate)) ||
    "A3";
  const validationPayload = {
    failed_source_key: plan.failed_source_key,
    replacement_source_key: plan.selected_source_key,
    liquid_name: plan.patch?.liquid_name || source.liquid_name || null,
    recovery_type: plan.patch?.recovery_type || "alternative_resource",
    resource_type: plan.patch?.resource_type || "liquid_source",
  };

  return [
    "from opentrons import protocol_api",
    "import json",
    "",
    'metadata = {"protocolName": "Liquid Source Substitution Validation", "author": "LabscriptAI OT"}',
    `requirements = {"robotType": ${pythonLiteral(robotType)}, "apiLevel": ${pythonLiteral(apiLevel)}}`,
    "",
    "def run(protocol: protocol_api.ProtocolContext) -> None:",
    `    protocol.load_trash_bin(${pythonLiteral(resolvedTrashSlot)})`,
    `    replacement_labware = protocol.load_labware(${pythonLiteral(source.labware_load_name)}, ${pythonLiteral(source.slot_name)}, namespace=${pythonLiteral(labwareNamespace)}, version=${labwareVersion})`,
    `    tiprack = protocol.load_labware(${pythonLiteral(tiprackLoadName)}, ${pythonLiteral(tiprackSlot)}, namespace=${pythonLiteral(tiprackNamespace)}, version=${tiprackVersion})`,
    "    pipette = protocol.load_instrument(",
    `        instrument_name=${pythonLiteral(pipetteName)},`,
    `        mount=${pythonLiteral(mount)},`,
    "        tip_racks=[tiprack],",
    `        liquid_presence_detection=${liquidPresenceDetection ? "True" : "False"},`,
    "    )",
    `    validation = ${pythonLiteral(validationPayload)}`,
    "    pipette.pick_up_tip()",
    "    try:",
    `        target_well = replacement_labware[${pythonLiteral(source.well_name)}]`,
    "        pipette.require_liquid_presence(target_well)",
    "        protocol.comment(",
    '            "LIQUID_SOURCE_SUBSTITUTION_VALIDATED:" + json.dumps(validation)',
    "        )",
    "    finally:",
    "        pipette.drop_tip()",
    "",
  ].join("\n");
}

export function generateLiquidSourceSubstitutionValidationProtocol({
  sessionState,
  failedSourceKey = null,
  failedSlotName = null,
  failedWellName = null,
  preferredSourceKey = null,
  pipetteName,
  mount,
  tiprackLoadName,
  tiprackSlot,
  outputPath = null,
  protocolOptions = {},
} = {}) {
  const plan = buildLiquidSourceSubstitutionPlan({
    sessionState,
    failedSourceKey,
    failedSlotName,
    failedWellName,
    preferredSourceKey,
  });
  if (plan.status !== "planned") {
    throw new Error(`Cannot generate liquid substitution validation protocol: ${plan.blocked_reason || "blocked"}.`);
  }

  const protocolSource = renderLiquidSourceSubstitutionValidationProtocol({
    plan,
    pipetteName,
    mount,
    tiprackLoadName,
    tiprackSlot,
    ...protocolOptions,
  });
  const resolvedOutputPath = outputPath ? path.resolve(outputPath) : null;
  if (resolvedOutputPath) {
    fs.mkdirSync(path.dirname(resolvedOutputPath), { recursive: true });
    fs.writeFileSync(resolvedOutputPath, protocolSource);
  }
  const liquidGuardAnalysis = analyzeLiquidProtocolGuards(protocolSource);
  const validationProtocol = {
    action: "require_liquid_presence",
    replacement_source_key: plan.selected_source_key,
    no_aspirate_or_dispense: liquidGuardAnalysis.no_aspirate_or_dispense,
    liquid_guard_analysis: liquidGuardAnalysis,
    no_robot_motion_until_run_protocol: true,
  };

  return {
    protocol_source: protocolSource,
    output_path: resolvedOutputPath,
    plan,
    validation_protocol: {
      ...validationProtocol,
      semantic_invariants: validateLiquidSourceSubstitutionInvariants({
        plan,
        validationProtocol,
      }),
    },
  };
}
