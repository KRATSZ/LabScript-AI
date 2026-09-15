import type { AgentEvent } from "./types";

function detailText(event: AgentEvent): string {
  const detail = event.detail;
  if (!detail) return "";
  const bits: string[] = [];
  if (typeof detail.duration_ms === "number") bits.push(`${detail.duration_ms} ms`);
  if (detail.ok === true) bits.push("ok");
  if (detail.ok === false) bits.push("not ok");
  return bits.join(" · ");
}

export function TrajectoryPane({ events }: { events: AgentEvent[] }) {
  if (!events.length) {
    return (
      <p className="hint" data-testid="trajectory-empty">
        Append-only agent log. Turns, steps, and tool calls show here. Chat stays human-readable.
      </p>
    );
  }
  return (
    <ol className="trajectory" data-testid="trajectory-log">
      {events.map((event) => (
        <li key={event.seq} data-kind={event.kind} className="traj-row">
          <span className="traj-kind">{event.kind}</span>
          {event.name ? <span className="traj-name">{event.name}</span> : null}
          {detailText(event) ? <span className="traj-detail">{detailText(event)}</span> : null}
        </li>
      ))}
    </ol>
  );
}
