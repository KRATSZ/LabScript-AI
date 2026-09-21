import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { StartForm } from "./StartForm";
import { LangProvider } from "./LangContext";
import "./styles.css";

function StartSmoke() {
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    const id = requestAnimationFrame(() => {
      document.querySelector<HTMLButtonElement>(".chip")?.click();
    });
    return () => cancelAnimationFrame(id);
  }, []);

  return (
    <div className="shell" data-smoke="start" {...(submitted ? { "data-submitted": "1" } : {})}>
      <StartForm busy={false} onSubmit={() => setSubmitted(true)} />
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
