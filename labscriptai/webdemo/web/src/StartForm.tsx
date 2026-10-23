import { useState } from "react";
import { DEVICE_CARDS, canStart, matchDeviceFromText } from "./devices";
import { EXAMPLES } from "./startExamples";
import { useLang } from "./LangContext";
import type { StartInput } from "./types";

const TILE_MARK: Record<string, string> = {
  ot2: "🧪",
  flex: "🧬",
  hamilton_star: "🔬",
  hamilton_vantage: "⚗️",
  tecan_fluent: "💧",
};

interface Props {
  busy: boolean;
  onSubmit: (input: StartInput) => void;
}

export function StartForm({ busy, onSubmit }: Props) {
  const { t } = useLang();
  const [goal, setGoal] = useState("");
  const [doc, setDoc] = useState("");
  const [fileName, setFileName] = useState("");
  const [deviceId, setDeviceId] = useState<string | undefined>();
  const [fileError, setFileError] = useState("");
  const [readingFile, setReadingFile] = useState(false);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!canStart(goal, deviceId) || busy || readingFile) return;
    const card = DEVICE_CARDS.find((item) => item.id === deviceId);
    if (!card) return;
    onSubmit({ goal: goal.trim(), doc: doc.trim(), robot: card.legacyRobot });
  };

  const pickExample = (item: (typeof EXAMPLES)[number]) => {
    if (busy) return;
    setGoal(t(item.goal));
    setDoc(t(item.doc));
    setFileName("");
    setFileError("");
    const hit = matchDeviceFromText(`${item.label}\n${item.goal}\n${item.doc}`);
    setDeviceId(hit ?? deviceId ?? item.deviceId);
  };

  return (
    <form className="card form" onSubmit={submit} aria-busy={busy || readingFile}>
      <div className="start-fields">
      <div className="start-intro">
        <h2>{t("Create a robot protocol")}</h2>
        <p>{t("Describe your experiment. Review the plan in chat, then generate and check your script.")}</p>
      </div>
      <div className="start-examples">
        <span className="field-title">{t("Try an example")}</span>
        <div className="chips">
          {EXAMPLES.map((item) => (
            <button key={item.label} type="button" className="chip" disabled={busy || readingFile} onClick={() => pickExample(item)}>
              {t(item.label)}
            </button>
          ))}
        </div>
        <p className="hint">{t("Examples use Flex unless you choose another instrument.")}</p>
      </div>

      <fieldset className="device-fieldset" disabled={busy || readingFile}>
        <legend>{t("1. Choose your instrument")}</legend>
        <div className="device-grid">
        {DEVICE_CARDS.map((card) => (
          <button
            key={card.id}
            type="button"
            className={deviceId === card.id ? "device-card selected" : "device-card"}
            aria-pressed={deviceId === card.id}
            data-device={card.id}
            disabled={busy}
            onClick={() => setDeviceId(card.id)}
          >
            <strong>
              <span className="device-emoji" aria-hidden="true">
                {TILE_MARK[card.id] ?? ""}
              </span>
              {card.label}
            </strong>
            <span className="device-blurb">{t(card.blurb)}</span>
          </button>
        ))}
        </div>
      </fieldset>

      <label htmlFor="goal">{t("2. Describe the experiment")}</label>
      <textarea
        id="goal"
        required
        rows={3}
        disabled={busy || readingFile}
        aria-describedby="goal-hint"
        placeholder={t("e.g. Transfer 50 µL from well A1 to B1")}
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
      />
      <p className="hint" id="goal-hint">{t("Include volumes, reagents, and source and destination wells.")}</p>

      <div className="notes-head">
        <label htmlFor="doc">{t("SOP or existing code (optional)")}</label>
        <label className="file-label" htmlFor="protocol-file">
          <input
            id="protocol-file"
            type="file"
            accept=".md,.txt,.py,.json"
            disabled={busy || readingFile}
            aria-describedby="file-hint"
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const input = e.currentTarget;
              setReadingFile(true);
              setFileError("");
              try {
                const text = await file.text();
                setDoc(text);
                setFileName(file.name);
              } catch {
                setFileError("Could not read that file. Paste its contents below or try another file.");
              } finally {
                setReadingFile(false);
                input.value = "";
              }
            }}
          />
          {t(readingFile ? "Reading file…" : "Attach a file")}
        </label>
      </div>
      <textarea
        id="doc"
        rows={2}
        placeholder={t("Paste your SOP, experimental steps, or robot code here.")}
        disabled={busy || readingFile}
        aria-describedby="file-hint"
        value={doc}
        onChange={(e) => setDoc(e.target.value)}
      />
      <p className="hint" id="file-hint">{fileName || t("Text files: .txt, .md, .py, .json")}</p>
      {fileError ? <p className="file error-note" role="alert">{t(fileError)}</p> : null}
      </div>
      <div className="start-actions">
      <p className="hint start-requirements" id="start-requirements" aria-live="polite">
        {t(!deviceId ? "Choose an instrument or try an example to begin." : !goal.trim() ? "Add an experiment description to continue." : "You can review and change the plan before code is generated.")}
      </p>
      <button className="primary" type="submit" aria-describedby="start-requirements" disabled={busy || readingFile || !canStart(goal, deviceId)}>
        {busy ? t("Starting…") : t("Create protocol")}
      </button>
      </div>
    </form>
  );
}
