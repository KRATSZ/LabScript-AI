import { useLang } from "./LangContext";
import type { UiLang } from "./i18n";

export function LanguageSwitch() {
  const { lang, setLang, t } = useLang();
  const pick = (next: UiLang) => () => setLang(next);
  return (
    <div className="lang-switch" role="group" aria-label={t("Language")} data-testid="lang-switch">
      <button
        type="button"
        className={lang === "en" ? "lang-btn selected" : "lang-btn"}
        aria-pressed={lang === "en"}
        data-testid="lang-en"
        onClick={pick("en")}
      >
        EN
      </button>
      <button
        type="button"
        className={lang === "zh" ? "lang-btn selected" : "lang-btn"}
        aria-pressed={lang === "zh"}
        data-testid="lang-zh"
        onClick={pick("zh")}
      >
        中文
      </button>
    </div>
  );
}
