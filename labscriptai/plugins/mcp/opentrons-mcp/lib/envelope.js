export function asTextResponse(payload) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(payload, null, 2),
      },
    ],
  };
}

export function buildEnvelope({
  success = true,
  data = {},
  error = null,
  hardwareSnapshot = {},
  stateRevision = 0,
  runId = null,
  sessionId = null,
} = {}) {
  return {
    success,
    data,
    error,
    hardware_snapshot: hardwareSnapshot,
    state_revision: stateRevision,
    run_id: runId,
    session_id: sessionId,
    timestamp: new Date().toISOString(),
  };
}

export function successResponse(options = {}) {
  return asTextResponse(buildEnvelope({ success: true, ...options }));
}

export function errorResponse(tool, error, extra = {}) {
  return asTextResponse(
    buildEnvelope({
      success: false,
      data: extra.data || {},
      error: {
        tool,
        message: error instanceof Error ? error.message : String(error),
      },
      hardwareSnapshot: extra.hardwareSnapshot || {},
      stateRevision: extra.stateRevision ?? 0,
      runId: extra.runId ?? null,
      sessionId: extra.sessionId ?? null,
    }),
  );
}
