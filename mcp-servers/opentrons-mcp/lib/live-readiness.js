import { buildErrorTaxonomy, mapRobotBlockerToLeaf } from "./error-taxonomy.js";

function uniqueOrdered(values = []) {
  const seen = new Set();
  const out = [];
  for (const value of values) {
    if (!value || seen.has(value)) {
      continue;
    }
    seen.add(value);
    out.push(value);
  }
  return out;
}

function buildReadinessCheck({
  name,
  status,
  summary,
  errorLeaf = null,
  evidenceSources = null,
  extra = {},
} = {}) {
  const taxonomy = errorLeaf
    ? buildErrorTaxonomy({
        phase: "live_readiness",
        errorLeaf,
        overrides: {
          auto_executable: false,
          evidence_sources: evidenceSources || ["health_check", "robot_status", "module_status"],
        },
      })
    : {
        phase: "live_readiness",
        error_domain: null,
        error_leaf: null,
        severity: status === "warn" ? "warning" : status,
        recoverability: null,
        requires_human_review: null,
        auto_executable: false,
        default_next_step: null,
        evidence_sources: evidenceSources || [],
      };

  return {
    name,
    status,
    summary,
    ...taxonomy,
    ...extra,
  };
}

function buildLocalRuntimeCheck(healthReport = {}) {
  if (healthReport?.venv?.status !== "ok") {
    return buildReadinessCheck({
      name: "local_runtime",
      status: "fail",
      summary: "Local Python runtime is missing or broken for simulation-first execution.",
      errorLeaf: "PYTHON_ENV_BROKEN",
      evidenceSources: ["health_check"],
      extra: {
        venv_status: healthReport?.venv?.status || "unknown",
      },
    });
  }

  if (healthReport?.venv?.opentrons === "not_installed") {
    return buildReadinessCheck({
      name: "local_runtime",
      status: "fail",
      summary: "Local Opentrons runtime is not installed; simulation gate cannot pass yet.",
      errorLeaf: "RUNTIME_UNAVAILABLE",
      evidenceSources: ["health_check"],
    });
  }

  return buildReadinessCheck({
    name: "local_runtime",
    status: "pass",
    summary: "Local runtime is ready for simulation-first gating.",
    evidenceSources: ["health_check"],
  });
}

function buildRobotConnectivityCheck(healthReport = {}) {
  if (healthReport?.robot?.status === "reachable") {
    return buildReadinessCheck({
      name: "robot_connectivity",
      status: "pass",
      summary: "Robot health endpoint is reachable.",
      evidenceSources: ["health_check"],
      extra: {
        robot_model: healthReport?.robot?.robot_model || null,
        robot_serial: healthReport?.robot?.robot_serial || null,
      },
    });
  }

  return buildReadinessCheck({
    name: "robot_connectivity",
    status: "fail",
    summary: "Robot health endpoint is unreachable.",
    errorLeaf: "ROBOT_UNREACHABLE",
    evidenceSources: ["health_check"],
    extra: {
      robot_status: healthReport?.robot?.status || "unknown",
      error: healthReport?.robot?.error || null,
    },
  });
}

function buildRestartStateCheck(restartReviewData = null) {
  if (!restartReviewData) {
    return null;
  }

  const sessionSummary = restartReviewData.session_summary || {};
  if (sessionSummary.needs_reconciliation) {
    return buildReadinessCheck({
      name: "session_state",
      status: "fail",
      summary: "Session requires reconciliation before further autonomous motion.",
      errorLeaf: "SESSION_NEEDS_RECONCILIATION",
      evidenceSources: ["session_state", "result_logs"],
      extra: {
        last_run_id: sessionSummary.last_run_id || null,
      },
    });
  }

  if (sessionSummary.last_run_id) {
    return buildReadinessCheck({
      name: "session_state",
      status: "warn",
      summary: "Session still points at a previous run; review run history before advancing.",
      errorLeaf: "STALE_LAST_RUN",
      evidenceSources: ["session_state", "result_logs"],
      extra: {
        last_run_id: sessionSummary.last_run_id,
      },
    });
  }

  return buildReadinessCheck({
    name: "session_state",
    status: "pass",
    summary: "Session state is clean and does not require restart reconciliation.",
    evidenceSources: ["session_state", "result_logs"],
  });
}

function buildRobotStatusCheck(robotStatusSnapshot = null) {
  if (!robotStatusSnapshot) {
    return null;
  }

  const blockers = robotStatusSnapshot.blockers || [];
  if (blockers.length === 0) {
    return buildReadinessCheck({
      name: "robot_status",
      status: "pass",
      summary: "Robot reports ready_for_physical_action.",
      evidenceSources: ["robot_status"],
    });
  }

  return buildReadinessCheck({
    name: "robot_status",
    status: "fail",
    summary: "Robot status includes blockers that prevent safe execution.",
    errorLeaf: mapRobotBlockerToLeaf(blockers[0]),
    evidenceSources: ["robot_status"],
    extra: {
      blockers,
    },
  });
}

function buildModuleStatusCheck(moduleStatusSnapshot = null) {
  if (!moduleStatusSnapshot) {
    return null;
  }

  const blockers = moduleStatusSnapshot.blockers || [];
  if (blockers.length === 0) {
    return buildReadinessCheck({
      name: "module_status",
      status: "pass",
      summary: "All observed modules report ready.",
      evidenceSources: ["module_status"],
    });
  }

  return buildReadinessCheck({
    name: "module_status",
    status: "warn",
    summary: "One or more modules are not ready yet.",
    errorLeaf: "MODULE_NOT_READY",
    evidenceSources: ["module_status"],
    extra: {
      blockers,
    },
  });
}

