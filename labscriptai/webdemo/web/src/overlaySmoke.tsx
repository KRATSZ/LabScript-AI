import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AnimationOverlay } from "./AnimationOverlay";
import { LangProvider } from "./LangContext";
import fixture from "./fixtures/simpleAnalysis.json";
import "./styles.css";
import type { SessionSnapshot } from "./types";

// Cloud hang still referenced for contract: simpleAnalysisFile.json
// Seek contract: DemoReplay → seekVisualizerPlayback(setSelectedCommand) → official Watch command id.
const empty = new URLSearchParams(window.location.search).has("empty");
const analyze = empty ? null : (fixture as Record<string, unknown>);
const session: SessionSnapshot = {
  id: "smoke",
  phase: "ready",
  missing: [],
  goal: "Prepare a PCR mix",
  doc: "none",
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
  code: "",
  plan: {
    steps: [
      { step_id: "1", primitive_type: "PICK_TIPS", tip_positions: ["A1"] },
      { step_id: "2", primitive_type: "ASPIRATE", source: "res:A1", volume_ul: 20 },
      { step_id: "3", primitive_type: "DISPENSE", destination: "plate:A1", volume_ul: 20 },
    ],
  },
  analyze,
  checks: null,
  fab: { lit: false },
};

const root = document.getElementById("root");
if (!root) throw new Error("missing #root");
createRoot(root).render(
  <StrictMode>
    <LangProvider>
      <div data-smoke="overlay">
        <AnimationOverlay session={session} analyze={analyze} robot="OT-2" onClose={() => undefined} />
      </div>
    </LangProvider>
  </StrictMode>
);
