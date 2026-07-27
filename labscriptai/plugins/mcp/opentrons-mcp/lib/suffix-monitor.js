import { validateVirtualLabStateSteps } from "./state.js";

export const hardStopViolationTypes = ["collision", "stall", "hard_stop"];

const SOURCE_KEY_FIELDS = ["source_key", "sourceKey", "source", "from"];

function normalizeContainerKey(key) {
  const trimmed = String(key || "").trim();
  if (!trimmed) {
    return null;
  }
  const [slot, well] = trimmed.split(".");
  return slot && well ? `${slot.toUpperCase()}.${well.toUpperCase()}` : trimmed.toUpperCase();
}

function stepReferencesSourceKey(step, normalizedFromKey) {
  for (const field of SOURCE_KEY_FIELDS) {
    const value = step?.[field];
    if (value === undefined || value === null) {
      continue;
    }
    if (typeof value === "string" && normalizeContainerKey(value) === normalizedFromKey) {
      return field;
    }
  }
  return null;
}

function patchStepSourceKey(step, normalizedFromKey, normalizedToKey) {
  const matchedField = stepReferencesSourceKey(step, normalizedFromKey);
  if (!matchedField) {
    return step;
  }
  return {
    ...step,
    [matchedField]: normalizedToKey,
  };
}

export function applyRecoveryPatchToSteps(steps, patch = {}) {
  const sourceSteps = Array.isArray(steps) ? steps : [];
  if (patch?.type !== "replace_source") {
    return sourceSteps.map(step => ({ ...step }));
  }

  const normalizedFromKey = normalizeContainerKey(patch.from_key || patch.fromKey);
  const normalizedToKey = normalizeContainerKey(patch.to_key || patch.toKey);
  if (!normalizedFromKey || !normalizedToKey) {
    return sourceSteps.map(step => ({ ...step }));
  }

  return sourceSteps.map(step => patchStepSourceKey(step, normalizedFromKey, normalizedToKey));
}

export function evaluateSuffixSufficiency({
  sessionState,
  steps,
  errorStepIndex,
  patch = null,
} = {}) {
  const allSteps = Array.isArray(steps) ? steps : [];
  const checkedFromIndex = Math.max(0, Number(errorStepIndex) || 0);
  const suffix = allSteps.slice(checkedFromIndex);
  const patchedSuffix = applyRecoveryPatchToSteps(suffix, patch);
  const validation = validateVirtualLabStateSteps(sessionState, patchedSuffix);
  const violations = validation.violations || [];
  const ok = violations.length === 0;

  return {
    ok,
    suffix_sufficient: ok,
    violations,
    patchedSuffix,
    checkedFromIndex,
    plan: {
      recovery_type: "alternative_resource",
      ...(patch && typeof patch === "object" ? patch : {}),
    },
  };
}
