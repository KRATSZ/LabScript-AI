/**
 * Public ListTools surface for labscriptai chat.
 *
 * TOOL_DEFINITIONS stays the full catalog (P0: names ≡ Object.keys(TOOL_HANDLERS)).
 * ListTools filters at serve time so chat does not see ~77 authoring/vision/watch tools.
 */

export const PUBLIC_LIST_TOOL_NAMES = Object.freeze([
  "robot_status",
  "module_status",
  "run_history",
  "parse_error",
  "suggest_recovery_action",
  "runtime_get_outbox",
  "runtime_watch_poll",
  "execute_protocol_recovery",
  "run_protocol",
  "recover_liquid_source_substitution",
  "recover_tip_pickup",
  "simulate_protocol",
  "control_run",
  "probe_wells",
  "drop_attached_tip",
  "capture_preview_image",
  "run_pressure_trace",
  "fetch_pressure_trace",
  "analyze_pressure_trace",
  "live_readiness_check",
]);

export function listPublicTools(definitions = [], handlers = {}) {
  const byName = new Map(
    (Array.isArray(definitions) ? definitions : [])
      .filter(tool => tool && typeof tool.name === "string")
      .map(tool => [tool.name, tool]),
  );
  return PUBLIC_LIST_TOOL_NAMES.filter(name => {
    if (!byName.has(name)) {
      return false;
    }
    if (name === "live_readiness_check") {
      return typeof handlers?.[name] === "function";
    }
    return true;
  }).map(name => byName.get(name));
}
