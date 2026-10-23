import type { ComponentType } from "react";
import { useLang } from "../LangContext";

/** Local Watch player when LabscriptAI_cloud is not checked out. Uses 8010 analyze commands. */
const ProtocolOperationAnimator: ComponentType<{ analysisOutput: unknown }> = () => {
  const { lang } = useLang();
  return (
    <div className="animator-unavailable" data-testid="protocol-operation-animator">
      <p className="file">{lang === "zh"
        ? "在上方查看三维预演；点击步骤或拖动进度可查看对应动作。"
        : "Use the 3D preview above. Select a step or move the timeline to inspect an action."}</p>
    </div>
  );
};

export default ProtocolOperationAnimator;
