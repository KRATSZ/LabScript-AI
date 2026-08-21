import { loadAutomationEnvValue } from "./automation-env.js";
import {
  buildDeckPhotoAnalysisPrompt,
  buildImageDataUrl,
  extractAssistantText,
  parseAssistantJson,
} from "./siliconflow.js";

const DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3";
// Default Ark endpoint for Seed 2.0 Pro (Volcengine Ark Responses API).
const DEFAULT_ARK_MODEL_ENDPOINT = "ep-20260716144817-n6rgn";
const DEFAULT_ARK_MAX_OUTPUT_TOKENS = 4096;

export function resolveArkApiKey({ apiKey = null } = {}) {
  return apiKey || loadAutomationEnvValue("ARK_API_KEY") || null;
}

export function resolveArkModelEndpoint({ modelEndpoint = null } = {}) {
  return (
    modelEndpoint ||
    process.env.ARK_MODEL_ENDPOINT ||
    loadAutomationEnvValue("ARK_MODEL_ENDPOINT") ||
    DEFAULT_ARK_MODEL_ENDPOINT
  );
}

export function resolveArkBaseUrl({ baseUrl = null } = {}) {
  return (
    baseUrl ||
    process.env.ARK_BASE_URL ||
    loadAutomationEnvValue("ARK_BASE_URL") ||
    DEFAULT_ARK_BASE_URL
  );
}

export function buildArkDeckPhotoAnalysisPrompt({
  prompt = null,
  expectedLayout = null,
} = {}) {
  if (prompt) {
    return prompt;
  }

  const basePrompt = buildDeckPhotoAnalysisPrompt({ expectedLayout });
  return [
    basePrompt,
    "",
    "输出要求（必须遵守）：",
    "1. 最终回复只能是单个 JSON 对象，不要 markdown，不要解释，不要推理过程。",
    "2. observed_items 必须是对象数组，每项含 slot、label、confidence、evidence。",
    "3. 若与 expected_layout 不一致，在 possible_issues 中明确写出槽位差异。",
  ].join("\n");
}

export function buildArkResponsesBody({
  modelEndpoint,
  imageDataUrl,
  prompt,
  maxOutputTokens = DEFAULT_ARK_MAX_OUTPUT_TOKENS,
} = {}) {
  if (!modelEndpoint) {
    throw new Error("Ark model endpoint is required.");
  }
  if (!imageDataUrl) {
    throw new Error("imageDataUrl is required.");
  }
  if (!prompt) {
    throw new Error("prompt is required.");
  }

  return {
    model: modelEndpoint,
    max_output_tokens: maxOutputTokens,
    input: [
      {
        role: "user",
        content: [
          {
            type: "input_image",
            image_url: imageDataUrl,
          },
          {
            type: "input_text",
            text: prompt,
          },
        ],
      },
    ],
  };
}

export function extractArkMessageText(responseJson) {
  const output = Array.isArray(responseJson?.output) ? responseJson.output : [];
  const textParts = [];
  for (const item of output) {
    if (item?.type === "message" && Array.isArray(item.content)) {
      for (const block of item.content) {
        if (block?.type === "output_text" && block.text) {
          textParts.push(String(block.text));
        }
      }
    }
  }
  return textParts.join("\n").trim() || null;
}

export function extractArkReasoningSummaryText(responseJson) {
  const output = Array.isArray(responseJson?.output) ? responseJson.output : [];
  const textParts = [];
  for (const item of output) {
    if (item?.type !== "reasoning" || !Array.isArray(item.summary)) {
      continue;
    }
    for (const block of item.summary) {
      if (block?.type === "summary_text" && block.text) {
        textParts.push(String(block.text).trim());
      }
    }
  }
  return textParts.join("\n").trim() || null;
}

export function extractLastJsonObject(text) {
  if (!text) {
    return null;
  }

  const fencedMatches = [...String(text).matchAll(/```json\s*([\s\S]*?)\s*```/gi)];
  for (let index = fencedMatches.length - 1; index >= 0; index -= 1) {
    const candidate = fencedMatches[index]?.[1]?.trim();
    if (candidate && parseAssistantJson(candidate)) {
      return candidate;
    }
  }

  let start = String(text).lastIndexOf("{");
  while (start >= 0) {
    const slice = String(text).slice(start);
    const parsed = parseAssistantJson(slice);
    if (parsed) {
      const match = slice.match(/\{[\s\S]*\}/);
      return match?.[0] || slice;
    }
    start = String(text).lastIndexOf("{", start - 1);
  }

  return null;
}

export function extractArkResponseText(responseJson) {
  const messageText = extractArkMessageText(responseJson);
  if (messageText) {
    return messageText;
  }
  const reasoningText = extractArkReasoningSummaryText(responseJson);
  if (reasoningText) {
    return reasoningText;
  }
  return extractAssistantText(responseJson);
}

