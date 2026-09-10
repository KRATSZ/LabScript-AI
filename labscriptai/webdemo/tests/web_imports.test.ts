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

  it("scientist-facing copy names four robots and prompt supports emit_plan", () => {
    const files = ["App.tsx", "StartForm.tsx", "ChatPane.tsx", "startExamples.ts", "pipelineLogic.ts"];
    const blob = files.map((name) => readFileSync(path.join(webSrc, name), "utf8")).join("\n");
    assert.match(blob, /OT-2/);
    assert.match(blob, /Flex/);
    assert.match(blob, /Hamilton/);
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
    assert.match(app, /from ["']\.\/ExportsPanel["']/);
    assert.match(app, /<ExportsPanel session=\{session\} \/>/);
    assert.doesNotMatch(app, /from ["']\.\/AnimationOverlay["']/);
    assert.match(app, /sessionCanWatch/);
    assert.match(app, /robotSupportsWatch\(robotRef\.current\)/);
    assert.match(app, /disabled=\{busy\}/);
    assert.match(app, /setOverlay\(false\)/);
    const issues = readFileSync(path.join(webSrc, "IssuesPanel.tsx"), "utf8");
    assert.match(issues, /statusWord/);
    assert.match(issues, /status-word/);
  });

  it("overlay smoke uses simpleAnalysisFile and AnimatorGuard exposes errors", () => {
    const smoke = readFileSync(path.join(webSrc, "overlaySmoke.tsx"), "utf8");
    assert.match(smoke, /simpleAnalysisFile\.json/);
    assert.doesNotMatch(smoke, /mockRobotSideAnalysis/);
    const overlay = readFileSync(path.join(webSrc, "AnimationOverlay.tsx"), "utf8");
    assert.match(overlay, /data-animator-error=\{this\.state\.error\}/);
  });
});
