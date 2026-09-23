import { useRef, useState } from "react";
import { DEVICE_CARDS, canStart, goalHasProtocolIntent, matchDeviceFromText } from "./devices";
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
  onCancel?: () => void;
}

export function StartForm({ busy, onSubmit, onCancel }: Props) {
  const { t, lang } = useLang();
  const fileRef = useRef<HTMLInputElement>(null);
  const [goal, setGoal] = useState("");
  const [doc, setDoc] = useState("");
  const [fileName, setFileName] = useState("");
  const [deviceId, setDeviceId] = useState<string | undefined>();

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!canStart(goal, deviceId) || busy) return;
    const card = DEVICE_CARDS.find((item) => item.id === deviceId);
    if (!card) return;
    onSubmit({ goal: goal.trim(), doc: doc.trim(), robot: card.legacyRobot });
  };

  const pickExample = (item: (typeof EXAMPLES)[number]) => {
    if (busy) return;
    const nextGoal = lang === "zh" ? item.goalZh : item.goal;
    const nextDoc = lang === "zh" ? item.docZh : item.doc;
    setGoal(nextGoal);
    setDoc(nextDoc);
    const hit = matchDeviceFromText(`${item.label}\n${item.goal}\n${item.doc}`);
    if (hit) setDeviceId(hit);
  };

  return (
    <form className="card form" onSubmit={submit}>
      <label>{t("Which robot?")}</label>
      <p className="hint">{t("Pick a robot.")}</p>
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
              {t(card.label)}
            </strong>
            <span className="device-blurb">{t(card.blurb)}</span>
          </button>
        ))}
      </div>

      <label htmlFor="goal">{t("What should we run?")}</label>
      <textarea
        id="goal"
        required
        rows={2}
        placeholder={t("e.g. Transfer 50 µL from well A1 to B1")}
        value={goal}
        disabled={busy}
        onChange={(e) => setGoal(e.target.value)}
      />
      {goal.trim() && !goalHasProtocolIntent(goal) ? (
        <p className="hint" data-testid="goal-intent-hint">
          {t("Name a transfer, a volume, or wells — for example Transfer 50 µL from A1 to B1.")}
        </p>
      ) : null}

      <label htmlFor="doc">{t("Notes (optional)")}</label>
      <p className="hint" data-testid="notes-file-hint">
        {t("Notes are .md, .txt, .py, or .json. They are notes, not the run.")}
      </p>
      <div className="file-pick">
        <button
          type="button"
          className="file-btn"
          data-testid="notes-file"
          aria-label={t("Choose file")}
          disabled={busy}
          onClick={() => fileRef.current?.click()}
        >
          {fileName || t("Choose file")}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".md,.txt,.py,.json"
          className="file-input-native"
          tabIndex={-1}
          aria-hidden="true"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            setFileName(file.name);
            setDoc(await file.text());
          }}
        />
      </div>
      <textarea
        id="doc"
        rows={2}
        placeholder={t("Paste a draft, or leave blank")}
        value={doc}
        disabled={busy}
        onChange={(e) => setDoc(e.target.value)}
      />

      <div className="chips">
        {EXAMPLES.map((item) => (
          <button
            key={item.label}
            type="button"
            className="chip"
            disabled={busy}
            onClick={() => pickExample(item)}
          >
            {t(item.label)}
          </button>
        ))}
      </div>

      <button className="primary" type="submit" disabled={busy || !canStart(goal, deviceId)}>
        {busy ? t("Starting…") : t("Let’s go")}
      </button>
      {busy && onCancel ? (
        <button type="button" className="file-btn cancel-turn" data-testid="cancel-turn" onClick={onCancel}>
          {t("Cancel")}
        </button>
      ) : null}
    </form>
  );
}
