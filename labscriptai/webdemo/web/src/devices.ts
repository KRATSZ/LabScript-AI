import type { DeviceCard, RobotModel } from "./types";

/** Display cards. Keep ids/labels/legacyRobot/codegen/animation in lockstep with server DEVICE_REGISTRY. */
export const DEVICE_CARDS: DeviceCard[] = [
  {
    id: "ot2",
    label: "OT-2",
    legacyRobot: "OT-2",
    codegen: "opentrons_python",
    animation: true,
    blurb: "Python script + simulation + animation",
  },
  {
    id: "flex",
    label: "Flex",
    legacyRobot: "Flex",
    codegen: "opentrons_python",
    animation: true,
    blurb: "Python script + simulation + animation",
  },
  {
    id: "hamilton_star",
    label: "Hamilton STAR",
    legacyRobot: "Hamilton",
    codegen: "plan_ir",
    animation: false,
    blurb: "Step JSON + runnable PyLabRobot script",
  },
  {
    id: "hamilton_vantage",
    label: "Hamilton Vantage",
    legacyRobot: "Vantage",
    codegen: "plan_ir",
    animation: false,
    blurb: "Step JSON + runnable PyLabRobot script",
  },
  {
    id: "tecan_fluent",
    label: "Tecan Fluent",
    legacyRobot: "Tecan",
    codegen: "plan_ir",
    animation: false,
    blurb: "Tecan Fluent .gwl worklist",
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

export function canStart(goal: string, deviceId: string | undefined): boolean {
  return Boolean(goal.trim() && DEVICE_CARDS.some((card) => card.id === deviceId));
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
