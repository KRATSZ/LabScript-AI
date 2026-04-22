#!/usr/bin/env node
/**
 * Run MCP-equivalent Kimi K2.5 deck photo analysis (SiliconFlow) on one local image.
 *
 *   export SILICONFLOW_API_KEY=...
 *   node mcp-servers/opentrons-mcp/scripts/vlm_kimi_deck_one.mjs path/to/image.jpeg
 *
 * Optional: pass custom prompt as second arg (quoted).
 */
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const mcpRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(__dirname, "../../..");

const imageArg = process.argv[2];
if (!imageArg) {
  console.error("Usage: SILICONFLOW_API_KEY=... node mcp-servers/opentrons-mcp/scripts/vlm_kimi_deck_one.mjs <image.jpeg> [optional prompt]");
  process.exit(1);
}

const imagePath = path.isAbsolute(imageArg) ? imageArg : path.join(repoRoot, imageArg);
const optionalPrompt = process.argv[3] || null;

process.chdir(mcpRoot);
const { TOOL_HANDLERS } = await import(path.join(mcpRoot, "index.js"));

try {
  const result = await TOOL_HANDLERS.analyze_image_with_kimi({
    image_path: imagePath,
    ...(optionalPrompt ? { prompt: optionalPrompt } : {}),
    model: "Pro/moonshotai/Kimi-K2.5",
    detail: "high",
    max_tokens: 2000,
  });
  console.log(JSON.stringify(result.data, null, 2));
} catch (err) {
  console.error(String(err?.message || err));
  process.exit(1);
}
