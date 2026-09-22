import { protocolSummary, type ProtocolSummaryModel } from "./protocolSummary";
import { useLang } from "./LangContext";
import type { SessionSnapshot } from "./types";

function approxText(model: ProtocolSummaryModel, t: (en: string) => string): string {
  if (model.actionCount > 0) {
    const unit = model.actionCount === 1 ? t("liquid-handling step") : t("liquid-handling steps");
    return `~${model.actionCount} ${unit}`;
  }
  if (model.stepCount > 0) {
    const unit = model.stepCount === 1 ? t("step") : t("steps");
    return `~${model.stepCount} ${unit}`;
  }
  return t("Steps not listed yet");
}

export function ProtocolSummaryCard({ session }: { session: SessionSnapshot | null }) {
  const { t } = useLang();
  const model = protocolSummary(session);
  if (!model) return null;
  return (
    <div className="protocol-summary" data-testid="protocol-summary">
      <div className="plan-heading">{t("Protocol summary")}</div>
      <p className="protocol-summary-approx" data-testid="protocol-summary-approx">
        {t("Approximate steps")}: {approxText(model, t)}
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
              <strong>{t(item.name)}</strong>
              <span>
                {t(item.role)}
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
