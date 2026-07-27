import fs from "fs";
import path from "path";
import { spawn } from "child_process";

import { resolvePythonCandidates, SCRIPTS_DIR } from "./paths.js";

const visionScriptPath = path.join(SCRIPTS_DIR, "vision_check.py");

function runCommand(command, args, stdinJson) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: process.cwd(),
      env: process.env,
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", chunk => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", chunk => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", code => {
      resolve({ code, stdout, stderr, command, args });
    });

    if (stdinJson) {
      child.stdin.write(JSON.stringify(stdinJson));
      child.stdin.end();
    }
  });
}

async function runVisionCheckPython(payload, preferredPython) {
  const candidates = resolvePythonCandidates(preferredPython);

  let lastError = null;
  for (const candidate of candidates) {
    try {
      const result = await runCommand(
        candidate,
        [visionScriptPath],
        payload,
      );
      return { ...result, python: candidate };
    } catch (error) {
      if (error.code === "ENOENT") {
        lastError = error;
        continue;
      }
      throw error;
    }
  }

  throw lastError || new Error("No usable Python interpreter found for vision_check.");
}

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch (error) {
    return {
      parse_error: error.message,
      raw_stdout: text,
    };
  }
}

export function buildVisionCheckPayload({
  mode = "deck",
  imagePath,
  expectedLayout = null,
  referenceImagePath = null,
  confThreshold = 0.25,
  weights = null,
  useTextPrompts = null,
  annotatedOutputDir = null,
  deckCornersNorm = null,
  loadLabelsSidecar = null,
  classPrompts = null,
  canonicalLabels = null,
} = {}) {
  return {
    mode,
    image_path: imagePath,
    expected_layout: expectedLayout && typeof expectedLayout === "object" ? expectedLayout : null,
    reference_image_path: referenceImagePath,
    conf_threshold: confThreshold,
    weights,
    use_text_prompts: typeof useTextPrompts === "boolean" ? useTextPrompts : null,
    annotated_output_dir: annotatedOutputDir || null,
    deck_corners_norm: Array.isArray(deckCornersNorm) ? deckCornersNorm : null,
    load_labels_sidecar: typeof loadLabelsSidecar === "boolean" ? loadLabelsSidecar : null,
    class_prompts: Array.isArray(classPrompts) ? classPrompts.map(String) : null,
    canonical_labels: Array.isArray(canonicalLabels) ? canonicalLabels.map(String) : null,
  };
}

export function normalizeVisionCheckProcessResult(result) {
  if (result.code !== 0) {
    const parsed = safeJsonParse(result.stdout.trim());
    if (parsed && typeof parsed === "object" && !parsed.parse_error) {
      return {
        ...parsed,
        vision_backend: "local_ultralytics",
        python: result.python,
        stderr: result.stderr || null,
        exit_code: result.code,
      };
    }
    return {
      summary: "vision_check Python process failed.",
      needs_human_review: true,
      uncertainties: ["vision_process_failed"],
      observed_items: [],
      slot_observations: {},
      mismatches: [],
      annotated_image_path: null,
      error: {
        exit_code: result.code,
        stderr: result.stderr,
        stdout: result.stdout?.slice?.(0, 4000),
      },
      vision_backend: "local_ultralytics",
      python: result.python,
    };
  }

  const parsed = safeJsonParse(result.stdout.trim());
  if (parsed.parse_error) {
    return {
      summary: "vision_check returned non-JSON output.",
      needs_human_review: true,
      uncertainties: ["invalid_vision_json"],
      observed_items: [],
      slot_observations: {},
      mismatches: [],
      annotated_image_path: null,
      error: parsed,
      vision_backend: "local_ultralytics",
      python: result.python,
    };
  }

  return {
    ...parsed,
    vision_backend: "local_ultralytics",
    python: result.python,
    stderr: result.stderr || null,
  };
}

/**
 * Run local YOLOE/YOLO vision check (observation-only; does not mutate session state).
 */
export async function runVisionCheck({
  mode = "deck",
  imagePath,
  expectedLayout = null,
  referenceImagePath = null,
  confThreshold = 0.25,
  weights = null,
  useTextPrompts = null,
  annotatedOutputDir = null,
  pythonExecutable = null,
  deckCornersNorm = null,
  loadLabelsSidecar = null,
  classPrompts = null,
  canonicalLabels = null,
} = {}) {
  if (!imagePath) {
    throw new Error("vision_check requires image_path.");
  }

  const resolvedImage = path.resolve(imagePath);
  if (!fs.existsSync(resolvedImage)) {
    throw new Error(`vision_check: image not found: ${resolvedImage}`);
  }

  let resolvedRef = null;
  if (referenceImagePath) {
    resolvedRef = path.resolve(referenceImagePath);
    if (!fs.existsSync(resolvedRef)) {
      throw new Error(`vision_check: reference_image_path not found: ${resolvedRef}`);
    }
  }

  const weightsResolved =
    weights != null && String(weights).trim() !== ""
      ? String(weights).trim()
      : process.env.OPENTRONS_YOLOE_WEIGHTS && String(process.env.OPENTRONS_YOLOE_WEIGHTS).trim() !== ""
        ? String(process.env.OPENTRONS_YOLOE_WEIGHTS).trim()
        : null;

  const payload = buildVisionCheckPayload({
    mode,
    imagePath: resolvedImage,
    expectedLayout,
    referenceImagePath: resolvedRef,
    confThreshold,
    weights: weightsResolved,
    useTextPrompts,
    annotatedOutputDir,
    deckCornersNorm,
    loadLabelsSidecar,
    classPrompts,
    canonicalLabels,
  });

  const result = await runVisionCheckPython(payload, pythonExecutable);
  return normalizeVisionCheckProcessResult(result);
}
