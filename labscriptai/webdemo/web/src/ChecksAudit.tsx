import { checksAudit } from "./auditModel";
import { useLang } from "./LangContext";
import type { ChecksResult, SessionSnapshot } from "./types";

export function ChecksAudit({
  session,
  checks,
}: {
  session?: SessionSnapshot | null;
  checks?: ChecksResult | null;
}) {
  const { t } = useLang();
  const model = checksAudit(checks ?? session?.checks, session);
  if (!model) return null;
  return (
    <div className="checks-audit" data-testid="checks-audit">
      <div className="plan-heading">{t("Checks that ran")}</div>
      <ul className="checks-audit-list">
        {model.checks.map((row) => (
          <li key={row.key} data-tone={row.tone}>
            <strong>{t(row.label)}</strong>
            <span>{t(row.result)}</span>
          </li>
        ))}
      </ul>
      <div className="plan-heading">{t("Assumptions")}</div>
      <ul className="checks-audit-list">
        {model.assumptions.map((line) => (
          <li key={line}>{t(line)}</li>
        ))}
      </ul>
      <div className="plan-heading">{t("Not verified")}</div>
      <ul className="checks-audit-list">
        {model.unverified.map((line) => (
          <li key={line}>{t(line)}</li>
        ))}
      </ul>
    </div>
  );
}
