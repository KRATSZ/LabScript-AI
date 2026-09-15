import { OverlayChrome } from "./OverlayChrome";
import { WatchPlayer } from "./WatchPlayer";

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
        <WatchPlayer analyze={analyze} robot={robot} />
      </div>
    </OverlayChrome>
  );
}

export default AnimationOverlay;
