import {
  DOWNLOAD_LABELS,
  downloadHint,
  downloadable,
  downloadSuffix,
  downloadText,
  planStepLine,
  planSteps,
} from "./artifacts";
import { isPythonCodegen } from "./devices";
import { statusTone } from "./pipelineLogic";
import type { SessionSnapshot } from "./types";

function downloadFor(session: SessionSnapshot, kind: ReturnType<typeof downloadable>[number]): void {
  if (kind === "sop") downloadText("sop.md", session.sop, "text/markdown");
  else if (kind === "python") downloadText("protocol.py", session.code, "text/x-python");
  else if (kind === "gwl") downloadText("worklist.gwl", session.artifacts?.worklistGwl ?? "", "text/plain");
  else if (kind === "plr") downloadText("vantage.py", session.artifacts?.hamiltonScript ?? "", "text/x-python");
  else downloadText("plan.json", JSON.stringify(session.plan, null, 2), "application/json");
}

export function ExportsPanel({ session }: { session: SessionSnapshot }) {
  const files = downloadable(session);
  const showPlanTable = !isPythonCodegen(session.robot) || !session.code?.trim();
  const steps = showPlanTable ? planSteps(session.plan) : [];
  const marker = downloadSuffix(session.checks?.status);
  const tone = statusTone(session.checks?.status);

  if (!files.length && !steps.length) return null;

  return (
    <div className="artifacts">
      {files.length ? (
        <div className="exports">
          {files.map((kind) => (
            <div key={kind} className="export-item">
              <button
                type="button"
                className="export-btn"
                onClick={() => downloadFor(session, kind)}
              >
                {DOWNLOAD_LABELS[kind]}
                {marker ? <span className={tone ? `status-${tone}` : undefined}>{marker}</span> : null}
              </button>
              <p className="export-hint">{downloadHint(kind, session.robot)}</p>
            </div>
          ))}
        </div>
      ) : null}
      {steps.length ? (
        <div className="plan-block">
          <div className="plan-heading">Plan IR (step list)</div>
          <div className="plan-steps">
            {steps.slice(0, 20).map((step, index) => (
              <p key={index} className="file">
                {planStepLine(step)}
              </p>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
