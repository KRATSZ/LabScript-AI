import { Component, type ErrorInfo, type ReactNode, useMemo } from "react";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import type { ProtocolAnalysisOutput } from "@opentrons/shared-data";
import { normalizeAnalysisOutput } from "../../../../../LabscriptAI_cloud/web/opentrons-protocol-visualizer-web-slim/protocol-visualizer-web/client/src/normalizeAnalysisOutput";
import ProtocolOperationAnimator from "../../../../../LabscriptAI_cloud/labscriptAI-frontend/src/components/ProtocolOperationAnimator";
import { analysisResetKey, safeNormalizeAnalysis } from "./analysis";
import { OverlayChrome } from "./OverlayChrome";

const theme = createTheme({
  palette: {
    primary: { main: "#2563eb" },
    secondary: { main: "#0d9488" },
    error: { main: "#ef4444" },
    success: { main: "#16a34a" },
  },
});

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
    console.error("ProtocolOperationAnimator render error:", error, info.componentStack);
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

export function AnimationOverlay({
  analyze,
  robot,
  onClose,
}: {
  analyze: Record<string, unknown> | null;
  robot?: string | null;
  onClose: () => void;
}) {
  const analysisOutput = useMemo(
    () =>
      safeNormalizeAnalysis(
        analyze,
        (input) => normalizeAnalysisOutput(input as unknown as ProtocolAnalysisOutput),
        robot
      ),
    [analyze, robot]
  );
  const resetKey = analysisResetKey(analyze);

  return (
    <OverlayChrome onClose={onClose}>
      <div className="overlay-player">
        {analysisOutput ? (
          <div className="overlay-player-inner">
            <ThemeProvider theme={theme}>
              <AnimatorGuard resetKey={resetKey}>
                <ProtocolOperationAnimator analysisOutput={analysisOutput} />
              </AnimatorGuard>
            </ThemeProvider>
          </div>
        ) : (
          <p className="file">Cannot play.</p>
        )}
      </div>
    </OverlayChrome>
  );
}

export default AnimationOverlay;
