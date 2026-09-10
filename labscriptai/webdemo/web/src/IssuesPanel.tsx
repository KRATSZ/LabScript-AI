import { statusTone, statusWord } from "./pipelineLogic";
import type { ChecksResult } from "./types";

function issueText(item: unknown): string {
  if (typeof item === "string") return item;
  if (item && typeof item === "object") {
    const rec = item as Record<string, unknown>;
    const bits = [rec.detail_text, rec.hint, rec.claim, rec.suggestion].filter(
      (part) => typeof part === "string" && part.trim()
    );
    if (bits.length) return bits.join(" — ");
  }
  return String(item);
}

function fallbackLines(checks: ChecksResult): string[] {
  const findings = Array.isArray(checks.llmreview?.findings) ? checks.llmreview.findings : [];
  const issues = Array.isArray(checks.logicpass.issues) ? checks.logicpass.issues : [];
  return [...findings, ...issues].map(issueText).filter(Boolean).slice(0, 5);
}

export function IssuesPanel({ checks }: { checks: ChecksResult | null }) {
  if (!checks) return null;
  const tone = statusTone(checks.status);
  const consequences =
    Array.isArray(checks.consequences) && checks.consequences.length
      ? checks.consequences.slice(0, 5)
      : fallbackLines(checks);
  return (
    <div>
      <div className={`issues-human${tone ? ` ${tone}` : ""}`}>
        <p className="status-word">{statusWord(checks.status)}</p>
        {consequences.map((line, index) => (
          <p key={index}>{line}</p>
        ))}
      </div>
      <details className="issues">
        <summary>Developer details</summary>
        <pre>
          {JSON.stringify(
            {
              status: checks.status,
              sim: checks.sim,
              logicpass: checks.logicpass,
              llmreview: checks.llmreview ?? null,
              compile: checks.compile ?? null,
              statepass: checks.statepass,
            },
            null,
            2
          )}
        </pre>
      </details>
    </div>
  );
}
