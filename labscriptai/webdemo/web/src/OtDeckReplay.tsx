import { Component, type ErrorInfo, type ReactNode, useLayoutEffect, useMemo, useRef, type RefObject } from "react";
import {
  ProtocolVisualization,
  type ProtocolAnalysisOutput,
} from "@opentrons/protocol-visualization";
import "@opentrons/components/styles/global";
import "@opentrons/protocol-visualization/styles";
import { analysisResetKey, padAnalysisForAnimator } from "./analysis";
import { PHONE_LAYOUT_QUERY, syncPhoneDeckSvg } from "./deckSvgFit";
import { FlexReplayTicks } from "./FlexReplayTicks";

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

function PhoneDeckSvgFit({ hostRef }: { hostRef: RefObject<HTMLElement | null> }) {
  useLayoutEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let raf = 0;
    const fit = () => {
      cancelAnimationFrame(raf);
      syncPhoneDeckSvg(host);
      raf = requestAnimationFrame(() => syncPhoneDeckSvg(host));
    };
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(host);
    const mo = new MutationObserver(fit);
    mo.observe(host, { childList: true, subtree: true });
    const mq = window.matchMedia(PHONE_LAYOUT_QUERY);
    const onChange = () => fit();
    mq.addEventListener("change", onChange);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      mo.disconnect();
      mq.removeEventListener("change", onChange);
    };
  }, [hostRef]);
  return null;
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
  const hostRef = useRef<HTMLDivElement>(null);

  if (!analysis) {
    return <p className="file">Cannot play.</p>;
  }

  return (
    <div
      className={robot === "Flex" ? "ot-deck-embed is-flex" : "ot-deck-embed"}
      data-testid="ot-deck-replay"
      data-robot={robot ?? ""}
      ref={hostRef}
    >
      <PhoneDeckSvgFit hostRef={hostRef} />
      <AnimatorGuard resetKey={resetKey}>
        <ProtocolVisualization
          analysis={analysis}
          groupedCommands={null}
          protocolDisplayName={protocolName || "Opentrons protocol"}
          appType={appType}
        />
      </AnimatorGuard>
      {robot === "Flex" ? <FlexReplayTicks hostRef={hostRef} /> : null}
    </div>
  );
}

export default OtDeckReplay;
