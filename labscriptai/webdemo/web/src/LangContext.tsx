import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { loadUiLang, saveUiLang, t as translate, type UiLang } from "./i18n";

interface LangApi {
  lang: UiLang;
  setLang: (next: UiLang) => void;
  t: (en: string) => string;
}

const LangContext = createContext<LangApi>({
  lang: "en",
  setLang: () => undefined,
  t: (en) => en,
});

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<UiLang>(() => loadUiLang());
  const api = useMemo<LangApi>(
    () => ({
      lang,
      setLang: (next) => {
        setLangState(next);
        saveUiLang(next);
      },
      t: (en) => translate(en, lang),
    }),
    [lang]
  );
  return <LangContext.Provider value={api}>{children}</LangContext.Provider>;
}

export function useLang(): LangApi {
  return useContext(LangContext);
}
