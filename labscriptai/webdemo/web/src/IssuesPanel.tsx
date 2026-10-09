import { ChecksAudit } from "./ChecksAudit";
import { statusTone, statusWord, verdictLabel } from "./pipelineLogic";
import { useLang } from "./LangContext";
import type { ChecksResult, SessionSnapshot } from "./types";

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

export function IssuesPanel({
  checks,
  session = null,
}: {
  checks: ChecksResult | null;
  session?: SessionSnapshot | null;
}) {
  const { t } = useLang();
  if (!checks) return null;
  const tone = statusTone(checks.status);
  const word = verdictLabel(checks.status, checks) || statusWord(checks.status);
  const consequences =
    Array.isArray(checks.consequences) && checks.consequences.length
      ? checks.consequences.slice(0, 5)
      : fallbackLines(checks);
  return (
    <div>
      <div className={`issues-human${tone ? ` ${tone}` : ""}`}>
        <p className="status-word" data-testid="check-verdict">{t(word)}</p>
        {consequences.map((line, index) => (
          <p key={index}>{line}</p>
        ))}
      </div>
      <ChecksAudit session={session} checks={checks} />
      <details className="issues">
        <summary>{t("Lab-check details")}</summary>
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
