import type { ReactNode } from "react";

export function OverlayChrome({
  onClose,
  children,
}: {
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <div className="overlay">
      <div className="overlay-backdrop" onClick={onClose} />
      <div className="overlay-card">
        <div className="overlay-head">
          <strong>Watch the protocol</strong>
          <button className="ghost" type="button" onClick={onClose}>
            Close
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
