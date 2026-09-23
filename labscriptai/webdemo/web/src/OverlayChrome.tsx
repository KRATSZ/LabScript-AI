import type { ReactNode } from "react";
import { LanguageSwitch } from "./LanguageSwitch";
import { useLang } from "./LangContext";

export function OverlayChrome({
  onClose,
  children,
}: {
  onClose: () => void;
  children: ReactNode;
}) {
  const { t } = useLang();
  return (
    <div className="overlay">
      <div className="overlay-backdrop" onClick={onClose} />
      <div className="overlay-card">
        <div className="overlay-head">
          <strong>{t("Watch the protocol")}</strong>
          <div className="overlay-head-actions">
            <LanguageSwitch />
            <button className="ghost" type="button" onClick={onClose}>
              {t("Close")}
            </button>
          </div>
        </div>
        {children}
      </div>
    </div>
  );
}
