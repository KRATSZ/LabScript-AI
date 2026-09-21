import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { protocolSummary } from "../web/src/protocolSummary.ts";
import type { SessionSnapshot } from "../web/src/types.ts";

function snap(over: Partial<SessionSnapshot> = {}): SessionSnapshot {
  return {
    id: "s",
    phase: "ready",
    missing: [],
    goal: "Prepare a PCR mix",
    doc: "none",
    robot: "OT-2",
    hardware: {
      leftPipette: "p300_single_gen2",
      rightPipette: "None",
      deck: {
        "1": "opentrons_96_tiprack_300ul",
        "2": "nest_96_wellplate_100ul_pcr_full_skirt",
        "3": "nest_12_reservoir_15ml",
      },
    },
    hardware_config: "",
    sop: "# PCR mix",
    code: "",
    plan: {
      steps: [
        { step_id: "1", primitive_type: "PICK_TIPS" },
        { step_id: "2", primitive_type: "ASPIRATE", volume_ul: 20 },
      ],
    },
    analyze: null,
    checks: null,
    fab: { lit: false },
    ...over,
  };
}

describe("protocolSummary", () => {
  it("lists consumables, pipettes, and approximate steps", () => {
    const model = protocolSummary(snap());
    assert.ok(model);
    assert.match(model.approx, /2/);
    assert.ok(model.pipettes.includes("p300_single_gen2"));
    assert.ok(model.consumables.some((item) => /PCR plate/i.test(item.name) || item.role === "PCR plate"));
    assert.ok(model.consumables.some((item) => item.role === "tips"));
  });

  it("dedupes the same consumable from deck and analyze", () => {
    const model = protocolSummary(
      snap({
        analyze: {
          labware: [
            { loadName: "opentrons_96_tiprack_300ul" },
            { loadName: "nest_96_wellplate_100ul_pcr_full_skirt" },
            { loadName: "nest_12_reservoir_15ml" },
          ],
        },
      })
    );
    assert.ok(model);
    const tips = model.consumables.filter((item) => item.role === "tips");
    const plates = model.consumables.filter((item) => item.role === "PCR plate");
    const reservoirs = model.consumables.filter((item) => item.role === "reservoir");
    assert.equal(tips.length, 1);
    assert.equal(plates.length, 1);
    assert.equal(reservoirs.length, 1);
    assert.equal(tips[0]?.slot, "1");
  });

  it("returns null when the session is empty", () => {
    assert.equal(
      protocolSummary(
        snap({
          goal: "",
          sop: "",
          plan: null,
          hardware: { deck: {} },
        })
      ),
      null
    );
  });
});
