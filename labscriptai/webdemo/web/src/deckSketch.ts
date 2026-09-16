import type { RobotModel } from "./types";

const OT2_ROWS: string[][] = [
  ["10", "11", "trash"],
  ["7", "8", "9"],
  ["4", "5", "6"],
  ["1", "2", "3"],
];

const FLEX_ROWS: string[][] = [
  ["A3", "B3", "C3", "D3"],
  ["A2", "B2", "C2", "D2"],
  ["A1", "B1", "C1", "D1"],
];

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
