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
  const { t, lang } = useLang();
  const model = checksAudit(checks ?? session?.checks, session);
  if (!model) return null;
  const show = (line: string) => {
    const fill = line.match(/^Checked using the (\S+) µL you confirmed in ([A-H]\d+)$/);
    if (fill && lang === "zh") return `按你确认的 ${fill[2]} = ${fill[1]} µL 检查`;
    const ruled = line.match(/^The draft still lists the reservoir you ruled out\.$/);
    if (ruled && lang === "zh") return "方案仍列出你已去掉的储液槽。";
    const short = line.match(
      /^You confirmed ([A-H]\d+) holds only (\S+) µL, but this transfer aspirates (\S+) µL\.$/
    );
    if (short && lang === "zh") return `你确认 ${short[1]} 只有 ${short[2]} µL，这次要吸 ${short[3]} µL。`;
    const missed = line.match(/^Checks did not use the (\S+) µL you confirmed in ([A-H]\d+)\.$/);
    if (missed && lang === "zh") return `校验没有使用你确认的 ${missed[2]} = ${missed[1]} µL。`;
    return t(line);
  };
  return (
    <div className="checks-audit" data-testid="checks-audit">
      <div className="plan-heading">{t("Checks that ran")}</div>
      <ul className="checks-audit-list">
        {model.checks.map((row) => (
          <li key={row.key} data-tone={row.tone}>
            <strong>{t(row.label)}</strong>
            <span>{show(row.result)}</span>
          </li>
        ))}
      </ul>
      <div className="plan-heading">{t("Assumptions")}</div>
      <ul className="checks-audit-list">
        {model.assumptions.map((line) => (
          <li key={line}>{show(line)}</li>
        ))}
      </ul>
      <div className="plan-heading">{t("Not verified")}</div>
      <ul className="checks-audit-list">
        {model.unverified.map((line) => (
          <li key={line}>{show(line)}</li>
        ))}
      </ul>
    </div>
  );
}
