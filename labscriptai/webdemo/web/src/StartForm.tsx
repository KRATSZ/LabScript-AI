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

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!canStart(goal, deviceId) || busy) return;
    const card = DEVICE_CARDS.find((item) => item.id === deviceId);
    if (!card) return;
    onSubmit({ goal: goal.trim(), doc: doc.trim(), robot: card.legacyRobot });
  };

  const pickExample = (item: (typeof EXAMPLES)[number]) => {
    if (busy) return;
    setGoal(item.goal);
    setDoc(item.doc);
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
              {card.label}
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
        onChange={(e) => setGoal(e.target.value)}
      />

      <label htmlFor="doc" className="notes-head">
        <span>{t("Notes (optional)")}</span>
        <span className="file-label">
          <input
            type="file"
            accept=".md,.txt,.py,.json"
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              setFileName(file.name);
              setDoc(await file.text());
            }}
          />
          {fileName || t("Choose file")}
        </span>
      </label>
      <textarea
        id="doc"
        rows={2}
        placeholder={t("Paste a draft, or leave blank")}
        value={doc}
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
    </form>
  );
}
