export const TERMINAL_RUN_STATUSES = new Set([
  "succeeded",
  "failed",
  "stopped",
  "awaiting-recovery",
  "blocked-by-open-door",
]);

export function normalizeRunStatus(status) {
  return String(status || "").trim().toLowerCase();
}

export function isTerminalRunStatus(status) {
  return TERMINAL_RUN_STATUSES.has(normalizeRunStatus(status));
}

export function shouldAttachRecoveryGuidance(status) {
  return ["failed", "awaiting-recovery"].includes(normalizeRunStatus(status));
}

export function buildRunProtocolResult({
  protocol,
  created_run,
  play_action = null,
  final_run_history,
  simulation_gate = null,
  preflight_gate = null,
  parsed_error = null,
  recovery = null,
} = {}) {
  const finalStatus = final_run_history?.status || null;
  const normalizedStatus = normalizeRunStatus(finalStatus);
  return {
    simulation_gate,
    preflight_gate,
    protocol,
    created_run,
    play_action,
    final_run_history,
    final_status: finalStatus,
    requires_attention: ["failed", "awaiting-recovery", "blocked-by-open-door"].includes(
      normalizedStatus,
    ),
    parsed_error,
    recovery,
  };
}
