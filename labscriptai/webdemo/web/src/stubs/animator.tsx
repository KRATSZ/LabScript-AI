import { useEffect, useState, type ComponentType } from "react";

function commandsOf(analysisOutput: unknown): Array<{ commandType?: string }> {
  if (!analysisOutput || typeof analysisOutput !== "object") return [];
  const cmds = (analysisOutput as { commands?: unknown }).commands;
  return Array.isArray(cmds) ? cmds.filter((item) => item && typeof item === "object") : [];
}

function commandLabel(type: string): string {
  const raw = type.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/_/g, " ");
  return raw ? raw.charAt(0).toUpperCase() + raw.slice(1) : "?";
}

/** Local Watch player when LabscriptAI_cloud is not checked out. Uses 8010 analyze commands. */
const ProtocolOperationAnimator: ComponentType<{ analysisOutput: unknown }> = ({
  analysisOutput,
}) => {
  const commands = commandsOf(analysisOutput);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (commands.length < 2) return;
    if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }
    const timer = window.setInterval(() => {
      setIndex((cur) => (cur + 1) % commands.length);
    }, 900);
    return () => window.clearInterval(timer);
  }, [commands.length]);

  const current = commands[Math.min(index, Math.max(commands.length - 1, 0))];

  return (
    <div data-testid="protocol-operation-animator" className="watch-stub">
      <p className="file">
        OT Watch from 8010 analyze — {commands.length} commands (software, not a live deck).
      </p>
      {current ? (
        <p className="watch-stub-now" data-testid="watch-stub-now">
          {index + 1}. {commandLabel(String(current.commandType ?? "?"))}
        </p>
      ) : null}
      <div className="watch-stub-list">
        {commands.slice(0, 40).map((cmd, i) => (
          <p key={i} className={i === index ? "file watch-stub-active" : "file"}>
            {i + 1}. {commandLabel(String(cmd.commandType ?? "?"))}
          </p>
        ))}
      </div>
    </div>
  );
};

export default ProtocolOperationAnimator;
