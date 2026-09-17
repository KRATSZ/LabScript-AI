export interface SlotRect {
  x: number;
  y: number;
  w: number;
  h: number;
  cx: number;
  cy: number;
}

export interface AxisTick {
  label: string;
  x: number;
  y: number;
}

export interface FlexTickLayout {
  rows: AxisTick[];
  cols: AxisTick[];
}

const ROW_LETTERS = ["A", "B", "C", "D"] as const;
const COL_NUMBERS = ["1", "2", "3"] as const;

function asSlot(x: number, y: number, w: number, h: number): SlotRect {
  return { x, y, w, h, cx: x + w / 2, cy: y + h / 2 };
}

/** Group similarly-sized deck slots into 4 rows (A back/top → D front/bottom). */
export function ticksFromSlotRects(raw: Array<{ x: number; y: number; w: number; h: number }>): FlexTickLayout | null {
  const sized = raw.filter((item) => item.w > 24 && item.h > 24).map((item) => asSlot(item.x, item.y, item.w, item.h));
  if (sized.length < 12) return null;
  const medianH = [...sized].sort((a, b) => a.h - b.h)[Math.floor(sized.length / 2)]?.h || 80;
  const main = sized.filter((item) => item.h > medianH * 0.55 && item.h < medianH * 1.55);
  const tol = medianH * 0.45;
  const sorted = [...main].sort((a, b) => a.cy - b.cy);
  const bands: SlotRect[][] = [];
  for (const slot of sorted) {
    const last = bands[bands.length - 1];
    if (!last || Math.abs(last[0].cy - slot.cy) > tol) bands.push([slot]);
    else last.push(slot);
  }
  // A1 expansion pad is a fifth band with 1–2 cells above row A.
  const rows = bands.filter((band) => band.length >= 3).slice(0, 4);
  if (rows.length < 4) return null;
  const rowTicks: AxisTick[] = rows.map((band, index) => {
    const left = Math.min(...band.map((slot) => slot.x));
    const cy = band.reduce((sum, slot) => sum + slot.cy, 0) / band.length;
    return { label: ROW_LETTERS[index], x: left - 16, y: cy };
  });
  const cols: AxisTick[] = [];
  for (let index = 0; index < COL_NUMBERS.length; index++) {
    const cells = rows
      .map((band) => [...band].sort((a, b) => a.cx - b.cx)[index])
      .filter((slot): slot is SlotRect => Boolean(slot));
    if (!cells.length) continue;
    const cx = cells.reduce((sum, slot) => sum + slot.cx, 0) / cells.length;
    const bottom = Math.max(...cells.map((slot) => slot.y + slot.h));
    cols.push({ label: COL_NUMBERS[index], x: cx, y: bottom + 14 });
  }
  if (cols.length < 3) return null;
  return { rows: rowTicks, cols };
}

export function readFlexTicks(host: HTMLElement): FlexTickLayout | null {
  const box = host.getBoundingClientRect();
  const rects = [...host.querySelectorAll('[data-testid="slot-base"]')].map((node) => {
    const r = node.getBoundingClientRect();
    return { x: r.left - box.left, y: r.top - box.top, w: r.width, h: r.height };
  });
  return ticksFromSlotRects(rects);
}
