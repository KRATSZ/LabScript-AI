import { useState } from "react";
import { EXAMPLES } from "./startExamples";

interface StartInput {
  goal: string;
  doc: string;
}

interface Props {
  busy: boolean;
  onSubmit: (input: StartInput) => void;
}

export function StartForm({ busy, onSubmit }: Props) {
  const [goal, setGoal] = useState("");
  const [doc, setDoc] = useState("");
  const [fileName, setFileName] = useState("");

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!goal.trim() || busy) return;
    onSubmit({ goal: goal.trim(), doc: doc.trim() });
  };

  const pickExample = (item: (typeof EXAMPLES)[number]) => {
    if (busy) return;
    setGoal(item.goal);
    setDoc(item.doc);
  };

  return (
    <form className="card form" onSubmit={submit}>
      <label htmlFor="goal">Experimental goal</label>
      <textarea
        id="goal"
        required
        rows={3}
        placeholder="e.g. Transfer 50 µL from well A1 to B1"
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
      />

      <label htmlFor="doc">Existing notes (optional)</label>
      <textarea
        id="doc"
        rows={3}
        placeholder="Paste a protocol draft, or leave blank"
        value={doc}
        onChange={(e) => setDoc(e.target.value)}
      />
      <div className="row">
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
        <span className="file">{fileName || "No file selected"}</span>
      </div>

      <p className="hint">Robot is asked in chat: OT-2 or Flex. Unsure? Click an example.</p>
      <div className="chips">
        {EXAMPLES.map((item) => (
          <button
            key={item.label}
            type="button"
            className="chip"
            disabled={busy}
            onClick={() => pickExample(item)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <button className="primary" type="submit" disabled={busy || !goal.trim()}>
        {busy ? "Starting…" : "Start"}
      </button>
    </form>
  );
}
