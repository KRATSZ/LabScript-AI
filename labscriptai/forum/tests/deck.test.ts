import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";
import { deckShape, layoutFor } from "../src/lib/deck.ts";

const occupied = [
	{ slot: "1", labware: "opentrons_96_tiprack_300ul" },
	{ slot: "2", labware: "nest_96_wellplate_200ul_flat" },
	{ slot: "3", labware: "nest_12_reservoir_15ml" },
];

describe("robot-shaped decks", () => {
	it("uses different grids for OT-2, STAR, and Fluent", () => {
		const ot2 = layoutFor("OT-2", occupied);
		const star = layoutFor("Hamilton STAR", occupied);
		const fluent = layoutFor("Tecan Fluent", occupied);
		assert.equal(deckShape("OT-2"), "ot2");
		assert.equal(ot2.columns, 3);
		assert.equal(ot2.cells.length, 12);
		assert.equal(star.columns, 12);
		assert.equal(star.cells.length, 12);
		assert.equal(fluent.columns, 6);
		assert.equal(fluent.cells.length, 18);
		assert.notEqual(ot2.columns, star.columns);
		assert.notEqual(star.columns, fluent.columns);
	});

	it("keeps empty slots visible", () => {
		const ot2 = layoutFor("OT-2", occupied);
		assert.equal(ot2.cells.filter((cell) => cell.empty).length, 9);
		assert.ok(ot2.cells.some((cell) => cell.id === "trash"));
		assert.equal(ot2.cells.find((cell) => cell.id === "1")?.empty, false);
		assert.equal(layoutFor("Hamilton STAR", occupied).cells.filter((cell) => cell.empty).length, 9);
		assert.equal(layoutFor("Tecan Fluent", occupied).cells.filter((cell) => cell.empty).length, 15);
	});

	it("does not collapse the map to one column on mobile", () => {
		const css = readFileSync(
			join(dirname(fileURLToPath(import.meta.url)), "../src/components/DeckMap.astro"),
			"utf8",
		);
		assert.equal(/max-width:[^}]*grid-template-columns:\s*1fr/.test(css), false);
	});
});
