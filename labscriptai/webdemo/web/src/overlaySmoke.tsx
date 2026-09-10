import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AnimationOverlay } from "./AnimationOverlay";
import fixture from "../../../../../LabscriptAI_cloud/web/opentrons-protocol-visualizer-web-slim/shared-data/js/helpers/__fixtures__/simpleAnalysisFile.json";
import "./styles.css";

const empty = new URLSearchParams(window.location.search).has("empty");
const analyze = empty ? null : (fixture as Record<string, unknown>);

const root = document.getElementById("root");
if (!root) throw new Error("missing #root");
createRoot(root).render(
  <StrictMode>
    <div data-smoke="overlay">
      <AnimationOverlay analyze={analyze} onClose={() => undefined} />
    </div>
  </StrictMode>
);
