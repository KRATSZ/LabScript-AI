import { useMemo } from "react";
import { DeckSketch } from "./DeckSketchView";
import { DemoReplay } from "./DemoReplay";
import { useLang } from "./LangContext";
import { planPreviewGap, sessionForPlanSketch } from "./planPreview";
import { planReplaySteps } from "./replaySteps";
import type { SessionSnapshot } from "./types";

export function PlrDeckReplay({
  plan,
  robot,
  session = null,
}: {
  plan: Record<string, unknown> | null;
  robot?: string | null;
  previewUp?: boolean;
  session?: SessionSnapshot | null;
}) {
  const { t } = useLang();
  const steps = useMemo(() => planReplaySteps(plan ?? session?.plan), [plan, session?.plan]);
  const sketchSession = useMemo(
    () => sessionForPlanSketch(session, plan ?? session?.plan ?? null, robot ?? session?.robot),
    [session, plan, robot]
  );
  const gap = planPreviewGap(plan ?? session?.plan, sketchSession?.hardware?.deck);
  const body = (
    <div className="plr-deck-embed" data-testid="plr-deck-replay">
      <div className="plr-deck-viewport plr-deck-inpage">
        {gap ? (
          <div className="stage-empty" data-testid="plr-preview-gap">
            <h2>{t("Deck")}</h2>
            <p>{t(gap)}</p>
          </div>
        ) : sketchSession ? (
          <DeckSketch session={sketchSession} />
        ) : (
          <div className="stage-empty" data-testid="plr-preview-gap">
            <h2>{t("Deck")}</h2>
            <p>{t(planPreviewGap(null) ?? "")}</p>
          </div>
        )}
      </div>
    </div>
  );

  if (!session) return body;
  return (
    <DemoReplay session={session} current={0} totalHint={steps.length}>
      {body}
    </DemoReplay>
  );
}
