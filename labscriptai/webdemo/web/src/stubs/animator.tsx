import type { ComponentType } from "react";

function commandsOf(analysisOutput: unknown): Array<{ commandType?: string }> {
  if (!analysisOutput || typeof analysisOutput !== "object") return [];
  const cmds = (analysisOutput as { commands?: unknown }).commands;
  return Array.isArray(cmds) ? cmds.filter((item) => item && typeof item === "object") : [];
}

/** Local Watch player when LabscriptAI_cloud is not checked out. Uses 8010 analyze commands. */
const ProtocolOperationAnimator: ComponentType<{ analysisOutput: unknown }> = ({
  analysisOutput,
}) => {
  const commands = commandsOf(analysisOutput);
  return (
    <div data-testid="protocol-operation-animator">
      <p className="file">OT Watch from 8010 analyze — {commands.length} commands (software, not a live deck).</p>
      {commands.slice(0, 40).map((cmd, index) => (
        <p key={index} className="file">
          {index + 1}. {String(cmd.commandType ?? "?")}
        </p>
      ))}
    </div>
  );
};

export default ProtocolOperationAnimator;
