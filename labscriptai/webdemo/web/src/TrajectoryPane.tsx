import type { AgentEvent } from "./types";
import {
  THINK_STEP,
  activityStatusWord,
  activitySteps,
  activitySummary,
  formatDuration,
  type ActivityLive,
} from "./trajectoryLogic";

export { eventClock, eventDetailText } from "./trajectoryLogic";

interface Props {
  events: AgentEvent[];
  runningTool?: string | null;
  live?: ActivityLive;
}

export function TrajectoryPane({ events, runningTool = null, live = {} }: Props) {
  const steps = activitySteps(events, runningTool, live);
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
                  const status = activityStatusWord(step.status);
                  const think = step.name === THINK_STEP;
                  return (
                    <li
                      key={step.key}
                      className={`activity-row ${step.status}${think ? " think" : ""}`}
                      data-kind={step.name}
                      aria-label={`${step.label}, ${status}`}
                    >
                      <span
                        className={`activity-dot ${step.status}${think ? " think" : ""}`}
                        aria-hidden
                      />
                      <span className="activity-copy">
                        <span className="activity-label">{step.label}</span>
                        {step.note ? <span className="activity-note">{step.note}</span> : null}
                      </span>
                      <span className="activity-meta">
                        <span className={`activity-status status-${step.status}`}>{status}</span>
                        {time ? <span className="activity-time">{time}</span> : null}
                      </span>
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
