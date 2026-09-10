import type { ChecksResult } from "./types";

function issueText(item: unknown): string {
  if (typeof item === "string") return item;
  if (item && typeof item === "object") {
    const rec = item as Record<string, unknown>;
    const bits = [rec.code, rec.detail_text, rec.hint, rec.claim, rec.suggestion].filter(
      (part) => typeof part === "string" && part.trim()
    );
    if (bits.length) return bits.join(" — ");
  }
  return String(item);
}

function simLine(checks: ChecksResult): string {
  if (checks.sim.reason === "plr_unavailable") {
    return "Simulation unavailable — PyLabRobot is not installed (this is not a pass)";
  }
  if (checks.sim.ok) return "Simulation passed";
  return `Simulation failed${checks.sim.reason ? ` (${checks.sim.reason})` : ""}`;
}

function humanReason(reason?: string): string {
  if (!reason || reason === "plr_unavailable") return "";
  return ` (${reason})`;
}

function logicLine(checks: ChecksResult): string {
  const lp = checks.logicpass;
  if (lp.outcome === "pass") return "Logic check passed";
  if (lp.outcome === "skipped") return `Logic check skipped${humanReason(lp.reason)}`;
  if (lp.outcome === "fail") return `Logic check failed${humanReason(lp.reason)}`;
  return `Logic check failed${humanReason(lp.reason)}`;
}

function reviewLine(checks: ChecksResult): string {
  const review = checks.llmreview;
  if (!review) return "Review not run";
  if (review.match === true) return "Review matches goal";
  if (review.match === false) return "Review does not match";
  return "Review not run";
}

export function IssuesPanel({ checks }: { checks: ChecksResult | null }) {
  if (!checks) return null;
  const issues = Array.isArray(checks.logicpass.issues) ? checks.logicpass.issues : [];
  const findings = Array.isArray(checks.llmreview?.findings) ? checks.llmreview.findings : [];
  const state = checks.statepass;
  return (
    <div>
      <div className="issues-human">
        <p>{simLine(checks)}</p>
        <p>{logicLine(checks)}</p>
        <p>{reviewLine(checks)}</p>
        {findings.length
          ? findings.slice(0, 4).map((item, index) => <p key={index}>{issueText(item)}</p>)
          : null}
        {issues.length
          ? issues.slice(0, 4).map((item, index) => <p key={`lp-${index}`}>{issueText(item)}</p>)
          : null}
      </div>
      <details className="issues">
        <summary>Developer details</summary>
        <pre>
          {JSON.stringify(
            {
              sim: checks.sim,
              logicpass: checks.logicpass,
              llmreview: checks.llmreview ?? null,
              statepass: state,
            },
            null,
            2
          )}
        </pre>
      </details>
    </div>
  );
}
