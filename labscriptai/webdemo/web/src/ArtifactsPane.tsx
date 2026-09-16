import { ExportsPanel } from "./ExportsPanel";
import type { SessionSnapshot } from "./types";

export function ArtifactsPane({ session }: { session: SessionSnapshot | null }) {
  if (!session) {
    return <p className="hint">Downloads land here after checks pass.</p>;
  }
  return (
    <div className="artifacts-pane" data-testid="artifacts-pane">
      <div className="activity-head">
        <h2>Files</h2>
        <p>Downloads after checks pass.</p>
      </div>
      <ExportsPanel session={session} filesOnly />
      {!session.sop?.trim() && !session.plan && !session.code?.trim() ? (
        <p className="hint">Nothing to download yet.</p>
      ) : null}
    </div>
  );
}
