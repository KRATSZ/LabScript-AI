import type { AgentEvent } from "./types";
import { eventClock, eventDetailText } from "./trajectoryLogic";

export { eventClock, eventDetailText };

export function TrajectoryPane({ events }: { events: AgentEvent[] }) {
  if (!events.length) {
    return (
      <p className="hint" data-testid="trajectory-empty">
        Quiet log of what happened.
      </p>
    );
  }
  return (
    <ol className="trajectory" data-testid="trajectory-log">
      {events.map((event) => (
        <li key={`${event.seq}-${event.kind}`} data-kind={event.kind} className="traj-row">
          {eventClock(event.t) ? <span className="traj-time">{eventClock(event.t)}</span> : null}
          <span className="traj-kind">{event.kind}</span>
          {event.name ? <span className="traj-name">{event.name}</span> : null}
          {eventDetailText(event) ? <span className="traj-detail">{eventDetailText(event)}</span> : null}
        </li>
      ))}
    </ol>
  );
}
