import test from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import os from "os";
import path from "path";

import {
  buildDeckPhotoAnalysisPrompt,
  buildImageDataUrl,
  buildSiliconFlowChatBody,
  extractAssistantText,
  parseAssistantJson,
} from "../lib/siliconflow.js";

test("buildImageDataUrl reads local image bytes", () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "sf-image-"));
  const imagePath = path.join(tempDir, "sample.jpg");
  fs.writeFileSync(imagePath, Buffer.from("fake-image"));

  const result = buildImageDataUrl(imagePath);
  assert.equal(result.mimeType, "image/jpeg");
  assert.match(result.dataUrl, /^data:image\/jpeg;base64,/);
});

test("buildSiliconFlowChatBody creates multimodal chat payload", () => {
  const payload = buildSiliconFlowChatBody({
    model: "Pro/moonshotai/Kimi-K2.5",
    imageDataUrl: "data:image/jpeg;base64,AAA",
    prompt: "请分析这张图",
  });

  assert.equal(payload.model, "Pro/moonshotai/Kimi-K2.5");
  assert.equal(payload.messages[0].role, "user");
  assert.equal(payload.messages[0].content[0].type, "image_url");
  assert.equal(payload.messages[0].content[1].type, "text");
});

test("buildDeckPhotoAnalysisPrompt injects expected layout", () => {
  const prompt = buildDeckPhotoAnalysisPrompt({
    expectedLayout: { C2: "opentrons_flex_96_tiprack_200ul" },
  });
  assert.match(prompt, /C2/);
  assert.match(prompt, /JSON/);
});

test("assistant text helpers parse JSON", () => {
  const text = extractAssistantText({
    choices: [{ message: { content: '{"summary":"ok"}' } }],
  });
  assert.equal(text, '{"summary":"ok"}');
  assert.deepEqual(parseAssistantJson(text), { summary: "ok" });
});
