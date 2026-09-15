import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { labwareKind, labwareLabel, pipetteLabel } from "../src/lib/labware.ts";

describe("labware labels", () => {
	it("shortens assumed-deck names", () => {
		assert.equal(labwareLabel("opentrons_96_tiprack_300ul"), "300 µL tips");
		assert.equal(labwareLabel("nest_96_wellplate_200ul_flat"), "96-well plate");
		assert.equal(labwareLabel("nest_12_reservoir_15ml"), "reservoir");
		assert.equal(labwareKind("tecan_diti_200ul_tiprack"), "tips");
		assert.equal(labwareKind("corning_96_wellplate_360ul_flat"), "plate");
	});

	it("uses human pipette names", () => {
		assert.equal(pipetteLabel("star_1000"), "STAR 1000 µL");
		assert.equal(pipetteLabel("p300_single_gen2"), "P300 Single GEN2");
		assert.equal(pipetteLabel("liha_1000"), "LiHa 1000 µL");
	});
});
