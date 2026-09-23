import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { LangProvider } from "./LangContext";
import { RightStage } from "./RightStage";
import { saveUiLang } from "./i18n";
import "./styles.css";
import type { AgentEvent, SessionSnapshot } from "./types";

saveUiLang("zh");

const session: SessionSnapshot = {
  id: "stage-wait-smoke",
  phase: "intake",
  missing: [],
  goal: "Prepare a PCR mix: dispense 20 µL of master mix into 8 sample wells.",
  doc: "",
  robot: "OT-2",
  hardware: {
    leftPipette: "p300_single_gen2",
    rightPipette: "None",
    deck: {
      "1": "opentrons_96_tiprack_300ul",
      "2": "nest_96_wellplate_100ul_pcr_full_skirt",
      "3": "nest_12_reservoir_15ml",
    },
  },
  hardware_config: "",
  sop: "",
  code: "",
  plan: null,
  analyze: null,
  checks: null,
  fab: { lit: false },
  device_label: "OT-2",
  language: "zh",
};

const events: AgentEvent[] = [
  { seq: 1, t: 1, kind: "tool/call", name: "ask_user" },
  { seq: 2, t: 2, kind: "tool/result", name: "ask_user", detail: { duration_ms: 40, ok: true } },
];

function StageWaitSmoke() {
  return (
    <div className="app" data-smoke="stage-wait">
      <header className="workspace-header">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <h1>LabscriptAI</h1>
          </div>
        </div>
        <div className="header-status">
          <strong>快速确认</strong>
          <span>OT-2 · Prepare a PCR mix…</span>
        </div>
      </header>
      <div className="workspace" data-testid="shell" style={{ ["--chat-pct" as string]: "38%" }}>
        <section className="chat-column">
          <div className="chat-column-body">
            <div className="chat">
              <div className="history">
                <div className="bubble-row user">
                  <div className="bubble user">Prepare a PCR mix: dispense 20 µL of master mix into 8 sample wells.</div>
                </div>
                <div className="bubble-row">
                  <div className="bubble bot">
                    OT-2，标准台面：300 µL 枪头在 1 号槽，96 孔 PCR 板在 2 号槽，12 孔储液槽在 3 号槽。
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        <div className="split-seam" />
        <RightStage
          session={session}
          events={events}
          runningTool={null}
          busy={false}
          canWatch={false}
          onWatch={() => undefined}
        />
      </div>
    </div>
  );
}

const root = document.getElementById("root");
if (!root) throw new Error("missing #root");
createRoot(root).render(
  <StrictMode>
    <LangProvider>
      <StageWaitSmoke />
    </LangProvider>
  </StrictMode>
);
