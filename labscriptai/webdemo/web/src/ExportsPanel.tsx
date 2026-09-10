import { isPlayableAnalyze } from "./analysis";
import { downloadable, downloadText, planStepLine, planSteps } from "./artifacts";
import type { SessionSnapshot } from "./types";

const DOWNLOAD_LABELS: Record<ReturnType<typeof downloadable>[number], string> = {
  sop: "SOP",
  python: "Python",
  plan: "Plan",
};

function downloadFor(session: SessionSnapshot, kind: ReturnType<typeof downloadable>[number]): void {
  if (kind === "sop") downloadText("sop.md", session.sop, "text/markdown");
  else if (kind === "python") downloadText("protocol.py", session.code, "text/x-python");
  else downloadText("plan.json", JSON.stringify(session.plan, null, 2), "application/json");
}

export function ExportsPanel({ session }: { session: SessionSnapshot }) {
  const files = downloadable(session);
  const steps = planSteps(session.plan);
  const showWatchNote = Boolean(session.plan) && !isPlayableAnalyze(session.analyze);

  if (!files.length && !steps.length && !showWatchNote) return null;

  return (
    <div className="artifacts">
      {files.length ? (
        <div className="exports">
          {files.map((kind) => (
            <button key={kind} type="button" className="export-btn" onClick={() => downloadFor(session, kind)}>
              {DOWNLOAD_LABELS[kind]}
            </button>
          ))}
        </div>
      ) : null}
      {steps.length ? (
        <div className="plan-block">
          <div className="plan-heading">Plan</div>
          <div className="plan-steps">
            {steps.slice(0, 20).map((step, index) => (
              <p key={index} className="file">
                {planStepLine(step)}
              </p>
            ))}
          </div>
        </div>
      ) : null}
      {showWatchNote ? <p className="file">Watch is Opentrons-only.</p> : null}
    </div>
  );
}
