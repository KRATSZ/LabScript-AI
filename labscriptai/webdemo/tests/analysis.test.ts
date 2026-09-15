import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  analysisResetKey,
  isPlayableAnalyze,
  padAnalysisForAnimator,
  safeNormalizeAnalysis,
  sessionCanWatch,
  watchUnavailableCopy,
} from "../web/src/analysis.ts";

describe("isPlayableAnalyze", () => {
  it("rejects missing or empty analysis", () => {
    assert.equal(isPlayableAnalyze(null), false);
    assert.equal(isPlayableAnalyze({}), false);
    assert.equal(isPlayableAnalyze({ commands: [] }), false);
  });

  it("accepts analysis that already has commands", () => {
    assert.equal(isPlayableAnalyze({ commands: [{ commandType: "home" }] }), true);
  });
});

describe("sessionCanWatch", () => {
  const cmds = { commands: [{ commandType: "home" }] };

  it("lights only OT-2/Flex with pass and commands", () => {
    assert.equal(sessionCanWatch("OT-2", "pass", cmds), true);
    assert.equal(sessionCanWatch("Flex", "pass", cmds), true);
    assert.equal(sessionCanWatch("Hamilton", "pass", cmds), false);
    assert.equal(sessionCanWatch("Tecan", "pass", cmds), false);
    assert.equal(sessionCanWatch("OT-2", "fail", cmds), false);
    assert.equal(sessionCanWatch("OT-2", "unevaluable", cmds), false);
    assert.equal(sessionCanWatch("OT-2", "pass", null), false);
  });
});

describe("watchUnavailableCopy", () => {
  const cmds = { commands: [{ commandType: "home" }] };

  it("explains 8010 down for OT devices and stays quiet for Hamilton", () => {
    assert.match(
      watchUnavailableCopy("OT-2", "down", null, null) ?? "",
      /8010/
    );
    assert.equal(watchUnavailableCopy("Hamilton", "down", "pass", cmds), null);
    assert.equal(watchUnavailableCopy("OT-2", "up", "pass", cmds), null);
    assert.match(
      watchUnavailableCopy("Flex", "up", "pass", null) ?? "",
      /analyze commands/
    );
  });
});

describe("safeNormalizeAnalysis", () => {
  it("returns null when normalize throws", () => {
    assert.equal(
      safeNormalizeAnalysis({ commands: [{ commandType: "home" }] }, () => {
        throw new Error("bad analysis");
      }),
      null
    );
  });

  it("pads then returns the normalized value when playable", () => {
    const src = { commands: [{ commandType: "home" }] };
    const out = safeNormalizeAnalysis(src, (input) => input);
    assert.ok(out);
    assert.equal(out.robotType, "OT-2 Standard");
    assert.deepEqual(out.config, { protocolType: "python", apiVersion: [2, 15] });
    assert.deepEqual(out.commands, src.commands);
  });
});

describe("padAnalysisForAnimator", () => {
  it("fills config, createdAt, and OT-2 robotType when omitted", () => {
    const padded = padAnalysisForAnimator({
      commands: [{ commandType: "home", createdAt: "2022-04-01T15:46:01.695210+00:00" }],
    });
    assert.equal(padded.robotType, "OT-2 Standard");
    assert.equal(padded.createdAt, "2022-04-01T15:46:01.695210+00:00");
    assert.deepEqual(padded.config, { protocolType: "python", apiVersion: [2, 15] });
  });

  it("keeps Flex robotType and existing config", () => {
    const config = { protocolType: "json", schemaVersion: 8 };
    const padded = padAnalysisForAnimator({
      commands: [{ commandType: "home" }],
      robotType: "OT-3 Standard",
      createdAt: "2024-01-01T00:00:00.000Z",
      config,
    });
    assert.equal(padded.robotType, "OT-3 Standard");
    assert.equal(padded.createdAt, "2024-01-01T00:00:00.000Z");
    assert.equal(padded.config, config);
  });

  it("maps a Flex hint without robotType to OT-3 Standard", () => {
    const padded = padAnalysisForAnimator({
      commands: [{ commandType: "home" }],
      robot: "Flex",
    });
    assert.equal(padded.robotType, "OT-3 Standard");
  });

  it("uses the session robot hint when analyze omits robotType", () => {
    assert.equal(
      padAnalysisForAnimator({ commands: [{ commandType: "home" }] }, "Flex").robotType,
      "OT-3 Standard"
    );
    assert.equal(
      padAnalysisForAnimator({ commands: [{ commandType: "home" }] }, "OT-2").robotType,
      "OT-2 Standard"
    );
  });

  it("rewrites dropTip on trash to dropTipInPlace, keeps tiprack dropTip", () => {
    const padded = padAnalysisForAnimator({
      labware: [
        { id: "trash", loadName: "opentrons_1_trash_1100ml_fixed" },
        { id: "tips", loadName: "opentrons_96_tiprack_300ul" },
        { id: "custom", isTiprack: true, loadName: "acme_96_tips" },
        { id: "plate", loadName: "corning_96_wellplate_360ul_flat" },
      ],
      commands: [
        { commandType: "dropTip", params: { pipetteId: "p", labwareId: "trash", wellName: "A1" } },
        { commandType: "dropTip", params: { pipetteId: "p", labwareId: "tips", wellName: "A1" } },
        { commandType: "dropTip", params: { pipetteId: "p", labwareId: "custom", wellName: "A1" } },
        { commandType: "dropTip", params: { pipetteId: "p", labwareId: "plate", wellName: "A1" } },
      ],
    });
    const cmds = padded.commands as Array<Record<string, unknown>>;
    assert.equal(cmds[0].commandType, "dropTipInPlace");
    assert.deepEqual(cmds[0].params, { pipetteId: "p" });
    assert.equal(cmds[1].commandType, "dropTip");
    assert.equal(cmds[2].commandType, "dropTip");
    assert.equal(cmds[3].commandType, "dropTipInPlace");
  });
});

describe("analysisResetKey", () => {
  it("changes when createdAt or command count changes", () => {
    assert.equal(analysisResetKey(null), "none");
    assert.notEqual(
      analysisResetKey({ createdAt: "a", commands: [1] }),
      analysisResetKey({ createdAt: "b", commands: [1] })
    );
    assert.notEqual(
      analysisResetKey({ createdAt: "a", commands: [1] }),
      analysisResetKey({ createdAt: "a", commands: [1, 2] })
    );
  });
});
