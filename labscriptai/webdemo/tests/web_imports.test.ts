import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SYSTEM_PROMPT } from "../server/src/prompt.ts";

const webSrc = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../web/src");

describe("web src case collisions", () => {
  it("no two files share a case-insensitive stem (macOS Vite trap)", () => {
    const stems = new Map<string, string[]>();
    for (const name of readdirSync(webSrc)) {
      const stem = name.replace(/\.[^.]+$/, "").toLowerCase();
      const list = stems.get(stem) ?? [];
      list.push(name);
      stems.set(stem, list);
    }
    const clashes = [...stems.values()].filter((list) => list.length > 1);
    assert.deepEqual(clashes, []);
  });
});

describe("AnimationOverlay code-split", () => {
  it("App.tsx lazy-loads AnimationOverlay", () => {
    const src = readFileSync(path.join(webSrc, "App.tsx"), "utf8");
    assert.match(src, /lazy\(\(\) => import\("\.\/AnimationOverlay"\)\)/);
    assert.doesNotMatch(src, /from ["']\.\/AnimationOverlay["']/);
  });

  it("App Suspense fallback uses OverlayChrome Close and backdrop", () => {
    const src = readFileSync(path.join(webSrc, "App.tsx"), "utf8");
    assert.match(src, /from ["']\.\/OverlayChrome["']/);
    assert.match(src, /<OverlayChrome onClose=\{[^}]+\}>/);
    assert.match(src, /Opening…/);
    const chrome = readFileSync(path.join(webSrc, "OverlayChrome.tsx"), "utf8");
    assert.match(chrome, /overlay-backdrop/);
    assert.match(chrome, />\s*Close\s*</);
    assert.doesNotMatch(chrome, /ProtocolOperationAnimator/);
  });

  it("demo start form does not link smoke pages", () => {
    const app = readFileSync(path.join(webSrc, "App.tsx"), "utf8");
    const start = readFileSync(path.join(webSrc, "StartForm.tsx"), "utf8");
    assert.doesNotMatch(app, /overlay-smoke|start-smoke|overlaySmoke|startSmoke/);
    assert.doesNotMatch(start, /overlay-smoke|start-smoke|overlaySmoke|startSmoke/);
  });

  it("scientist-facing copy names five robots and prompt supports emit_plan", () => {
    const files = ["App.tsx", "StartForm.tsx", "ChatPane.tsx", "startExamples.ts", "pipelineLogic.ts", "RightStage.tsx"];
    const blob = files.map((name) => readFileSync(path.join(webSrc, name), "utf8")).join("\n");
    assert.match(blob, /OT-2/);
    assert.match(blob, /Flex/);
    assert.match(blob, /Hamilton STAR/);
    assert.match(blob, /Hamilton Vantage/);
    assert.match(blob, /Tecan/);
    const prompt = readFileSync(path.resolve(webSrc, "../../server/src/prompt.ts"), "utf8");
    assert.doesNotMatch(SYSTEM_PROMPT, /Which robot/);
    assert.match(SYSTEM_PROMPT, /Never ask which machine/);
    assert.match(SYSTEM_PROMPT, /Hamilton/);
    assert.match(prompt, /emit_plan/);
    assert.match(prompt, /generate_code \(8010 Python\)/);
    assert.match(prompt, /Never change volumes, wells, counts/);
    assert.match(prompt, /Do not skip generate_code/);
    assert.doesNotMatch(prompt, /Plan IR/);
    assert.doesNotMatch(SYSTEM_PROMPT, /Confirm assumed_deck=true/);
    assert.match(SYSTEM_PROMPT, /Confirm the standard deck in one sentence/);
    assert.doesNotMatch(blob, /Robot is asked in chat/);
    assert.match(blob, /DEVICE_CARDS/);
  });

  it("artifacts helpers and Artifacts panel exist", () => {
    const artifacts = readFileSync(path.join(webSrc, "artifacts.ts"), "utf8");
    assert.match(artifacts, /export function planStepLine/);
    assert.match(artifacts, /export function downloadable/);
    assert.match(artifacts, /export function downloadText/);
    assert.match(artifacts, /"gwl"/);
    assert.match(artifacts, /"plr"/);
    assert.match(artifacts, /\.gwl worklist/);
    assert.match(artifacts, /PyLabRobot script/);
    const panel = readFileSync(path.join(webSrc, "ExportsPanel.tsx"), "utf8");
    assert.match(panel, /from ["']\.\/artifacts["']/);
    assert.match(panel, /DOWNLOAD_LABELS/);
    assert.match(panel, /export-hint/);
    const app = readFileSync(path.join(webSrc, "App.tsx"), "utf8");
    const artifactsPane = readFileSync(path.join(webSrc, "ArtifactsPane.tsx"), "utf8");
    const stagePane = readFileSync(path.join(webSrc, "StagePane.tsx"), "utf8");
    assert.match(artifactsPane, /from ["']\.\/ExportsPanel["']/);
    assert.match(artifactsPane, /<ExportsPanel session=\{session\} filesOnly \/>/);
    assert.match(stagePane, /from ["']\.\/IssuesPanel["']/);
    assert.match(stagePane, /Transfer steps/);
    assert.ok(
      stagePane.indexOf("Transfer steps") < stagePane.indexOf("<IssuesPanel"),
      "step list must sit above lab-check JSON"
    );
    assert.match(app, /from ["']\.\/RightStage["']/);
    assert.match(readFileSync(path.join(webSrc, "RightStage.tsx"), "utf8"), /session\?\.id/);
    assert.doesNotMatch(app, /from ["']\.\/AnimationOverlay["']/);
    assert.match(app, /sessionCanWatch/);
    assert.match(app, /robotSupportsWatch\(robotRef\.current\)/);
    assert.match(app, /disabled=\{busy\}/);
    assert.match(app, /setOverlay\(false\)/);
    assert.match(app, /fetchHealth/);
    assert.match(app, /8010 down/);
    assert.match(readFileSync(path.join(webSrc, "StagePane.tsx"), "utf8"), /watchUnavailableCopy/);
    assert.doesNotMatch(readFileSync(path.join(webSrc, "StagePane.tsx"), "utf8"), /DeckPlay|WatchPlayer|Run preview/);
    assert.match(readFileSync(path.join(webSrc, "ChatPane.tsx"), "utf8"), /sanitizeAssistantText/);
    assert.match(readFileSync(path.join(webSrc, "RightStage.tsx"), "utf8"), /tabCount/);
    assert.match(readFileSync(path.join(webSrc, "stageTabs.ts"), "utf8"), /export function tabCount/);
    assert.match(readFileSync(path.join(webSrc, "ChatPane.tsx"), "utf8"), /react-markdown/);
    assert.match(readFileSync(path.join(webSrc, "ChatPane.tsx"), "utf8"), /MarkdownBody/);
    const issues = readFileSync(path.join(webSrc, "IssuesPanel.tsx"), "utf8");
    assert.match(issues, /statusWord/);
    assert.match(issues, /status-word/);
  });

  it("overlay smoke uses simpleAnalysisFile and AnimatorGuard exposes errors", () => {
    const smoke = readFileSync(path.join(webSrc, "overlaySmoke.tsx"), "utf8");
    assert.match(smoke, /simpleAnalysisFile\.json/);
    assert.doesNotMatch(smoke, /mockRobotSideAnalysis/);
    const overlay = readFileSync(path.join(webSrc, "AnimationOverlay.tsx"), "utf8");
    const replay = readFileSync(path.join(webSrc, "OtDeckReplay.tsx"), "utf8");
    assert.match(replay, /data-animator-error=\{this\.state\.error\}/);
    assert.match(replay, /ProtocolVisualization/);
    assert.match(replay, /appType/);
    assert.match(overlay, /OtDeckReplay/);
    assert.doesNotMatch(overlay, /WatchPlayer/);
    assert.doesNotMatch(overlay, /ProtocolOperationAnimator/);
  });

  it("vite uses npm Opentrons viz and optional GitHub hang, not a vendored slim", () => {
    const vite = readFileSync(path.resolve(webSrc, "../vite.config.ts"), "utf8");
    assert.match(vite, /function cloudOrStub/);
    assert.match(vite, /stubRoot/);
    assert.match(vite, /LABSCRIPTAI_VISUALIZER_ROOT/);
    assert.match(vite, /@opentrons\/protocol-visualization/);
    assert.doesNotMatch(vite, /slimRoot, "components\/src\/index.ts"/);
    assert.match(readFileSync(path.join(webSrc, "stubs/normalize-analysis.ts"), "utf8"), /normalizeAnalysisOutput/);
    assert.match(readFileSync(path.join(webSrc, "stubs/animator.tsx"), "utf8"), /8010 analyze/);
    const webFiles = readdirSync(webSrc);
    assert.equal(webFiles.includes("DeckPlay.tsx"), false);
    assert.equal(webFiles.includes("WatchPlayer.tsx"), false);
    assert.equal(webFiles.includes("playBeats.ts"), false);
    assert.match(readFileSync(path.join(webSrc, "StagePane.tsx"), "utf8"), /OtDeckReplay/);
    assert.match(readFileSync(path.join(webSrc, "StagePane.tsx"), "utf8"), /PlrDeckReplay/);
    assert.match(readFileSync(path.join(webSrc, "PlrDeckReplay.tsx"), "utf8"), /\/api\/plr\/visualizer\/start/);
  });
});
