import type { ComponentType } from "react";

/** Fallback Watch player when LabscriptAI_cloud is missing. Tecan/Hamilton do not use Watch. */
const ProtocolOperationAnimator: ComponentType<{ analysisOutput: unknown }> = () => (
  <p className="file">
    Watch animation needs the LabscriptAI_cloud visualizer. Tecan Fluent and Hamilton plans do not
    use Watch — download the step list instead.
  </p>
);

export default ProtocolOperationAnimator;
