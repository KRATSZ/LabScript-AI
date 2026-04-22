import test from "node:test";
import assert from "node:assert/strict";

import {
  buildVisionCheckPayload,
  normalizeVisionCheckProcessResult,
  runVisionCheck,
} from "../lib/vision-check.js";

test("runVisionCheck throws when image_path is missing", async () => {
  await assert.rejects(() => runVisionCheck({ imagePath: null }), /image_path/);
});

test("runVisionCheck throws when image file does not exist", async () => {
  await assert.rejects(() => runVisionCheck({ imagePath: "/nonexistent/deck.jpg" }), /not found/);
});

test("buildVisionCheckPayload normalizes optional fields", () => {
  assert.deepEqual(
    buildVisionCheckPayload({
      imagePath: "/tmp/deck.jpg",
      expectedLayout: { A1: "module" },
      confThreshold: 0.4,
      weights: "best.pt",
      useTextPrompts: true,
      annotatedOutputDir: "/tmp/out",
      deckCornersNorm: [[0, 0], [1, 0], [1, 1], [0, 1]],
      loadLabelsSidecar: false,
      classPrompts: ["module"],
      canonicalLabels: ["module"],
    }),
    {
      mode: "deck",
      image_path: "/tmp/deck.jpg",
      expected_layout: { A1: "module" },
      reference_image_path: null,
      conf_threshold: 0.4,
      weights: "best.pt",
      use_text_prompts: true,
      annotated_output_dir: "/tmp/out",
      deck_corners_norm: [[0, 0], [1, 0], [1, 1], [0, 1]],
      load_labels_sidecar: false,
      class_prompts: ["module"],
      canonical_labels: ["module"],
    },
  );
});

test("normalizeVisionCheckProcessResult returns parsed success payload", () => {
  const result = normalizeVisionCheckProcessResult({
    code: 0,
    stdout: JSON.stringify({
      summary: "ok",
      annotated_image_path: "/tmp/annotated.jpg",
      model: { lab_tuned: true },
    }),
    stderr: "",
    python: "python3",
  });

  assert.equal(result.summary, "ok");
  assert.equal(result.annotated_image_path, "/tmp/annotated.jpg");
  assert.equal(result.model.lab_tuned, true);
  assert.equal(result.python, "python3");
  assert.equal(result.vision_backend, "local_ultralytics");
});

test("normalizeVisionCheckProcessResult returns structured error payload on non-json stdout", () => {
  const result = normalizeVisionCheckProcessResult({
    code: 0,
    stdout: "not json",
    stderr: "warn",
    python: "python3",
  });

  assert.equal(result.summary, "vision_check returned non-JSON output.");
  assert.equal(result.needs_human_review, true);
  assert.equal(result.error.raw_stdout, "not json");
});

test("normalizeVisionCheckProcessResult preserves JSON error payload when python exits non-zero", () => {
  const result = normalizeVisionCheckProcessResult({
    code: 2,
    stdout: JSON.stringify({
      summary: "vision failed",
      annotated_image_path: "/tmp/annotated.jpg",
      model: { fallback_used: true },
    }),
    stderr: "stderr",
    python: "python3",
  });

  assert.equal(result.summary, "vision failed");
  assert.equal(result.exit_code, 2);
  assert.equal(result.annotated_image_path, "/tmp/annotated.jpg");
  assert.equal(result.model.fallback_used, true);
});

test("normalizeVisionCheckProcessResult falls back to generic process failure payload", () => {
  const result = normalizeVisionCheckProcessResult({
    code: 1,
    stdout: "traceback here",
    stderr: "stderr",
    python: "python3",
  });

  assert.equal(result.summary, "vision_check Python process failed.");
  assert.equal(result.needs_human_review, true);
  assert.equal(result.error.exit_code, 1);
  assert.match(result.error.stdout, /traceback/);
});
