import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  DEVICE_REGISTRY,
  HARDWARE_PRESETS,
  PRESET_ROBOT,
  ROBOT_PRESET,
  deviceFor,
  deviceForId,
  knownHamiltonWellUl,
  knownOpentronsWellUl,
  knownTecanWellUl,
  assumedCapacityLine,
  OT2_STANDARD_TIP_UL,
  FLEX_STANDARD_TIP_UL,
  TECAN_STANDARD_TIP_UL,
  type DeviceProfile,
} from "../server/src/devices.ts";
import { inferRobotFromText, isRobotModel, planBackendFor } from "../server/src/session.ts";

const REQUIRED: Array<keyof DeviceProfile> = [
  "id",
  "label",
  "aliases",
  "legacyRobot",
  "codegen",
  "planBackend",
  "checks",
  "animation",
  "artifactExt",
  "hardwarePreset",
];

const IDS = ["ot2", "flex", "hamilton_star", "tecan_fluent"] as const;

describe("device registry", () => {
  it("has exactly four cards with complete fields", () => {
    assert.equal(DEVICE_REGISTRY.length, 4);
    assert.deepEqual(
      DEVICE_REGISTRY.map((d) => d.id),
      [...IDS]
    );
    for (const device of DEVICE_REGISTRY) {
      for (const key of REQUIRED) {
        assert.notEqual(device[key], undefined, `${device.id} missing ${key}`);
      }
      assert.ok(Array.isArray(device.aliases) && device.aliases.length > 0);
      assert.ok(device.aliases.every((re) => re instanceof RegExp));
      assert.ok(Array.isArray(device.checks) && device.checks.length > 0);
      assert.ok(device.hardwarePreset.id);
      assert.ok(device.hardwarePreset.leftPipette);
      assert.ok(device.hardwarePreset.deck);
      assert.equal(typeof device.animation, "boolean");
      assert.match(device.artifactExt, /^\.(py|json|gwl)$/);
      assert.equal(device.hardwarePreset.id, ROBOT_PRESET[device.legacyRobot]);
      assert.equal(PRESET_ROBOT[device.hardwarePreset.id as keyof typeof PRESET_ROBOT], device.legacyRobot);
    }
  });

  it("deviceFor and deviceForId map legacy robots and ids", () => {
    assert.equal(deviceFor("OT-2")?.id, "ot2");
    assert.equal(deviceFor("ot2")?.id, "ot2");
    assert.equal(deviceForId("ot2")?.legacyRobot, "OT-2");
    assert.equal(deviceFor("Flex")?.id, "flex");
    assert.equal(deviceFor("flex")?.id, "flex");
    assert.equal(deviceFor("Hamilton")?.id, "hamilton_star");
    assert.equal(deviceForId("hamilton_star")?.label, "Hamilton STAR");
    assert.equal(deviceFor("Tecan")?.id, "tecan_fluent");
    assert.equal(deviceFor("tecan_fluent")?.label, "Tecan Fluent");
    assert.equal(deviceFor(undefined), undefined);
    assert.equal(deviceFor(""), undefined);
    assert.equal(deviceFor("nope"), undefined);
    assert.equal(deviceForId("missing"), undefined);
    assert.equal(deviceFor("ot2"), deviceForId("ot2"));
  });

  it("OT-2 and Flex generate Python with animation; Hamilton and Fluent use Plan IR", () => {
    const ot2 = deviceForId("ot2")!;
    const flex = deviceForId("flex")!;
    const ham = deviceForId("hamilton_star")!;
    const fluent = deviceForId("tecan_fluent")!;
    for (const d of [ot2, flex]) {
      assert.equal(d.codegen, "opentrons_python");
      assert.equal(d.planBackend, "serializing");
      assert.equal(d.animation, true);
      assert.equal(d.artifactExt, ".py");
      assert.deepEqual(d.checks, ["opentrons_sim", "logicpass", "llmreview"]);
    }
    assert.equal(ham.codegen, "plan_ir");
    assert.equal(ham.planBackend, "hamilton");
    assert.equal(ham.animation, false);
    assert.equal(ham.artifactExt, ".py");
    assert.deepEqual(ham.checks, ["virtual_deck", "plr_sim"]);
    assert.equal(fluent.codegen, "plan_ir");
    assert.equal(fluent.planBackend, "tecan_evo");
    assert.equal(fluent.animation, false);
    assert.equal(fluent.artifactExt, ".gwl");
    assert.deepEqual(fluent.checks, ["virtual_deck", "plr_sim", "pyfluent_compile"]);
    assert.equal(fluent.label, "Tecan Fluent");
    assert.equal(fluent.note, undefined);
  });

  it("hardware presets match the moved OT-2 / Flex / Hamilton / Tecan decks", () => {
    assert.deepEqual(Object.keys(HARDWARE_PRESETS), [
      "ot2_p300_standard3",
      "flex_1000_standard3",
      "hamilton_star_standard",
      "tecan_evo_standard",
    ]);
    assert.equal(HARDWARE_PRESETS.ot2_p300_standard3.leftPipette, "p300_single_gen2");
    assert.equal(HARDWARE_PRESETS.ot2_p300_standard3.deck["1"], "opentrons_96_tiprack_300ul");
    assert.equal(HARDWARE_PRESETS.flex_1000_standard3.deck.A3, "trash_bin");
    assert.equal(HARDWARE_PRESETS.hamilton_star_standard.deck["1"], "hamilton_96_tiprack_300ul");
    assert.equal(HARDWARE_PRESETS.hamilton_star_standard.deck["2"], "corning_96_wellplate_360ul_flat");
    assert.equal(knownHamiltonWellUl("corning_96_wellplate_360ul_flat"), 360);
    assert.equal(knownHamiltonWellUl("nest_12_reservoir_15ml"), 15_000);
    assert.equal(knownHamiltonWellUl("hamilton_96_tiprack_300ul"), undefined);
    assert.equal(knownHamiltonWellUl("opentrons_96_wellplate_200ul_flat"), undefined);
    assert.equal(knownHamiltonWellUl("mystery_plate"), undefined);
    assert.equal(HARDWARE_PRESETS.tecan_evo_standard.deck["1"], "tecan_diti_200ul_tiprack");
    assert.equal(HARDWARE_PRESETS.tecan_evo_standard.leftPipette, "liha_1000");
    assert.equal(knownTecanWellUl("tecan_96_wellplate"), 360);
    assert.equal(knownTecanWellUl("nest_12_reservoir_15ml"), 15_000);
    assert.equal(knownTecanWellUl("TECAN_96_WELLPLATE"), 360);
    assert.equal(TECAN_STANDARD_TIP_UL, 1000);
    assert.equal(knownTecanWellUl("tecan_diti_200ul_tiprack"), undefined);
    assert.equal(knownTecanWellUl("corning_96_wellplate_360ul_flat"), undefined);
    assert.equal(knownTecanWellUl("mystery_plate"), undefined);
    assert.match(assumedCapacityLine("OT-2"), /plate wells hold 200 µL, tips 300 µL/);
    assert.match(assumedCapacityLine("Flex"), /plate wells hold 200 µL, tips 1000 µL/);
    assert.match(assumedCapacityLine("Hamilton"), /plate wells hold 360 µL, tips 300 µL/);
    assert.match(assumedCapacityLine("Tecan"), /plate wells hold 360 µL, tips 1000 µL/);
    assert.equal(knownOpentronsWellUl("nest_96_wellplate_200ul_flat"), 200);
    assert.equal(OT2_STANDARD_TIP_UL, 300);
    assert.equal(FLEX_STANDARD_TIP_UL, 1000);
  });

  it("aliases infer exactly one legacy robot, same as before", () => {
    assert.equal(inferRobotFromText("Hamilton STAR: transfer 50 µL A1 to B1"), "Hamilton");
    assert.equal(inferRobotFromText("ot2 transfer"), "OT-2");
    assert.equal(inferRobotFromText("OT-2 PCR"), "OT-2");
    assert.equal(inferRobotFromText("Flex protocol"), "Flex");
    assert.equal(inferRobotFromText("Tecan Freedom EVO"), "Tecan");
    assert.equal(inferRobotFromText("Tecan Fluent protocol"), "Tecan");
    assert.equal(inferRobotFromText("PCR setup"), undefined);
    assert.equal(inferRobotFromText("common deck on OT-2, Flex, Hamilton, or Tecan"), undefined);
    assert.equal(isRobotModel("OT-2"), true);
    assert.equal(isRobotModel("ot2"), false);
    assert.equal(isRobotModel("Tecan Fluent"), false);
    assert.equal(planBackendFor("Hamilton"), "hamilton");
    assert.equal(planBackendFor("Tecan"), "tecan_evo");
    assert.equal(planBackendFor("OT-2"), "serializing");
    assert.equal(planBackendFor("Flex"), "serializing");
    assert.equal(planBackendFor(undefined), "auto");
  });
});
