import { protocolSummary } from "./protocolSummary";
import { useLang } from "./LangContext";
import type { SessionSnapshot } from "./types";

export function ProtocolSummaryCard({ session }: { session: SessionSnapshot | null }) {
  const { t } = useLang();
  const model = protocolSummary(session);
  if (!model) return null;
  return (
    <div className="protocol-summary" data-testid="protocol-summary">
      <div className="plan-heading">{t("Protocol summary")}</div>
      <p className="protocol-summary-approx" data-testid="protocol-summary-approx">
        {t("Approximate steps")}: {model.approx}
      </p>
      {model.pipettes.length ? (
        <p className="protocol-summary-line">
          {t("Pipettes")}: {model.pipettes.join(", ")}
        </p>
      ) : null}
      <div className="plan-heading">{t("Consumables")}</div>
      {model.consumables.length ? (
        <ul className="protocol-summary-list">
          {model.consumables.map((item) => (
            <li key={`${item.slot ?? ""}:${item.name}`}>
              <strong>{item.name}</strong>
              <span>
                {item.role}
                {item.slot ? ` · ${item.slot}` : ""}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="hint">{t("No consumables listed yet.")}</p>
      )}
    </div>
  );
}
