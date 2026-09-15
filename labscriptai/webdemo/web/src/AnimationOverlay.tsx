import { OverlayChrome } from "./OverlayChrome";
import { OtDeckReplay } from "./OtDeckReplay";

export function AnimationOverlay({
  analyze,
  robot,
  onClose,
}: {
  analyze: Record<string, unknown> | null;
  robot?: string | null;
  onClose: () => void;
}) {
  return (
    <OverlayChrome onClose={onClose}>
      <div className="overlay-player">
        <div className="overlay-player-inner">
          <OtDeckReplay analyze={analyze} robot={robot} appType="desktop" />
        </div>
      </div>
    </OverlayChrome>
  );
}

export default AnimationOverlay;
