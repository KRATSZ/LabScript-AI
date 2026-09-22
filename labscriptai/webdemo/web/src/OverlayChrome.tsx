import type { ReactNode } from "react";
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
          <button className="ghost" type="button" onClick={onClose}>
            {t("Close")}
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
