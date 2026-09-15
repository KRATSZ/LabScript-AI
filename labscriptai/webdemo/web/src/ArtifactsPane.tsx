import { ExportsPanel } from "./ExportsPanel";
import type { SessionSnapshot } from "./types";

export function ArtifactsPane({ session }: { session: SessionSnapshot | null }) {
  if (!session) {
    return <p className="hint">SOP, step JSON, .gwl, and PyLabRobot scripts land here.</p>;
  }
  return (
    <div className="artifacts-pane" data-testid="artifacts-pane">
      <ExportsPanel session={session} filesOnly />
      {!session.sop?.trim() && !session.plan && !session.code?.trim() ? (
        <p className="hint">Nothing downloadable yet. Chat stays in the left pane.</p>
      ) : null}
    </div>
  );
}
