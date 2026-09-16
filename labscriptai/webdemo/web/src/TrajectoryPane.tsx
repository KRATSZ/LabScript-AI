import type { AgentEvent } from "./types";
import {
  activityStatusWord,
  activitySteps,
  activitySummary,
  formatDuration,
} from "./trajectoryLogic";

export { eventClock, eventDetailText } from "./trajectoryLogic";

interface Props {
  events: AgentEvent[];
  runningTool?: string | null;
}

export function TrajectoryPane({ events, runningTool = null }: Props) {
  const steps = activitySteps(events, runningTool);
  if (!steps.length) {
    return (
      <div className="stage-empty" data-testid="trajectory-empty">
        <h2>Activity</h2>
        <p>Each confirm, write-up, and bench check lands here.</p>
      </div>
    );
  }
  const turns = [...new Set(steps.map((step) => step.turn))];
  return (
    <div className="activity-pane" data-testid="trajectory-log">
      <div className="activity-head">
        <h2>Activity</h2>
        <p>{activitySummary(steps)}</p>
      </div>
      <ol className="activity-timeline">
        {turns.map((turn) => {
          const rows = steps.filter((step) => step.turn === turn);
          return (
            <li key={turn} className="activity-turn">
              {turns.length > 1 ? <h3>{turn === 1 ? "Start" : "After you replied"}</h3> : null}
              <ol className="activity-list">
                {rows.map((step) => {
                  const time = step.status === "run" ? "" : formatDuration(step.durationMs);
                  const status = step.status === "ok" ? "" : activityStatusWord(step.status);
                  return (
                    <li
                      key={step.key}
                      className={`activity-row ${step.status}`}
                      data-kind={step.name}
                      aria-label={`${step.label}, ${activityStatusWord(step.status)}`}
                    >
                      <span className={`activity-dot ${step.status}`} aria-hidden />
                      <span className="activity-label">{step.label}</span>
                      {status || time ? (
                        <span className="activity-meta">
                          {status ? (
                            <span className={`activity-status status-${step.status}`}>{status}</span>
                          ) : null}
                          {time ? <span className="activity-time">{time}</span> : null}
                        </span>
                      ) : null}
                    </li>
                  );
                })}
              </ol>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
