import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { parseUiLang, t } from "../web/src/i18n.ts";

describe("ui language", () => {
  it("parses Chinese aliases", () => {
    assert.equal(parseUiLang("zh"), "zh");
    assert.equal(parseUiLang("中文"), "zh");
    assert.equal(parseUiLang("en"), "en");
    assert.equal(parseUiLang("nope"), "en");
  });

  it("translates chrome while keeping English keys", () => {
    assert.equal(t("Change robot", "en"), "Change robot");
    assert.equal(t("Change robot", "zh"), "更换仪器");
    assert.equal(t("Protocol summary", "zh"), "方案摘要");
    assert.equal(t("On-screen preview only", "zh"), "仅屏幕预览");
    assert.equal(t("Ready to watch", "zh"), "可以观看");
    assert.equal(t("Unknown string", "zh"), "Unknown string");
  });
});
