/// <reference types="vite/client" />

declare module "@opentrons/components";
declare module "@opentrons/shared-data" {
  export type ProtocolAnalysisOutput = Record<string, unknown>;
}
declare module "@opentrons/step-generation";
declare module "@visualizer/normalize-analysis" {
  export function normalizeAnalysisOutput(input: Record<string, unknown>): unknown;
}
declare module "@visualizer/animator" {
  import type { ComponentType } from "react";
  const ProtocolOperationAnimator: ComponentType<{ analysisOutput: unknown }>;
  export default ProtocolOperationAnimator;
}
