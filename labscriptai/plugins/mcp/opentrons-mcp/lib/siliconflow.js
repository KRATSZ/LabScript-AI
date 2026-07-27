import fs from "fs";
import path from "path";

function guessMimeType(filePath) {
  const lower = String(path.extname(filePath) || "").toLowerCase();
  switch (lower) {
    case ".png":
      return "image/png";
    case ".webp":
      return "image/webp";
    case ".gif":
      return "image/gif";
    case ".jpg":
    case ".jpeg":
    default:
      return "image/jpeg";
  }
}

export function buildImageDataUrl(imagePath) {
  const resolvedPath = path.resolve(imagePath);
  if (!fs.existsSync(resolvedPath)) {
    throw new Error(`Image file not found: ${resolvedPath}`);
  }
  const mimeType = guessMimeType(resolvedPath);
  const base64 = fs.readFileSync(resolvedPath).toString("base64");
  return {
    imagePath: resolvedPath,
    mimeType,
    dataUrl: `data:${mimeType};base64,${base64}`,
  };
}

export function buildDeckPhotoAnalysisPrompt({
  prompt = null,
  expectedLayout = null,
} = {}) {
  if (prompt) {
    return prompt;
  }

  const expectedLayoutText =
    expectedLayout && Object.keys(expectedLayout).length > 0
      ? `\n预期布局: ${JSON.stringify(expectedLayout, null, 2)}`
      : "";

  return [
    "你在分析一张 Opentrons Flex 实验台照片。",
    "只做 deck-level 判断，不要臆测孔内液体体积。",
    "请输出严格 JSON，字段为:",
    "{",
    '  "summary": "一句话总结",',
    '  "observed_items": [{"slot":"C2","label":"tiprack","confidence":0.0,"evidence":"..."}],',
    '  "possible_issues": ["..."],',
    '  "uncertainties": ["..."],',
    '  "recommended_next_actions": ["..."],',
    '  "needs_human_review": false',
    "}",
    expectedLayoutText,
  ].join("\n");
}

export function buildSiliconFlowChatBody({
  model = "Pro/moonshotai/Kimi-K2.5",
  imageDataUrl,
  prompt,
  detail = "high",
  systemPrompt = null,
  temperature = 0.1,
  maxTokens = 1200,
  jsonMode = true,
} = {}) {
  if (!imageDataUrl) {
    throw new Error("imageDataUrl is required.");
  }
  if (!prompt) {
    throw new Error("prompt is required.");
  }

  const messages = [];
  if (systemPrompt) {
    messages.push({
      role: "system",
      content: systemPrompt,
    });
  }
  messages.push({
    role: "user",
    content: [
      {
        type: "image_url",
        image_url: {
          url: imageDataUrl,
          detail,
        },
      },
      {
        type: "text",
        text: prompt,
      },
    ],
  });

  return {
    model,
    messages,
    temperature,
    max_tokens: maxTokens,
    ...(jsonMode
      ? {
          response_format: {
            type: "json_object",
          },
        }
      : {}),
  };
}

export function extractAssistantText(responseJson) {
  const content = responseJson?.choices?.[0]?.message?.content ?? null;
  if (typeof content === "string") {
    return content;
  }
  if (Array.isArray(content)) {
    return content
      .map(item => (typeof item === "string" ? item : item?.text || ""))
      .filter(Boolean)
      .join("\n");
  }
  return null;
}

export function parseAssistantJson(text) {
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    const fenced = text.match(/```json\s*([\s\S]*?)\s*```/i);
    if (fenced?.[1]) {
      try {
        return JSON.parse(fenced[1]);
      } catch {
        // continue
      }
    }
    const objectLike = text.match(/\{[\s\S]*\}/);
    if (objectLike?.[0]) {
      try {
        return JSON.parse(objectLike[0]);
      } catch {
        return null;
      }
    }
    return null;
  }
}

export function resolveSiliconFlowApiKey({ apiKey = null, envVarName = "SILICONFLOW_API_KEY" } = {}) {
  return apiKey || process.env[envVarName] || null;
}

export async function callSiliconFlowChatCompletion({
  apiKey,
  baseUrl = "https://api.siliconflow.cn/v1",
  body,
} = {}) {
  if (!apiKey) {
    throw new Error("SiliconFlow API key is required. Pass api_key or set SILICONFLOW_API_KEY.");
  }
  const url = `${String(baseUrl).replace(/\/$/, "")}/chat/completions`;
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
      `SiliconFlow request failed: ${response.status} ${response.statusText}${
        responseText ? ` - ${responseText}` : ""
      }`,
    );
  }

  return {
    json: responseJson,
    traceId: response.headers.get("x-siliconcloud-trace-id") || null,
  };
}
