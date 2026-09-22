import { DemoReplay } from "./DemoReplay";
import { OverlayChrome } from "./OverlayChrome";
import { OtDeckReplay } from "./OtDeckReplay";
import type { SessionSnapshot } from "./types";

export function AnimationOverlay({
  session,
  analyze,
  robot,
  onClose,
}: {
  session?: SessionSnapshot | null;
  analyze: Record<string, unknown> | null;
  robot?: string | null;
  onClose: () => void;
}) {
  const replay = <OtDeckReplay analyze={analyze} robot={robot} appType="desktop" />;
  return (
    <OverlayChrome onClose={onClose}>
      <div className="overlay-player">
        <div className="overlay-player-inner">
          {session ? <DemoReplay session={session}>{replay}</DemoReplay> : replay}
        </div>
      </div>
    </OverlayChrome>
  );
}

export default AnimationOverlay;
