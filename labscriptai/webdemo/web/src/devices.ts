import type { DeviceCard, RobotModel } from "./types";

/** Display cards. Keep ids/labels/legacyRobot/codegen/animation in lockstep with server DEVICE_REGISTRY. */
export const DEVICE_CARDS: DeviceCard[] = [
  {
    id: "ot2",
    label: "OT-2",
    legacyRobot: "OT-2",
    codegen: "opentrons_python",
    animation: true,
    blurb: "On-screen deck",
  },
  {
    id: "flex",
    label: "Flex",
    legacyRobot: "Flex",
    codegen: "opentrons_python",
    animation: true,
    blurb: "On-screen deck",
  },
  {
    id: "hamilton_star",
    label: "Hamilton STAR",
    legacyRobot: "Hamilton",
    codegen: "plan_ir",
    animation: false,
    blurb: "Downloadable script",
  },
  {
    id: "hamilton_vantage",
    label: "Hamilton Vantage",
    legacyRobot: "Vantage",
    codegen: "plan_ir",
    animation: false,
    blurb: "Downloadable script",
  },
  {
    id: "tecan_fluent",
    label: "Tecan Fluent",
    legacyRobot: "Tecan",
    codegen: "plan_ir",
    animation: false,
    blurb: "Downloadable worklist",
  },
];

export function deviceByRobot(robot: RobotModel | null | undefined): DeviceCard | undefined {
  if (!robot) return undefined;
  return DEVICE_CARDS.find((card) => card.legacyRobot === robot);
}

export function robotSupportsWatch(robot: RobotModel | null | undefined): boolean {
  return deviceByRobot(robot)?.animation === true;
}

export function isPythonCodegen(robot: RobotModel | null | undefined): boolean {
  return deviceByRobot(robot)?.codegen === "opentrons_python";
}

export function isPlanCodegen(robot: RobotModel | null | undefined): boolean {
  return deviceByRobot(robot)?.codegen === "plan_ir";
}

export function isHamiltonRobot(robot: RobotModel | null | undefined): boolean {
  return robot === "Hamilton" || robot === "Vantage";
}

const ACTION_RE =
  /\b(transfer|aspirate|dispense|mix|dilut|aliquot|prepare|pcr|move|pipette|spot|wash|serial|protocol)\b|转移|移液|稀释|混合|分装|制备|聚合酶/i;
const VOLUME_RE = /\d+(?:\.\d+)?\s*(?:µl|ul|μl|nl|ml)\b/i;
const WELL_RE = /\b[A-H]\s*\d{1,2}\b/i;

/** A start goal needs an operation, a volume, or wells — not just leftover typing. */
export function goalHasProtocolIntent(goal: string): boolean {
  const text = goal.trim();
  if (!text) return false;
  return ACTION_RE.test(text) || VOLUME_RE.test(text) || WELL_RE.test(text);
}

export function canStart(goal: string, deviceId: string | undefined): boolean {
  return Boolean(goalHasProtocolIntent(goal) && DEVICE_CARDS.some((card) => card.id === deviceId));
}

function namedIn(text: string, name: string): boolean {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(?:^|[^A-Za-z0-9])${escaped}(?![A-Za-z0-9])`, "i").test(text);
}

/** Unique device named in chip/goal text; undefined if none or several. Prefer full labels over short aliases. */
export function matchDeviceFromText(text: string): string | undefined {
  const labelHits = DEVICE_CARDS.filter((card) => namedIn(text, card.label));
  if (labelHits.length === 1) return labelHits[0].id;
  if (labelHits.length > 1) return undefined;
  const legacyHits = DEVICE_CARDS.filter((card) => namedIn(text, card.legacyRobot));
  return legacyHits.length === 1 ? legacyHits[0].id : undefined;
}
