function unwrapData(payload) {
  if (payload && typeof payload === "object" && "data" in payload) {
    return payload.data;
  }
  return payload || {};
}

function hasOwnValue(value) {
  return value !== undefined && value !== null;
}

export function buildCameraStatusSnapshot(payload) {
  const data = unwrapData(payload);
  return {
    camera_enabled: hasOwnValue(data.cameraEnabled) ? Boolean(data.cameraEnabled) : null,
    live_stream_enabled: hasOwnValue(data.liveStreamEnabled)
      ? Boolean(data.liveStreamEnabled)
      : null,
    error_recovery_camera_enabled: hasOwnValue(data.errorRecoveryCameraEnabled)
      ? Boolean(data.errorRecoveryCameraEnabled)
      : null,
  };
}

export function buildCameraControlBody(args = {}) {
  const data = {};

  if (typeof args.camera_enabled === "boolean") {
    data.cameraEnabled = args.camera_enabled;
  }
  if (typeof args.live_stream_enabled === "boolean") {
    data.liveStreamEnabled = args.live_stream_enabled;
  }
  if (typeof args.error_recovery_camera_enabled === "boolean") {
    data.errorRecoveryCameraEnabled = args.error_recovery_camera_enabled;
  }

  if (!Object.keys(data).length) {
    throw new Error(
      "configure_camera requires at least one of camera_enabled, live_stream_enabled, or error_recovery_camera_enabled.",
    );
  }

  return { data };
}

export function buildCameraImageSettings(args = {}) {
  const data = {};

  if (args.camera_id) {
    data.cameraId = args.camera_id;
  }
  if (args.resolution_width || args.resolution_height) {
    if (!args.resolution_width || !args.resolution_height) {
      throw new Error("resolution_width and resolution_height must be provided together.");
    }
    data.resolution = {
      width: Number(args.resolution_width),
      height: Number(args.resolution_height),
    };
  }
  if (hasOwnValue(args.zoom)) {
    data.zoom = Number(args.zoom);
  }
  if (hasOwnValue(args.contrast)) {
    data.contrast = Number(args.contrast);
  }
  if (hasOwnValue(args.brightness)) {
    data.brightness = Number(args.brightness);
  }
  if (hasOwnValue(args.saturation)) {
    data.saturation = Number(args.saturation);
  }
  if (hasOwnValue(args.pan_x) || hasOwnValue(args.pan_y)) {
    if (!hasOwnValue(args.pan_x) || !hasOwnValue(args.pan_y)) {
      throw new Error("pan_x and pan_y must be provided together.");
    }
    data.pan = {
      x: Number(args.pan_x),
      y: Number(args.pan_y),
    };
  }

  return data;
}

export function buildCameraImageSettingsBody(args = {}) {
  const data = buildCameraImageSettings(args);
  if (!Object.keys(data).length) {
    throw new Error(
      "configure_camera requires image settings such as resolution_width, zoom, brightness, saturation, or pan_x/pan_y before calling /camera/cameraSettings.",
    );
  }
  return { data };
}

export function buildCaptureImageParams(args = {}) {
  const params = {};
  if (args.file_name) {
    params.fileName = sanitizeCaptureFileName(args.file_name);
  }
  if (args.resolution_width || args.resolution_height) {
    if (!args.resolution_width || !args.resolution_height) {
      throw new Error("resolution_width and resolution_height must be provided together.");
    }
    params.resolution = [Number(args.resolution_width), Number(args.resolution_height)];
  }
  if (hasOwnValue(args.zoom)) {
    params.zoom = Number(args.zoom);
  }
  if (hasOwnValue(args.pan_x) || hasOwnValue(args.pan_y)) {
    if (!hasOwnValue(args.pan_x) || !hasOwnValue(args.pan_y)) {
      throw new Error("pan_x and pan_y must be provided together.");
    }
    params.pan = [Number(args.pan_x), Number(args.pan_y)];
  }
  if (hasOwnValue(args.contrast)) {
    params.contrast = Number(args.contrast);
  }
  if (hasOwnValue(args.brightness)) {
    params.brightness = Number(args.brightness);
  }
  if (hasOwnValue(args.saturation)) {
    params.saturation = Number(args.saturation);
  }
  return params;
}

export function sanitizeCaptureFileName(fileName) {
  return String(fileName || "")
    .replace(/\.[^./\\]+$/g, "")
    .replace(/[^a-zA-Z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function contentTypeToExtension(contentType) {
  const normalized = String(contentType || "").toLowerCase();
  if (normalized.includes("png")) {
    return "png";
  }
  if (normalized.includes("webp")) {
    return "webp";
  }
  if (normalized.includes("gif")) {
    return "gif";
  }
  return "jpg";
}

export function buildPreviewArtifactName({
  robotIp,
  cameraId,
  contentType,
  timestamp = new Date().toISOString(),
} = {}) {
  const safeRobot = String(robotIp || "robot")
    .replace(/[^a-z0-9]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
  const safeCamera = cameraId
    ? String(cameraId)
        .replace(/[^a-z0-9]+/gi, "-")
        .replace(/^-+|-+$/g, "")
        .toLowerCase()
    : null;
  const safeTimestamp = String(timestamp).replace(/[:.]/g, "-");
  const extension = contentTypeToExtension(contentType);
  return `${safeTimestamp}-${safeRobot}${safeCamera ? `-${safeCamera}` : ""}-preview.${extension}`;
}
