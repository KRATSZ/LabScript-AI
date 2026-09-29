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
    assert.equal(t("Steps not listed yet", "zh"), "步骤尚未列出");
    assert.equal(t("liquid-handling steps", "zh"), "个移液步骤");
    assert.equal(t("tips", "zh"), "枪头");
    assert.equal(t("Trash", "zh"), "废液槽");
    assert.equal(t("300 µL tips", "zh"), "300 µL 枪头");
    assert.equal(t("Unknown string", "zh"), "Unknown string");
    assert.equal(t("Choose file", "zh"), "选择文件");
    assert.equal(t("Aspirate", "zh"), "吸液");
    assert.equal(t("Dispense", "zh"), "放液");
    assert.equal(t("Pick up tip", "zh"), "取枪头");
    assert.equal(t("Cancel", "zh"), "取消");
    assert.equal(t("Retry", "zh"), "重试");
    assert.equal(t("Hamilton STAR", "zh"), "汉密尔顿 STAR");
    assert.equal(t("Human-readable protocol write-up", "zh"), "可读的方案说明");
    assert.match(t("Notes are .md, .txt, .py, or .json. They are notes, not the run.", "zh"), /\.md/);
    assert.equal(t("Transfer 50 µL A1→B1", "zh"), "转移 50 µL A1→B1");
    assert.equal(t("Wrote the protocol", "zh"), "已写方案");
    assert.equal(t("Earlier messages stay in the language they were written in.", "zh"), "此前的消息保持生成时的语言。");
  });
});
