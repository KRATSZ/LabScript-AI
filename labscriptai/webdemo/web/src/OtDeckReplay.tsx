import { Component, type ErrorInfo, type ReactNode, useMemo } from "react";
import {
  ProtocolVisualization,
  type ProtocolAnalysisOutput,
} from "@opentrons/protocol-visualization";
import "@opentrons/components/styles/global";
import "@opentrons/protocol-visualization/styles";
import { analysisResetKey, padAnalysisForAnimator } from "./analysis";

class AnimatorGuard extends Component<
  { children: ReactNode; resetKey: string },
  { failed: boolean; error: string }
> {
  state = { failed: false, error: "" };

  static getDerivedStateFromError(error: Error): { failed: boolean; error: string } {
    return { failed: true, error: error.message || String(error) };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    this.setState({ failed: true, error: error.message || String(error) });
    console.error("ProtocolVisualization render error:", error, info.componentStack);
  }

  componentDidUpdate(prevProps: { children: ReactNode; resetKey: string }): void {
    if (prevProps.resetKey !== this.props.resetKey) {
      this.setState({ failed: false, error: "" });
    }
  }

  render(): ReactNode {
    if (this.state.failed) {
      return (
        <p className="file" data-animator-error={this.state.error}>
          Cannot play.
        </p>
      );
    }
    return this.props.children;
  }
}

export function OtDeckReplay({
  analyze,
  robot,
  protocolName,
  appType = "desktop",
}: {
  analyze: Record<string, unknown> | null;
  robot?: string | null;
  protocolName?: string;
  appType?: "web" | "desktop";
}) {
  const analysis = useMemo(() => {
    if (!analyze) return null;
    return padAnalysisForAnimator(analyze, robot) as unknown as ProtocolAnalysisOutput;
  }, [analyze, robot]);
  const resetKey = analysisResetKey(analyze);

  if (!analysis) {
    return <p className="file">Cannot play.</p>;
  }

  return (
    <div className="ot-deck-embed" data-testid="ot-deck-replay">
      <AnimatorGuard resetKey={resetKey}>
        <ProtocolVisualization
          analysis={analysis}
          groupedCommands={null}
          protocolDisplayName={protocolName || "Opentrons protocol"}
          appType={appType}
        />
      </AnimatorGuard>
    </div>
  );
}

export default OtDeckReplay;
