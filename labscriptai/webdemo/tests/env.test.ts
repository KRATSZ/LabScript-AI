import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  DEFAULT_DEEPSEEK_MODEL,
  DEFAULT_DEEPSEEK_ORIGIN,
  normalizeDeepseekBaseUrl,
} from "../server/src/env.ts";

describe("DeepSeek demo env", () => {
  it("defaults the live chat model to deepseek-flash", () => {
    assert.equal(DEFAULT_DEEPSEEK_MODEL, "deepseek-flash");
  });

  it("normalizes origin, trailing slash, and /v1 for /chat/completions", () => {
    assert.equal(normalizeDeepseekBaseUrl(undefined), DEFAULT_DEEPSEEK_ORIGIN);
    assert.equal(normalizeDeepseekBaseUrl(""), DEFAULT_DEEPSEEK_ORIGIN);
    assert.equal(normalizeDeepseekBaseUrl("https://api.deepseek.com/"), DEFAULT_DEEPSEEK_ORIGIN);
    assert.equal(normalizeDeepseekBaseUrl("https://api.deepseek.com/v1"), DEFAULT_DEEPSEEK_ORIGIN);
    assert.equal(normalizeDeepseekBaseUrl("https://api.deepseek.com/v1/"), DEFAULT_DEEPSEEK_ORIGIN);
  });
});
