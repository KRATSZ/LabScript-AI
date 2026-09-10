import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  applyAskUser,
  applyForm,
  applyPreset,
  canEmitPlan,
  canGenerateCode,
  canGenerateSop,
  canRunPipeline,
  checksRoute,
  computePhase,
  createSession,
  enoughHardware,
  formatHardwareConfig,
  inferRobotFromText,
  missingList,
  presetMismatchWarning,
  shouldCallCompactSop,
  shouldReuseSop,
  snapshot,
} from "../server/src/session.ts";
import { refuseEmptySop } from "../server/src/gate.ts";

describe("session machine", () => {
  it("goal-only stays before generate_code", () => {
    const session = createSession();
    session.goal = "transfer 50uL A1 to B1";
    assert.equal(computePhase(session), "need_doc");
    assert.equal(canRunPipeline(session), false);
    assert.equal(canGenerateCode(session), false);
  });

  it("form without robot stays at need_robot", () => {
    const session = createSession();
    applyForm(session, { goal: "PCR setup", doc: "" });
    assert.equal(session.doc, "none");
    assert.equal(session.robot, undefined);
    assert.equal(session.sop, undefined);
    assert.equal(enoughHardware(session), false);
    assert.equal(session.phase, "need_robot");
    assert.deepEqual(missingList(session), ["robot"]);
    assert.equal(canGenerateSop(session), false);
    assert.equal(shouldCallCompactSop(session), false);
    assert.match(formatHardwareConfig(session), /Robot Model: unset/);
    assert.doesNotMatch(formatHardwareConfig(session), /Robot Model: Flex/);
    assert.equal(canGenerateCode(session), false);
  });

  it("form draft becomes session sop so code can run after hardware", () => {
    const session = createSession();
    applyForm(session, {
      goal: "transfer",
      doc: "# SOP\n1. Aspirate A1",
      robot: "Flex",
    });
    assert.equal(session.doc, "# SOP\n1. Aspirate A1");
    assert.equal(session.sop, session.doc);
    assert.equal(session.phase, "ready");
    assert.equal(session.deckAssumed, true);
    assert.equal(canGenerateCode(session), true);
    assert.equal(shouldReuseSop(session), true);
    assert.equal(shouldCallCompactSop(session), false);
    assert.equal(shouldCallCompactSop(session, true), true);
    assert.equal(shouldReuseSop(session, true), false);
  });

  it("enoughHardware still requires pipette, tips, and plate", () => {
    const session = createSession();
    session.goal = "goal";
    session.doc = "none";
    session.robot = "OT-2";
    assert.equal(enoughHardware(session), false);
    session.hardware.leftPipette = "p300_single_gen2";
    assert.equal(enoughHardware(session), false);
    session.hardware.deck["1"] = "opentrons_96_tiprack_300ul";
    assert.equal(enoughHardware(session), false);
    session.hardware.deck["2"] = "nest_96_wellplate_200ul_flat";
    assert.equal(enoughHardware(session), true);
    session.hardware.deck["1"] = "custom_labware";
    assert.equal(enoughHardware(session), false);
    assert.equal(snapshot(session).plan, null);
  });

  it("OT-2 standard3 preset sets robot and makes session ready", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "" });
    assert.equal(session.phase, "need_robot");
    applyAskUser(session, { preset: "ot2_p300_standard3" });
    assert.equal(session.robot, "OT-2");
    assert.equal(enoughHardware(session), true);
    assert.equal(session.phase, "ready");
    assert.equal(session.hardware.leftPipette, "p300_single_gen2");
    assert.equal(session.hardware.deck["1"], "opentrons_96_tiprack_300ul");
    assert.equal(session.deckAssumed, true);
  });

  it("Flex standard3 preset sets robot and includes A3 trash", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "" });
    applyPreset(session, "flex_1000_standard3");
    assert.equal(session.robot, "Flex");
    assert.equal(enoughHardware(session), true);
    assert.equal(session.phase, "ready");
    assert.equal(session.hardware.deck.A1, "opentrons_flex_96_tiprack_1000ul");
    assert.equal(session.hardware.deck.C1, "nest_12_reservoir_15ml");
    assert.equal(session.hardware.deck.A3, "trash_bin");
    assert.equal(session.deckAssumed, true);
  });

  it("ask_user draft seeds sop when sop is empty", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "" });
    assert.equal(session.doc, "none");
    assert.equal(session.sop, undefined);
    applyAskUser(session, { doc: "# SOP\n1. A", preset: "ot2_p300_standard3" });
    assert.equal(session.sop, "# SOP\n1. A");
    assert.equal(canGenerateCode(session), true);
    applyAskUser(session, { doc: "none" });
    assert.equal(session.doc, "none");
    assert.equal(session.sop, "# SOP\n1. A");
    applyAskUser(session, { doc: "# later draft" });
    assert.equal(session.sop, "# SOP\n1. A");
  });

  it("hardware ask_user treats undefined doc as none", () => {
    const session = createSession();
    session.goal = "transfer";
    assert.equal(session.doc, undefined);
    applyAskUser(session, {
      robot: "OT-2",
      left_pipette: "p300_single_gen2",
      deck: [
        { slot: "1", labware: "opentrons_96_tiprack_300ul" },
        { slot: "2", labware: "nest_96_wellplate_200ul_flat" },
      ],
    });
    assert.equal(session.doc, "none");
    assert.equal(session.phase, "ready");
  });

  it("warns on robot/preset mismatch but still applies and sets robot", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", robot: "OT-2" });
    const warning = presetMismatchWarning(session.robot, "flex_1000_standard3");
    applyAskUser(session, { preset: "flex_1000_standard3" });
    assert.equal(session.robot, "Flex");
    assert.equal(session.phase, "ready");
    assert.equal(session.hardware.deck.A3, "trash_bin");
    assert.match(warning ?? "", /flex_1000_standard3/);
    assert.match(warning ?? "", /OT-2/);
    assert.equal(presetMismatchWarning("Flex", "ot2_p300_standard3")?.includes("OT-2"), true);
    assert.equal(presetMismatchWarning("Flex", "flex_1000_standard3"), undefined);
  });

  it("explicit deck after preset overrides that slot", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", robot: "OT-2" });
    applyAskUser(session, {
      preset: "ot2_p300_standard3",
      deck: [{ slot: "2", labware: "corning_96_wellplate_360ul_flat" }],
    });
    assert.equal(session.phase, "ready");
    assert.equal(session.hardware.deck["2"], "corning_96_wellplate_360ul_flat");
    assert.equal(session.hardware.deck["1"], "opentrons_96_tiprack_300ul");
  });

  it("generate_code refuses empty sop even when ready", () => {
    const session = createSession();
    applyForm(session, { goal: "goal", robot: "Flex" });
    applyAskUser(session, {
      left_pipette: "p300_single_gen2",
      deck: [
        { slot: "1", labware: "opentrons_96_tiprack_300ul" },
        { slot: "2", labware: "nest_12_reservoir_15ml" },
      ],
    });
    assert.equal(session.phase, "ready");
    assert.ok(refuseEmptySop(session.sop));
    assert.equal(canGenerateCode(session), false);
  });

  it("OT-2 with Python and a stored plan still routes checks to opentrons", () => {
    assert.equal(
      checksRoute({
        robot: "OT-2",
        code: "from opentrons import protocol_api\ndef run(protocol):\n    protocol.home()\n",
        plan: { steps: [{ step_id: "1" }] },
      }),
      "opentrons"
    );
    assert.equal(checksRoute({ robot: "Flex", code: "def run(p):\n  p.home()\n", plan: {} }), "opentrons");
    assert.equal(checksRoute({ robot: "Hamilton", code: "", plan: { steps: [] } }), "plan");
    assert.equal(checksRoute({ robot: "OT-2", code: "", plan: { steps: [{ step_id: "1" }] } }), "plan");
    assert.equal(checksRoute({ robot: "OT-2", code: "", plan: undefined }), "blocked");
  });

  it("OT-2 ready with SOP can emit_plan", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "ot2_p300_standard3" });
    session.sop = "# SOP\n1. A";
    assert.equal(canGenerateCode(session), true);
    assert.equal(canEmitPlan(session), true);
  });

  it("applyAskUser with Hamilton assumes deck and enables emit_plan", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { robot: "Hamilton" });
    assert.equal(session.robot, "Hamilton");
    assert.equal(session.phase, "ready");
    assert.equal(session.deckAssumed, true);
    assert.equal(canEmitPlan(session), true);
    assert.equal(canGenerateCode(session), false);
    assert.equal(session.hardware.deck["1"], "hamilton_96_tiprack_300ul");
  });

  it("Hamilton preset is ready for Plan IR, not Opentrons Python", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "hamilton_star_standard" });
    assert.equal(session.robot, "Hamilton");
    assert.equal(session.phase, "ready");
    assert.equal(canEmitPlan(session), true);
    assert.equal(canGenerateCode(session), false);
    assert.match(formatHardwareConfig(session), /Plan backend: hamilton/);
  });

  it("Tecan DiTi preset counts as tips", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "# SOP\n1. A" });
    applyAskUser(session, { preset: "tecan_evo_standard" });
    assert.equal(session.robot, "Tecan");
    assert.equal(enoughHardware(session), true);
    assert.equal(canEmitPlan(session), true);
    assert.equal(canGenerateCode(session), false);
    assert.match(formatHardwareConfig(session), /Plan backend: tecan_evo/);
  });

  it("non-Opentrons Plan IR still routes checks to plan", () => {
    assert.equal(checksRoute({ robot: "Hamilton", code: "", plan: { steps: [] } }), "plan");
    assert.equal(checksRoute({ robot: "Tecan", code: "def run(p):\n  pass\n", plan: { steps: [] } }), "plan");
    assert.equal(checksRoute({ robot: "Hamilton", code: "", plan: undefined }), "blocked");
  });

  it("applyAskUser robot Flex assumes standard deck and becomes ready", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "" });
    applyAskUser(session, { robot: "Flex" });
    assert.equal(session.robot, "Flex");
    assert.equal(session.phase, "ready");
    assert.equal(session.hardware.deck.A1, "opentrons_flex_96_tiprack_1000ul");
    assert.equal(session.hardware.deck.D2, "nest_96_wellplate_200ul_flat");
    assert.equal(session.hardware.deck.C1, "nest_12_reservoir_15ml");
    assert.equal(session.hardware.deck.A3, "trash_bin");
    assert.equal(session.hardware.leftPipette, "flex_1channel_1000");
    assert.equal(session.deckAssumed, true);
    assert.equal(snapshot(session).deck_assumed, true);
    assert.equal(snapshot(session).code_service, "down");
  });

  it("applyAskUser robot OT-2 assumes standard deck and becomes ready", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "" });
    applyAskUser(session, { robot: "OT-2" });
    assert.equal(session.robot, "OT-2");
    assert.equal(session.phase, "ready");
    assert.equal(session.hardware.deck["1"], "opentrons_96_tiprack_300ul");
    assert.equal(session.hardware.deck["2"], "nest_96_wellplate_200ul_flat");
    assert.equal(session.hardware.deck["3"], "nest_12_reservoir_15ml");
    assert.equal(session.hardware.leftPipette, "p300_single_gen2");
    assert.equal(session.deckAssumed, true);
    assert.equal(snapshot(session).deck_assumed, true);
  });

  it("explicit deck array keeps user labware and is not assumed", () => {
    const custom = createSession();
    applyForm(custom, { goal: "transfer", doc: "" });
    applyAskUser(custom, {
      robot: "Flex",
      deck: [
        { slot: "D1", labware: "corning_96_wellplate_360ul_flat" },
        { slot: "A2", labware: "opentrons_flex_96_tiprack_1000ul" },
      ],
    });
    assert.equal(custom.deckAssumed, false);
    assert.equal(custom.hardware.deck.D1, "corning_96_wellplate_360ul_flat");
    assert.equal(custom.hardware.deck.A2, "opentrons_flex_96_tiprack_1000ul");
    assert.equal(custom.hardware.deck.A1, undefined);
    assert.equal(custom.hardware.deck.A3, undefined);

    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "" });
    applyAskUser(session, { robot: "Flex" });
    assert.equal(session.deckAssumed, true);
    applyAskUser(session, {
      deck: [{ slot: "D1", labware: "corning_96_wellplate_360ul_flat" }],
    });
    assert.equal(session.deckAssumed, false);
    assert.equal(session.hardware.deck.D1, "corning_96_wellplate_360ul_flat");
    assert.equal(session.hardware.deck.A1, "opentrons_flex_96_tiprack_1000ul");
    assert.equal(session.hardware.deck.A3, "trash_bin");
    assert.equal(snapshot(session).deck_assumed, false);
  });

  it("switching robot on an assumed deck replaces the layout", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "" });
    applyAskUser(session, { robot: "Flex" });
    assert.equal(session.hardware.deck.A1, "opentrons_flex_96_tiprack_1000ul");
    applyAskUser(session, { robot: "OT-2" });
    assert.equal(session.robot, "OT-2");
    assert.equal(session.deckAssumed, true);
    assert.equal(session.hardware.deck.A1, undefined);
    assert.equal(session.hardware.deck["1"], "opentrons_96_tiprack_300ul");
    assert.equal(session.hardware.leftPipette, "p300_single_gen2");
  });

  it("robot switch clears leftover custom slots and generated artifacts", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "" });
    applyAskUser(session, {
      robot: "Flex",
      deck: [
        { slot: "D1", labware: "corning_96_wellplate_360ul_flat" },
        { slot: "A2", labware: "opentrons_flex_96_tiprack_1000ul" },
      ],
    });
    session.sop = "# Flex SOP";
    session.code = "def run(protocol):\n    protocol.home()\n";
    session.plan = { steps: [{ step_id: "1" }] };
    session.analyze = { commands: [{ commandType: "home" }] };
    session.lastChecks = { fab: { lit: true } } as never;
    applyAskUser(session, {
      robot: "OT-2",
      deck: [{ slot: "2", labware: "corning_96_wellplate_360ul_flat" }],
    });
    assert.equal(session.robot, "OT-2");
    assert.equal(session.hardware.deck.A1, undefined);
    assert.equal(session.hardware.deck.D1, undefined);
    assert.equal(session.hardware.deck["2"], "corning_96_wellplate_360ul_flat");
    assert.equal(session.deckAssumed, false);
    assert.equal(session.code, undefined);
    assert.equal(session.plan, undefined);
    assert.equal(session.analyze, undefined);
    assert.equal(session.lastChecks, undefined);
    assert.equal(session.sop, undefined);
  });

  it("mismatched preset then robot still lands on the named robot deck", () => {
    const session = createSession();
    applyForm(session, { goal: "transfer", doc: "" });
    applyAskUser(session, { preset: "flex_1000_standard3", robot: "OT-2" });
    assert.equal(session.robot, "OT-2");
    assert.equal(session.hardware.deck["1"], "opentrons_96_tiprack_300ul");
    assert.equal(session.hardware.deck.A1, undefined);
    assert.equal(session.deckAssumed, true);
  });

  it("inferRobotFromText needs exactly one named robot", () => {
    assert.equal(inferRobotFromText("Hamilton STAR: transfer 50 µL A1 to B1"), "Hamilton");
    assert.equal(inferRobotFromText("ot2 transfer"), "OT-2");
    assert.equal(inferRobotFromText("OT-2 PCR"), "OT-2");
    assert.equal(inferRobotFromText("Flex protocol"), "Flex");
    assert.equal(inferRobotFromText("Tecan Freedom EVO"), "Tecan");
    assert.equal(inferRobotFromText("PCR setup"), undefined);
    assert.equal(
      inferRobotFromText("common deck on OT-2, Flex, Hamilton, or Tecan"),
      undefined
    );
  });

  it("goal that names one robot assumes a deck and skips the robot ask", () => {
    const session = createSession();
    applyForm(session, { goal: "Hamilton STAR: transfer 50 µL A1 to B1", doc: "" });
    assert.equal(session.robot, "Hamilton");
    assert.equal(session.phase, "ready");
    assert.equal(session.deckAssumed, true);
    assert.deepEqual(missingList(session), []);
    assert.equal(canEmitPlan(session), false);
  });

  it("ask_user infers robot from a goal that names one", () => {
    const session = createSession();
    applyAskUser(session, { goal: "Flex: transfer 50 µL A1 to B1" });
    assert.equal(session.robot, "Flex");
    assert.equal(session.doc, "none");
    assert.equal(session.phase, "ready");
    assert.equal(session.deckAssumed, true);
  });
});