export function resolveArkAssistantPayload(responseJson) {
  const messageText = extractArkMessageText(responseJson);
  const reasoningText = extractArkReasoningSummaryText(responseJson);
  const status = responseJson?.status || null;
  const incompleteReason = responseJson?.incomplete_details?.reason || null;

  const candidates = [];
  if (messageText) {
    candidates.push({ source: "message", text: messageText });
  }
  if (reasoningText) {
    const embeddedJson = extractLastJsonObject(reasoningText);
    if (embeddedJson) {
      candidates.push({ source: "reasoning_summary_json", text: embeddedJson });
    }
    candidates.push({ source: "reasoning_summary", text: reasoningText });
  }

  for (const candidate of candidates) {
    const parsed = parseAssistantJson(candidate.text);
    if (parsed && typeof parsed === "object") {
      return {
        raw_text: candidate.text,
        parsed_result: parsed,
        text_source: candidate.source,
        reasoning_fallback_used: candidate.source !== "message",
        message_text: messageText,
        reasoning_summary: reasoningText,
        status,
        incomplete_reason: incompleteReason,
      };
    }
  }

  const fallbackText = messageText || reasoningText || null;
  return {
    raw_text: fallbackText,
    parsed_result: parseAssistantJson(fallbackText),
    text_source: messageText ? "message_unparsed" : reasoningText ? "reasoning_unparsed" : null,
    reasoning_fallback_used: Boolean(!messageText && reasoningText),
    message_text: messageText,
    reasoning_summary: reasoningText,
    status,
    incomplete_reason: incompleteReason,
  };
}

export async function callArkResponses({
  apiKey,
  baseUrl = DEFAULT_ARK_BASE_URL,
  body,
} = {}) {
  if (!apiKey) {
    throw new Error("Ark API key is required. Pass api_key or set ARK_API_KEY.");
  }
  const url = `${String(baseUrl).replace(/\/$/, "")}/responses`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  });
  const responseText = await response.text();
  let responseJson = null;
  try {
    responseJson = JSON.parse(responseText);
  } catch {
    responseJson = null;
  }

  if (!response.ok) {
    throw new Error(
      `Ark request failed: ${response.status} ${response.statusText}${
        responseText ? ` - ${responseText}` : ""
      }`,
    );
  }

  return {
    json: responseJson,
    requestId: responseJson?.id || response.headers.get("x-request-id") || null,
  };
}

async function requestArkAnalysis({
  apiKey,
  baseUrl,
  modelEndpoint,
  dataUrl,
  prompt,
  maxOutputTokens,
} = {}) {
  const body = buildArkResponsesBody({
    modelEndpoint,
    imageDataUrl: dataUrl,
    prompt,
    maxOutputTokens,
  });
  const response = await callArkResponses({
    apiKey,
    baseUrl,
    body,
  });
  const payload = resolveArkAssistantPayload(response.json);
  return {
    response,
    payload,
  };
}

export async function analyzeImageWithArk({
  imagePath,
  apiKey = null,
  baseUrl = null,
  modelEndpoint = null,
  prompt = null,
  expectedLayout = null,
  maxOutputTokens = DEFAULT_ARK_MAX_OUTPUT_TOKENS,
} = {}) {
  const { dataUrl, imagePath: resolvedImage, mimeType } = buildImageDataUrl(imagePath);
  const resolvedApiKey = resolveArkApiKey({ apiKey });
  const resolvedModel = resolveArkModelEndpoint({ modelEndpoint });
  const resolvedBaseUrl = resolveArkBaseUrl({ baseUrl });
  const resolvedPrompt = buildArkDeckPhotoAnalysisPrompt({
    prompt,
    expectedLayout,
  });

  let { response, payload } = await requestArkAnalysis({
    apiKey: resolvedApiKey,
    baseUrl: resolvedBaseUrl,
    modelEndpoint: resolvedModel,
    dataUrl,
    prompt: resolvedPrompt,
    maxOutputTokens,
  });

  let fallbackUsed = false;
  if (!payload.parsed_result && (payload.status === "incomplete" || !payload.message_text)) {
    fallbackUsed = true;
    const retryPrompt = [
      resolvedPrompt,
      "",
      "上一请求未完成。现在请只输出完整 JSON 对象，不要 reasoning，不要 markdown，不要额外文字。",
    ].join("\n");
    ({ response, payload } = await requestArkAnalysis({
      apiKey: resolvedApiKey,
      baseUrl: resolvedBaseUrl,
      modelEndpoint: resolvedModel,
      dataUrl,
      prompt: retryPrompt,
      maxOutputTokens: Math.max(maxOutputTokens, DEFAULT_ARK_MAX_OUTPUT_TOKENS),
    }));
  }

  return {
    image_path: resolvedImage,
    mime_type: mimeType,
    provider: "ark",
    model_endpoint: resolvedModel,
    resolved_model: response.json?.model || resolvedModel,
    request_id: response.requestId,
    prompt: resolvedPrompt,
    parsed_result: payload.parsed_result,
    raw_text: payload.raw_text,
    text_source: payload.text_source,
    reasoning_fallback_used: payload.reasoning_fallback_used,
    retry_used: fallbackUsed,
    message_text: payload.message_text,
    reasoning_summary: payload.reasoning_summary,
    usage: response.json?.usage || null,
    status: payload.status,
    incomplete_reason: payload.incomplete_reason,
  };
}