function buildHomeSafetyCheck(homeSafety = null) {
  if (!homeSafety) {
    return null;
  }

  if (homeSafety.auto_home_allowed) {
    return buildReadinessCheck({
      name: "home_safety",
      status: "pass",
      summary: "Home/cleanup path is currently safe.",
      evidenceSources: ["robot_status", "session_state"],
    });
  }

  let errorLeaf = "UNKNOWN_NEEDS_HUMAN";
  if ((homeSafety.blockers || []).includes("needs_reconciliation")) {
    errorLeaf = "SESSION_NEEDS_RECONCILIATION";
  } else if ((homeSafety.blockers || []).includes("door_open")) {
    errorLeaf = "DOOR_OPEN";
  } else if ((homeSafety.blockers || []).includes("estop_engaged")) {
    errorLeaf = "ESTOP_ENGAGED";
  }

  return buildReadinessCheck({
    name: "home_safety",
    status: "warn",
    summary: "Home/cleanup is not yet safe; resolve blockers before any motion that implies homing.",
    errorLeaf,
    evidenceSources: ["robot_status", "session_state"],
    extra: {
      blockers: homeSafety.blockers || [],
      minimum_cleanup_actions: homeSafety.minimum_cleanup_actions || [],
    },
  });
}

function buildPreflightGateCheck(preflight = null) {
  if (!preflight) {
    return null;
  }

  const blockingChecks = preflight.blocking_checks || [];
  const warningChecks = preflight.warning_checks || [];
  const primaryCheck = blockingChecks[0] || warningChecks[0] || null;
  const status = blockingChecks.length > 0 ? "fail" : warningChecks.length > 0 ? "warn" : "pass";
  return buildReadinessCheck({
    name: "preflight_gate",
    status,
    summary:
      preflight.summary ||
      (status === "pass"
        ? "Preflight passed."
        : status === "warn"
          ? "Preflight passed with warnings."
          : "Preflight blocked execution."),
    errorLeaf: primaryCheck?.error_leaf || null,
    evidenceSources: ["preflight_run_setup"],
    extra: {
      robot_model: preflight.robot_model || null,
      deck_model: preflight.deck_model || null,
      blocking_check_count: blockingChecks.length,
      warning_check_count: warningChecks.length,
    },
  });
}

function resolveRecommendedNextTools({
  checks,
  safeNextAction = null,
  hasFilePath = false,
} = {}) {
  const byName = Object.fromEntries(checks.map(check => [check.name, check]));

  if (byName.local_runtime?.status === "fail") {
    return ["doctor_local_runtime"];
  }
  if (byName.robot_connectivity?.status === "fail") {
    return ["robot_health"];
  }
  if (byName.session_state?.status === "fail" && safeNextAction) {
    return uniqueOrdered([
      "safe_next_action",
      safeNextAction.recommended_next_tool,
      ...(safeNextAction.tool_sequence || []).map(item => item.tool),
    ]);
  }
  if (byName.session_state?.status === "warn" && safeNextAction) {
    return uniqueOrdered([
      "safe_next_action",
      "run_history",
      "parse_error",
      ...(safeNextAction.tool_sequence || []).map(item => item.tool),
    ]);
  }
  if (byName.robot_status?.status === "fail") {
    return ["robot_status"];
  }
  if (byName.module_status?.status === "warn") {
    return ["module_status"];
  }
  if (byName.home_safety?.status === "warn") {
    return ["is_home_safe"];
  }
  if (byName.preflight_gate?.status === "fail") {
    return ["preflight_run_setup"];
  }
  return hasFilePath ? ["create_run"] : ["upload_protocol", "create_run"];
}

export function buildLiveReadinessReport({
  healthReport,
  restartReviewData = null,
  safeNextAction = null,
  robotStatusSnapshot = null,
  moduleStatusSnapshot = null,
  homeSafety = null,
  preflight = null,
  hasFilePath = false,
  extraChecks = [],
} = {}) {
  const checks = [
    buildLocalRuntimeCheck(healthReport),
    buildRobotConnectivityCheck(healthReport),
    buildRestartStateCheck(restartReviewData),
    buildRobotStatusCheck(robotStatusSnapshot),
    buildModuleStatusCheck(moduleStatusSnapshot),
    buildHomeSafetyCheck(homeSafety),
    buildPreflightGateCheck(preflight),
    ...extraChecks,
  ].filter(Boolean);

  const hasFail = checks.some(check => check.status === "fail");
  const hasWarn = checks.some(check => check.status === "warn");
  const overallStatus = hasFail ? "fail" : hasWarn ? "warn" : "pass";

  return {
    overall_status: overallStatus,
    ready_for_create_run: !hasFail,
    ready_for_play: !hasFail,
    checks,
    blocking_reasons: checks
      .filter(check => check.status === "fail")
      .map(check => ({
        name: check.name,
        summary: check.summary,
        error_leaf: check.error_leaf,
      })),
    recommended_next_tools: resolveRecommendedNextTools({
      checks,
      safeNextAction,
      hasFilePath,
    }),
    safe_next_action: safeNextAction,
    restart_review: restartReviewData,
    preflight,
  };
}
