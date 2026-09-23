import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { LanguageSwitch } from "./LanguageSwitch";
import { LangProvider, useLang } from "./LangContext";
import { RightStage } from "./RightStage";
import fixture from "./fixtures/simpleAnalysis.json";
import "./styles.css";
import type { AgentEvent, SessionSnapshot } from "./types";

const analyze = fixture as Record<string, unknown>;
const session: SessionSnapshot = {
  id: "watch-stage-smoke",
  phase: "ready",
  missing: [],
  goal: "Prepare a PCR mix: dispense 20 µL of master mix into 8 sample wells.",
  doc: "Dispense 20 µL of master mix into 8 sample wells.",
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
  sop: "# PCR mix",
  code: "from opentrons import protocol_api\n",
  plan: {
    steps: [
      { step_id: "1", primitive_type: "PICK_TIPS", tip_positions: ["A1"] },
      { step_id: "2", primitive_type: "ASPIRATE", source: "res:A1", volume_ul: 20 },
      { step_id: "3", primitive_type: "DISPENSE", destination: "plate:A1", volume_ul: 20 },
    ],
  },
  analyze,
  checks: { status: "pass" } as SessionSnapshot["checks"],
  fab: { lit: true },
  device_label: "OT-2",
};

const events: AgentEvent[] = [
  { seq: 1, t: 1, kind: "tool/call", name: "run_checks" },
  { seq: 2, t: 2, kind: "tool/result", name: "run_checks", detail: { duration_ms: 400, ok: true } },
];

function WatchStageSmoke() {
  const { t } = useLang();
  return (
    <div className="app" data-smoke="watch-stage">
      <header className="workspace-header">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <h1>LabscriptAI</h1>
          </div>
        </div>
        <div className="header-status">
          <strong className="status-pass">{t("Ready to watch")}</strong>
          <span>OT-2 · Prepare a PCR mix…</span>
        </div>
        <LanguageSwitch />
      </header>
      <div className="workspace session-mode watch-ready" data-testid="shell">
        <section className="chat-column" data-testid="chat-column">
          <div className="chat-column-body">
            <div className="chat">
              <div className="history">
                <div className="bubble-row user">
                  <div className="bubble user">
                    Prepare a PCR mix: dispense 20 µL of master mix into 8 sample wells.
                  </div>
                </div>
                <div className="bubble-row">
                  <div className="bubble bot">{t("Ready to watch")}</div>
                </div>
              </div>
              <form className="composer">
                <textarea rows={1} placeholder={t("Volume, wells, or a confirm…")} readOnly />
                <button className="send" type="button" disabled>
                  {t("Send")}
                </button>
              </form>
            </div>
          </div>
        </section>
        <RightStage
          session={session}
          events={events}
          runningTool={null}
          busy={false}
          canWatch
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
      <WatchStageSmoke />
    </LangProvider>
  </StrictMode>
);
