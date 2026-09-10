import { PIPELINE_HINTS, pipelineStates, pipelineSteps, preview } from "./pipelineLogic.ts";
import type { SessionSnapshot } from "./types";

interface Props {
  session: SessionSnapshot;
  runningTool: string | null;
  busy: boolean;
}

export function Pipeline({ session, runningTool, busy }: Props) {
  const steps = pipelineSteps(session.robot);
  const states = pipelineStates(session, runningTool);
  const hint = busy ? PIPELINE_HINTS[runningTool || ""] || "Working…" : "";
  return (
    <div className="pipeline-wrap">
      <div className="pipeline" aria-label="Progress">
        {steps.map((label, i) => (
          <div key={label} className="pipeline-step">
            {i > 0 ? <span className="pipeline-line" /> : null}
            <span className={`pipeline-dot ${states[i]}`} />
            <span>{label}</span>
          </div>
        ))}
      </div>
      {hint ? <p className="pipeline-hint">{hint}</p> : null}
      {session.sop.trim() ? (
        <details className="preview">
          <summary>SOP</summary>
          <pre>{preview(session.sop)}</pre>
        </details>
      ) : null}
      {session.code.trim() ? (
        <details className="preview">
          <summary>Script</summary>
          <pre>{preview(session.code)}</pre>
        </details>
      ) : null}
    </div>
  );
}
