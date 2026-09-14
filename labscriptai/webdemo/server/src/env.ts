import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const WEBDEMO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const REPO_ROOT = path.resolve(WEBDEMO_ROOT, "../..");
const CLOUD_ENV = path.resolve(REPO_ROOT, "../LabscriptAI_cloud/.env");

function parseEnvLine(line: string): [string, string] | null {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith("#")) return null;
  const eq = trimmed.indexOf("=");
  if (eq <= 0) return null;
  const key = trimmed.slice(0, eq).trim();
  let value = trimmed.slice(eq + 1).trim().replace(/\r$/, "");
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    value = value.slice(1, -1);
  }
  return [key, value];
}

function fillMissingFromFile(filePath: string): void {
  if (!existsSync(filePath)) return;
  const text = readFileSync(filePath, "utf8");
  for (const line of text.split(/\r?\n/)) {
    const parsed = parseEnvLine(line);
    if (!parsed) continue;
    const [key, value] = parsed;
    if (process.env[key] == null || process.env[key] === "") {
      process.env[key] = value;
    }
  }
}

export interface DemoEnv {
  apiKey: string;
  baseUrl: string;
  model: string;
  backend: string;
  python: string;
  repoRoot: string;
  webdemoRoot: string;
}

export function assertLocalBackend(url: string): string {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    throw new Error(`Backend refused: invalid URL (need 127.0.0.1 or localhost)`);
  }
  const host = parsed.hostname;
  if (host !== "127.0.0.1" && host !== "localhost") {
    throw new Error(`Backend refused: hostname ${host} is not 127.0.0.1 or localhost`);
  }
  return `${parsed.origin}${parsed.pathname}`.replace(/\/$/, "");
}

export function loadDemoEnv(): DemoEnv {
  fillMissingFromFile(path.join(WEBDEMO_ROOT, ".env"));
  fillMissingFromFile(CLOUD_ENV);

  const apiKey =
    process.env.LABSCRIPTAI_DEEPSEEK_API_KEY ||
    process.env.DEEPSEEK_API_KEY ||
    "";
  const baseUrl = (
    process.env.LABSCRIPTAI_DEEPSEEK_BASE_URL || "https://api.deepseek.com/v1"
  ).replace(/\/$/, "");
  const model =
    process.env.LABSCRIPTAI_DEEPSEEK_MODEL ||
    process.env.LABSCRIPTAI_MODEL_NAME ||
    "deepseek-v4-flash";
  // Python reviewer/author clients read DEEPSEEK_* / DEEPSEEK_REVIEW_*.
  // Official DeepSeek accepts both https://api.deepseek.com and .../v1.
  const pythonBase = baseUrl.replace(/\/v1$/, "") || "https://api.deepseek.com";
  const fill = (key: string, value: string) => {
    if (!process.env[key]) process.env[key] = value;
  };
  if (apiKey) {
    fill("DEEPSEEK_API_KEY", apiKey);
    fill("DEEPSEEK_REVIEW_API_KEY", apiKey);
  }
  fill("DEEPSEEK_BASE_URL", pythonBase);
  fill("DEEPSEEK_REVIEW_BASE_URL", pythonBase);
  fill("DEEPSEEK_MODEL", model);
  fill("DEEPSEEK_REVIEW_MODEL", model);

  return {
    apiKey,
    baseUrl,
    model,
    backend: assertLocalBackend(process.env.LABSCRIPTAI_BACKEND || "http://127.0.0.1:8010"),
    python: process.env.LABSCRIPTAI_PYTHON || "python3",
    repoRoot: REPO_ROOT,
    webdemoRoot: WEBDEMO_ROOT,
  };
}
