/// <reference types="vite/client" />

declare module "@opentrons/protocol-visualization/styles";
declare module "@opentrons/components/styles/global";
declare module "@visualizer/normalize-analysis" {
  export function normalizeAnalysisOutput(input: Record<string, unknown>): unknown;
}
declare module "@visualizer/animator" {
  import type { ComponentType } from "react";
  const ProtocolOperationAnimator: ComponentType<{ analysisOutput: unknown }>;
  export default ProtocolOperationAnimator;
}
