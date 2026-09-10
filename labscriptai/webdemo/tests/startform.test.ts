import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { DEVICE_REGISTRY } from "../server/src/devices.ts";
import { DEVICE_CARDS, canStart, matchDeviceFromText } from "../web/src/devices.ts";
import { EXAMPLES } from "../web/src/startExamples.ts";

const webSrc = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../web/src");
const readWeb = (name: string) => readFileSync(path.join(webSrc, name), "utf8");

describe("StartForm examples", () => {
  it("three chips fill goal and optional notes, and do not imply auto-submit", () => {
    assert.equal(EXAMPLES.length, 3);
    assert.equal(EXAMPLES[0].label, "Transfer 50 µL A1→B1");
    assert.equal(EXAMPLES[0].goal, "Transfer 50 µL from well A1 to B1 on a 96-well plate.");
    assert.equal(EXAMPLES[0].doc, "");
    assert.equal(EXAMPLES[1].label, "Prepare a PCR mix");
    assert.match(EXAMPLES[1].goal, /PCR mix/);
    assert.match(EXAMPLES[1].doc, /master mix/);
    assert.equal(EXAMPLES[2].label, "No protocol — common deck");
    assert.match(EXAMPLES[2].goal, /common deck/);
    const blob = EXAMPLES.map((item) => `${item.label}\n${item.goal}\n${item.doc}`).join("\n");
    assert.doesNotMatch(blob, /standard3|standard 3-slot/i);
    assert.match(EXAMPLES[2].goal, /Hamilton/);
    assert.match(EXAMPLES[2].goal, /Tecan/);
  });
});

describe("StartForm device cards", () => {
  it("mirrors registry ids/labels/legacyRobot/animation and has capability copy", () => {
    assert.equal(DEVICE_CARDS.length, DEVICE_REGISTRY.length);
    assert.deepEqual(
      DEVICE_CARDS.map((c) => c.id),
      DEVICE_REGISTRY.map((d) => d.id)
    );
    for (let i = 0; i < DEVICE_CARDS.length; i++) {
      const card = DEVICE_CARDS[i];
      const device = DEVICE_REGISTRY[i];
      assert.equal(card.label, device.label);
      assert.equal(card.legacyRobot, device.legacyRobot);
      assert.equal(card.animation, device.animation);
      assert.equal(card.codegen, device.codegen);
      assert.ok(card.blurb.trim());
      if (!card.animation) assert.doesNotMatch(card.blurb, /animat/i);
    }
    assert.equal(DEVICE_CARDS[0].blurb, "Python script + simulation + animation");
    assert.equal(DEVICE_CARDS[1].blurb, "Python script + simulation + animation");
    assert.equal(DEVICE_CARDS[2].blurb, "Step table today — STAR script later");
    assert.equal(DEVICE_CARDS[3].blurb, "Tecan Fluent .gwl worklist");
  });

  it("Start requires a selected device and a goal", () => {
    assert.equal(canStart("", "ot2"), false);
    assert.equal(canStart("   ", "ot2"), false);
    assert.equal(canStart("transfer", undefined), false);
    assert.equal(canStart("transfer", "nope"), false);
    assert.equal(canStart("transfer", "ot2"), true);
    assert.equal(canStart("  PCR  ", "tecan_fluent"), true);
  });

  it("example chips select a card only when they name exactly one device", () => {
    assert.equal(matchDeviceFromText("Hamilton STAR: transfer 50 µL A1 to B1"), "hamilton_star");
    assert.equal(matchDeviceFromText("Flex PCR mix"), "flex");
    assert.equal(matchDeviceFromText("OT-2: transfer"), "ot2");
    assert.equal(matchDeviceFromText("Tecan Fluent .gwl"), "tecan_fluent");
    assert.equal(matchDeviceFromText("Tecan Freedom EVO"), "tecan_fluent");
    assert.equal(matchDeviceFromText(EXAMPLES[0].goal), undefined);
    assert.equal(matchDeviceFromText(EXAMPLES[1].goal), undefined);
    assert.equal(
      matchDeviceFromText(`${EXAMPLES[2].label}\n${EXAMPLES[2].goal}\n${EXAMPLES[2].doc}`),
      undefined
    );
  });

  it("StartForm renders cards from the registry helper and disables Start until a device is picked", () => {
    const src = readWeb("StartForm.tsx");
    assert.match(src, /DEVICE_CARDS\.map/);
    assert.match(src, /canStart\(goal, deviceId\)/);
    assert.match(src, /matchDeviceFromText/);
    assert.match(src, /Pick a robot first/);
    assert.doesNotMatch(src, /Robot is asked in chat/);
    assert.match(src, /aria-pressed=\{deviceId === card\.id\}/);
    assert.match(readWeb("App.tsx"), /Change device/);
    assert.match(readWeb("types.ts"), /export interface StartInput/);
    assert.match(readWeb("types.ts"), /robot: RobotModel/);
  });
});
