import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCaptureImageParams,
  buildCameraControlBody,
  buildCameraImageSettings,
  buildCameraStatusSnapshot,
  buildPreviewArtifactName,
  contentTypeToExtension,
  sanitizeCaptureFileName,
} from "../lib/vision.js";

test("buildCameraStatusSnapshot normalizes booleans from wrapped payload", () => {
  assert.deepEqual(
    buildCameraStatusSnapshot({
      data: {
        cameraEnabled: true,
        liveStreamEnabled: false,
        errorRecoveryCameraEnabled: true,
      },
    }),
    {
      camera_enabled: true,
      live_stream_enabled: false,
      error_recovery_camera_enabled: true,
    },
  );
});

test("buildCameraControlBody requires at least one state field", () => {
  assert.throws(() => buildCameraControlBody({}), /configure_camera requires at least one/);
});

test("buildCameraImageSettings builds resolution and pan blocks", () => {
  assert.deepEqual(
    buildCameraImageSettings({
      camera_id: "deck",
      resolution_width: 1280,
      resolution_height: 720,
      zoom: 1.25,
      pan_x: 10,
      pan_y: -5,
    }),
    {
      cameraId: "deck",
      resolution: { width: 1280, height: 720 },
      zoom: 1.25,
      pan: { x: 10, y: -5 },
    },
  );
});

test("buildCaptureImageParams uses array shapes required by captureImage", () => {
  assert.deepEqual(
    buildCaptureImageParams({
      file_name: "shot.jpg",
      resolution_width: 1280,
      resolution_height: 720,
      pan_x: 10,
      pan_y: -5,
    }),
    {
      fileName: "shot",
      resolution: [1280, 720],
      pan: [10, -5],
    },
  );
});

test("sanitizeCaptureFileName strips extensions and invalid characters", () => {
  assert.equal(sanitizeCaptureFileName("real deck shot.jpg"), "real-deck-shot");
});

test("contentTypeToExtension maps image mime types", () => {
  assert.equal(contentTypeToExtension("image/png"), "png");
  assert.equal(contentTypeToExtension("image/jpeg"), "jpg");
});

test("buildPreviewArtifactName uses safe filename parts", () => {
  assert.equal(
    buildPreviewArtifactName({
      robotIp: "10.31.2.149:31950",
      cameraId: "deck camera",
      contentType: "image/png",
      timestamp: "2026-03-24T08:30:10.123Z",
    }),
    "2026-03-24T08-30-10-123Z-10-31-2-149-31950-deck-camera-preview.png",
  );
});
