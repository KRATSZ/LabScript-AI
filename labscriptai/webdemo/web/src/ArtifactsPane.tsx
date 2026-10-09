import { ExportsPanel } from "./ExportsPanel";
import { IssuesPanel } from "./IssuesPanel";
import { ProtocolSummaryCard } from "./SummaryCard";
import { useLang } from "./LangContext";
import type { SessionSnapshot } from "./types";

export function ArtifactsPane({ session }: { session: SessionSnapshot | null }) {
  const { t } = useLang();
  if (!session) {
    return <p className="hint">{t("Downloads land here.")}</p>;
  }
  return (
    <div className="artifacts-pane" data-testid="artifacts-pane">
      <div className="activity-head">
        <h2>{t("Files")}</h2>
        <p>{t("Downloads after checks.")}</p>
      </div>
      <ProtocolSummaryCard session={session} />
      {session.checks ? <IssuesPanel checks={session.checks} session={session} /> : null}
      <ExportsPanel session={session} filesOnly />
      {!session.sop?.trim() && !session.plan && !session.code?.trim() ? (
        <p className="hint">{t("Nothing to download yet.")}</p>
      ) : null}
    </div>
  );
}
