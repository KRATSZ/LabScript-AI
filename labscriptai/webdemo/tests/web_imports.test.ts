import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

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

  it("scientist-facing copy is OT-2 or Flex, and the prompt prefers 8010 Python", () => {
    const files = ["App.tsx", "StartForm.tsx", "ChatPane.tsx", "startExamples.ts", "pipelineLogic.ts"];
    const blob = files.map((name) => readFileSync(path.join(webSrc, name), "utf8")).join("\n");
    assert.match(blob, /OT-2/);
    assert.match(blob, /Flex/);
    assert.doesNotMatch(blob, /Hamilton/);
    assert.doesNotMatch(blob, /Tecan/);
    const prompt = readFileSync(path.resolve(webSrc, "../../server/src/prompt.ts"), "utf8");
    assert.match(prompt, /Which robot — OT-2 or Flex\?/);
    assert.match(prompt, /I'll assume a standard deck/);
    assert.match(prompt, /assumed_deck=true/);
    assert.match(prompt, /generate_code \(8010 Python\)/);
    assert.match(prompt, /Do not change volumes, wells, or counts the user gave/);
    assert.match(prompt, /No bash\. No robot\. No live Flex\./);
    assert.match(prompt, /Replies stay short/);
    assert.match(prompt, /Do not skip generate_code/);
    assert.doesNotMatch(prompt, /emit_plan/);
    assert.doesNotMatch(prompt, /Hamilton/);
    assert.doesNotMatch(prompt, /Tecan/);
    assert.doesNotMatch(prompt, /Plan IR/);
  });

  it("overlay smoke uses simpleAnalysisFile and AnimatorGuard exposes errors", () => {
    const smoke = readFileSync(path.join(webSrc, "overlaySmoke.tsx"), "utf8");
    assert.match(smoke, /simpleAnalysisFile\.json/);
    assert.doesNotMatch(smoke, /mockRobotSideAnalysis/);
    const overlay = readFileSync(path.join(webSrc, "AnimationOverlay.tsx"), "utf8");
    assert.match(overlay, /data-animator-error=\{this\.state\.error\}/);
  });
});
