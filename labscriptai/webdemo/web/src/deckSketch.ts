import type { RobotModel } from "./types";

const OT2_ROWS: string[][] = [
  ["10", "11", "trash"],
  ["7", "8", "9"],
  ["4", "5", "6"],
  ["1", "2", "3"],
];

/** Flex: letters are rows (A back / top → D front / bottom), numbers are columns (1 left → 3 right). A1 is back-left. */
const FLEX_ROWS: string[][] = [
  ["A1", "A2", "A3"],
  ["B1", "B2", "B3"],
  ["C1", "C2", "C3"],
  ["D1", "D2", "D3"],
];

export interface DeckSketchAxes {
  rows: string[];
  cols: string[];
}

/** Slot grid for the waiting-panel sketch. Empty slots stay numbered so the bench is readable. */
export function deckSketchRows(
  robot: RobotModel | null | undefined,
  deck: Record<string, string>
): string[][] {
  if (robot === "Flex") return FLEX_ROWS;
  if (robot === "OT-2") return OT2_ROWS;
  const slots = Object.keys(deck);
  if (!slots.length) return [["1", "2", "3"]];
  const rows: string[][] = [];
  for (let i = 0; i < slots.length; i += 3) rows.push(slots.slice(i, i + 3));
  return rows;
}

/** Axis labels matching labscriptai.cn/animation: letters down the left, numbers along the bottom. */
export function deckSketchAxes(robot: RobotModel | null | undefined): DeckSketchAxes | null {
  if (robot === "Flex") return { rows: ["A", "B", "C", "D"], cols: ["1", "2", "3"] };
  return null;
}

export interface StarCarrierSite {
  id: string;
  label: string;
  labware: string;
}

export interface StarCarrierSketch {
  id: string;
  title: string;
  rails: string;
  sites: StarCarrierSite[];
}

/** PLR STARDeck: tip carrier (5) · plate carrier (5) · trough · built-in waste. */
export function hamiltonStarSketch(deck: Record<string, string>): StarCarrierSketch[] {
  const tips = deckLabware(deck, "1");
  const plate = deckLabware(deck, "2");
  const trough = deckLabware(deck, "3");
  const sites = (id: string, count: number, labwareAt: (index: number) => string): StarCarrierSite[] =>
    Array.from({ length: count }, (_, index) => ({
      id: `${id}-${index}`,
      label: `Site ${index + 1}`,
      labware: labwareAt(index),
    }));
  return [
    { id: "tip_car", title: "Tip carrier", rails: "1–6", sites: sites("tip", 5, () => tips) },
    { id: "plate_car", title: "Plate carrier", rails: "8–13", sites: sites("plt", 5, (index) => (index === 0 ? plate : "")) },
    {
      id: "trough",
      title: "Reagents",
      rails: "15",
      sites: [{ id: "trough", label: "Trough", labware: trough }],
    },
    {
      id: "waste",
      title: "Waste",
      rails: "built-in",
      sites: [
        { id: "trash", label: "Trash", labware: "" },
        { id: "core96", label: "96-head", labware: "" },
        { id: "teach", label: "Teaching rack", labware: "" },
      ],
    },
  ];
}

export function usesStarSketch(robot: RobotModel | null | undefined): boolean {
  return robot === "Hamilton";
}

export function slotKey(slot: string): string {
  return slot.trim().toLowerCase();
}

export function deckLabware(deck: Record<string, string>, slot: string): string {
  const want = slotKey(slot);
  for (const [key, value] of Object.entries(deck)) {
    if (slotKey(key) === want) return value;
  }
  return "";
}

/** Top-left cell of the sketch — Flex A1 (back-left) or OT-2 slot 10. */
export function sketchOriginSlot(robot: RobotModel | null | undefined): string {
  const rows = deckSketchRows(robot, {});
  return rows[0]?.[0] ?? "";
}
