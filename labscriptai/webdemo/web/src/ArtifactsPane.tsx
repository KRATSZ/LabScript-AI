import { ExportsPanel } from "./ExportsPanel";
import type { SessionSnapshot } from "./types";

export function ArtifactsPane({ session }: { session: SessionSnapshot | null }) {
  if (!session) {
    return <p className="hint">SOP, scripts, and worklists land here.</p>;
  }
  return (
    <div className="artifacts-pane" data-testid="artifacts-pane">
      <ExportsPanel session={session} filesOnly />
      {!session.sop?.trim() && !session.plan && !session.code?.trim() ? (
        <p className="hint">Nothing to download yet. Chat stays on the left.</p>
      ) : null}
    </div>
  );
}
