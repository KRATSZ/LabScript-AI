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
      {turns.map((turn) => {
        const rows = steps.filter((step) => step.turn === turn);
        return (
          <section key={turn} className="activity-turn">
            <h3>Reply {turn}</h3>
            <ol className="activity-list">
              {rows.map((step) => (
                <li key={step.key} className={`activity-row ${step.status}`} data-kind={step.name}>
                  <span className={`activity-dot ${step.status}`} />
                  <span className="activity-label">{step.label}</span>
                  <span className={`activity-status status-${step.status}`}>{activityStatusWord(step.status)}</span>
                  <span className="activity-time">{step.status === "run" ? "" : formatDuration(step.durationMs)}</span>
                </li>
              ))}
            </ol>
          </section>
        );
      })}
    </div>
  );
}
