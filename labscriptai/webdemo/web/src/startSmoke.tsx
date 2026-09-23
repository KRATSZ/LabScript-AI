import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { StartForm } from "./StartForm";
import { LanguageSwitch } from "./LanguageSwitch";
import { LangProvider, useLang } from "./LangContext";
import "./styles.css";

function StartSmoke() {
  const { t } = useLang();
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    const id = requestAnimationFrame(() => {
      const chips = document.querySelectorAll<HTMLButtonElement>(".chip");
      const pcr = [...chips].find((btn) => /PCR/i.test(btn.textContent || ""));
      (pcr || chips[0])?.click();
    });
    return () => cancelAnimationFrame(id);
  }, []);

  return (
    <div className="app" data-smoke="start" {...(submitted ? { "data-submitted": "1" } : {})}>
      <header className="workspace-header">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <h1>LabscriptAI</h1>
            <p>{t("On-screen preview only")}</p>
          </div>
        </div>
        <LanguageSwitch />
      </header>
      <div className="workspace start-mode" data-testid="shell">
        <section className="chat-column" data-testid="chat-column">
          <div className="start-scroll">
            <StartForm busy={false} onSubmit={() => setSubmitted(true)} />
          </div>
        </section>
      </div>
    </div>
  );
}

const root = document.getElementById("root");
if (!root) throw new Error("missing #root");
createRoot(root).render(
  <StrictMode>
    <LangProvider>
      <StartSmoke />
    </LangProvider>
  </StrictMode>
);
