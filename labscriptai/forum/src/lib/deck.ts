import { labwareKind, labwareLabel, type LabwareKind } from "./labware.ts";

export type DeckShape = "ot2" | "hamilton_star" | "tecan_fluent";

export interface OccupiedSlot {
	slot: string;
	labware: string;
}

export interface DeckCell {
	id: string;
	label: string;
	empty: boolean;
	kind?: LabwareKind | "trash";
	labwareLabel?: string;
}

export interface DeckLayout {
	shape: DeckShape;
	caption: string;
	columns: number;
	cells: DeckCell[];
}

const OT2_ORDER = ["10", "11", "trash", "7", "8", "9", "4", "5", "6", "1", "2", "3"];
const STAR_TRACKS = Array.from({ length: 12 }, (_, i) => String(i + 1));
const FLUENT_SITES = Array.from({ length: 18 }, (_, i) => String(i + 1));

export function deckShape(device: string): DeckShape {
	const d = device.toLowerCase();
	if (/\bhamilton\b/.test(d)) return "hamilton_star";
	if (/\btecan\b|\bfluent\b/.test(d)) return "tecan_fluent";
	return "ot2";
}

function fill(ids: string[], occupied: OccupiedSlot[]): DeckCell[] {
	const bySlot = new Map(occupied.map((row) => [row.slot.toLowerCase(), row]));
	return ids.map((id) => {
		const hit = bySlot.get(id.toLowerCase());
		if (id === "trash") {
			return { id, label: "trash", empty: true, kind: "trash" };
		}
		if (!hit) return { id, label: id, empty: true };
		return {
			id,
			label: id,
			empty: false,
			kind: labwareKind(hit.labware),
			labwareLabel: labwareLabel(hit.labware),
		};
	});
}

export function layoutFor(device: string, occupied: OccupiedSlot[]): DeckLayout {
	const shape = deckShape(device);
	if (shape === "hamilton_star") {
		return {
			shape,
			caption: "Hamilton STAR · tracks 1–12, front rail",
			columns: 12,
			cells: fill(STAR_TRACKS, occupied),
		};
	}
	if (shape === "tecan_fluent") {
		return {
			shape,
			caption: "Tecan Fluent · 18-site worktable",
			columns: 6,
			cells: fill(FLUENT_SITES, occupied),
		};
	}
	return {
		shape: "ot2",
		caption: "OT-2 · 11 slots + trash, viewed from the front",
		columns: 3,
		cells: fill(OT2_ORDER, occupied),
	};
}
