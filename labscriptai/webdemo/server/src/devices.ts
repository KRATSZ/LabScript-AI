export type DeviceId = "ot2" | "flex" | "hamilton_star" | "hamilton_vantage" | "tecan_fluent";
export type RobotModel = "OT-2" | "Flex" | "Hamilton" | "Vantage" | "Tecan";
export type HamiltonFamily = "star" | "vantage";
export type PlanBackend = "serializing" | "hamilton" | "ot2" | "tecan_evo" | "tecan_fluent" | "auto";
export type CodegenKind = "opentrons_python" | "plan_ir";

export interface HardwarePresetBody {
  leftPipette: string;
  rightPipette: string;
  apiVersion: string;
  deck: Record<string, string>;
}

export interface DeviceProfile {
  id: DeviceId;
  label: string;
  aliases: RegExp[];
  legacyRobot: RobotModel;
  codegen: CodegenKind;
  planBackend: PlanBackend;
  checks: string[];
  animation: boolean;
  artifactExt: ".py" | ".json" | ".gwl";
  hardwarePreset: HardwarePresetBody & { id: string };
  note?: string;
}

const OT2_HW = {
  leftPipette: "p300_single_gen2",
  rightPipette: "None",
  apiVersion: "2.15",
  deck: {
    "1": "opentrons_96_tiprack_300ul",
    "2": "nest_96_wellplate_200ul_flat",
    "3": "nest_12_reservoir_15ml",
  },
} as const satisfies HardwarePresetBody;

const FLEX_HW = {
  leftPipette: "flex_1channel_1000",
  rightPipette: "None",
  apiVersion: "2.22",
  deck: {
    A1: "opentrons_flex_96_tiprack_1000ul",
    D2: "nest_96_wellplate_200ul_flat",
    C1: "nest_12_reservoir_15ml",
    A3: "trash_bin",
  },
} as const satisfies HardwarePresetBody;

const HAMILTON_HW = {
  leftPipette: "star_1000",
  rightPipette: "None",
  apiVersion: "",
  deck: {
    "1": "hamilton_96_tiprack_300ul",
    "2": "corning_96_wellplate_360ul_flat",
    "3": "nest_12_reservoir_15ml",
  },
} as const satisfies HardwarePresetBody;

/** Per-well µL for Hamilton STAR standard-deck labware. Unknown names stay unknown. */
export const HAMILTON_STANDARD_WELL_UL: Record<string, number> = {
  corning_96_wellplate_360ul_flat: 360,
  nest_12_reservoir_15ml: 15_000,
};

export function knownHamiltonWellUl(labware: string | undefined): number | undefined {
  if (!labware) return undefined;
  const n = labware.trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(HAMILTON_STANDARD_WELL_UL, n)
    ? HAMILTON_STANDARD_WELL_UL[n]
    : undefined;
}

/** Per-well µL for Tecan Fluent standard-deck labware. Unknown names stay unknown. */
export const TECAN_STANDARD_WELL_UL: Record<string, number> = {
  tecan_96_wellplate: 360,
  nest_12_reservoir_15ml: 15_000,
};

/** Assumed Fluent FCA DiTi capacity (tecan_diti_200ul_tiprack). fca_1000 is the pipette, not a 1000 µL tip. */
export const TECAN_STANDARD_TIP_UL = 200;

export function knownTecanWellUl(labware: string | undefined): number | undefined {
  if (!labware) return undefined;
  const n = labware.trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(TECAN_STANDARD_WELL_UL, n)
    ? TECAN_STANDARD_WELL_UL[n]
    : undefined;
}

/** Per-well µL for Opentrons standard-deck labware. Unknown names stay unknown. */
export const OPENTRONS_STANDARD_WELL_UL: Record<string, number> = {
  nest_96_wellplate_200ul_flat: 200,
  nest_12_reservoir_15ml: 15_000,
};

export const OT2_STANDARD_TIP_UL = 300;
export const FLEX_STANDARD_TIP_UL = 1000;
export const HAMILTON_STANDARD_TIP_UL = 300;

export function knownOpentronsWellUl(labware: string | undefined): number | undefined {
  if (!labware) return undefined;
  const n = labware.trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(OPENTRONS_STANDARD_WELL_UL, n)
    ? OPENTRONS_STANDARD_WELL_UL[n]
    : undefined;
}

function knownWellUl(labware: string | undefined): number | undefined {
  return knownOpentronsWellUl(labware) ?? knownHamiltonWellUl(labware) ?? knownTecanWellUl(labware);
}

function knownTipUl(labware: string | undefined, device?: DeviceProfile): number | undefined {
  const n = (labware || "").trim().toLowerCase();
  if (n === "opentrons_96_tiprack_300ul") return OT2_STANDARD_TIP_UL;
  if (n === "opentrons_flex_96_tiprack_1000ul") return FLEX_STANDARD_TIP_UL;
  if (n === "hamilton_96_tiprack_300ul") return HAMILTON_STANDARD_TIP_UL;
  const named = n.match(/(\d+)\s*ul/);
  if (named && /diti|tiprack|tip\s*rack/.test(n)) return Number(named[1]);
  if (device?.id === "tecan_fluent") return TECAN_STANDARD_TIP_UL;
  return undefined;
}

/** One-line assumed-deck capacities for the model, e.g. "plate wells hold 200 µL, tips 300 µL". */
export function assumedCapacityLine(
  robotOrId: string | undefined,
  deck?: Record<string, string>
): string {
  const d = deviceFor(robotOrId);
  if (!d) return "";
  const layout = deck && Object.keys(deck).length > 0 ? deck : d.hardwarePreset.deck;
  let plateUl: number | undefined;
  let tipUl: number | undefined;
  for (const name of Object.values(layout)) {
    const lower = name.toLowerCase();
    if (!tipUl && /tip\s*rack|tiprack|diti/i.test(lower)) {
      tipUl = knownTipUl(name, d);
    } else if (
      !plateUl &&
      /wellplate|plate/i.test(lower) &&
      !/tip|diti|reservoir/i.test(lower)
    ) {
      plateUl = knownWellUl(name);
    }
  }
  if (tipUl == null && d.id === "tecan_fluent") tipUl = TECAN_STANDARD_TIP_UL;
  const parts: string[] = [];
  if (plateUl != null) parts.push(`plate wells hold ${plateUl} µL`);
  if (tipUl != null) parts.push(`tips ${tipUl} µL`);
  return parts.join(", ");
}

const TECAN_HW = {
  leftPipette: "fca_1000",
  rightPipette: "None",
  apiVersion: "",
  deck: {
    "1": "tecan_diti_200ul_tiprack",
    "2": "tecan_96_wellplate",
    "3": "nest_12_reservoir_15ml",
  },
} as const satisfies HardwarePresetBody;

export const HARDWARE_PRESETS = {
  ot2_p300_standard3: OT2_HW,
  flex_1000_standard3: FLEX_HW,
  hamilton_star_standard: HAMILTON_HW,
  hamilton_vantage_standard: HAMILTON_HW,
  tecan_fluent_standard: TECAN_HW,
} as const;

export type HardwarePresetId = keyof typeof HARDWARE_PRESETS;

export const DEVICE_REGISTRY: DeviceProfile[] = [
  {
    id: "ot2",
    label: "OT-2",
    aliases: [/\bot-?2\b/],
    legacyRobot: "OT-2",
    codegen: "opentrons_python",
    planBackend: "serializing",
    checks: ["opentrons_sim", "logicpass", "llmreview"],
    animation: true,
    artifactExt: ".py",
    hardwarePreset: { id: "ot2_p300_standard3", ...OT2_HW },
  },
  {
    id: "flex",
    label: "Flex",
    aliases: [/\bflex\b/],
    legacyRobot: "Flex",
    codegen: "opentrons_python",
    planBackend: "serializing",
    checks: ["opentrons_sim", "logicpass", "llmreview"],
    animation: true,
    artifactExt: ".py",
    hardwarePreset: { id: "flex_1000_standard3", ...FLEX_HW },
  },
  {
    id: "hamilton_star",
    label: "Hamilton STAR",
    aliases: [/\bhamilton\s+star\b/, /\bstar\b/, /\bhamilton\b(?!\s+vantage)/],
    legacyRobot: "Hamilton",
    codegen: "plan_ir",
    planBackend: "hamilton",
    checks: ["virtual_deck", "plr_sim"],
    animation: false,
    artifactExt: ".py",
    hardwarePreset: { id: "hamilton_star_standard", ...HAMILTON_HW },
  },
  {
    id: "hamilton_vantage",
    label: "Hamilton Vantage",
    aliases: [/\bvantage\b/, /\bhamilton\s+vantage\b/],
    legacyRobot: "Vantage",
    codegen: "plan_ir",
    planBackend: "hamilton",
    checks: ["virtual_deck", "plr_sim"],
    animation: false,
    artifactExt: ".py",
    hardwarePreset: { id: "hamilton_vantage_standard", ...HAMILTON_HW },
  },
  {
    id: "tecan_fluent",
    label: "Tecan Fluent",
    aliases: [/\btecan\b/],
    legacyRobot: "Tecan",
    codegen: "plan_ir",
    planBackend: "tecan_fluent",
    checks: ["virtual_deck", "plr_sim", "pyfluent_compile"],
    animation: false,
    artifactExt: ".gwl",
    hardwarePreset: { id: "tecan_fluent_standard", ...TECAN_HW },
    note: "Simulation reuses Freedom EVO deck geometry (200 µL tips). The download is a FluentControl worklist, not EVOware.",
  },
];

export function deviceForId(id: string): DeviceProfile | undefined {
  return DEVICE_REGISTRY.find((d) => d.id === id);
}

export function deviceFor(robotOrId: string | undefined): DeviceProfile | undefined {
  if (!robotOrId) return undefined;
  const raw = robotOrId.trim();
  if (!raw) return undefined;
  const lower = raw.toLowerCase();
  return (
    deviceForId(raw) ??
    DEVICE_REGISTRY.find(
      (d) => d.legacyRobot === raw || d.label === raw || d.id === raw
    ) ??
    DEVICE_REGISTRY.find(
      (d) =>
        d.legacyRobot.toLowerCase() === lower ||
        d.label.toLowerCase() === lower ||
        d.id.toLowerCase() === lower
    )
  );
}

export function usesFluentCompile(robotOrId: string | undefined): boolean {
  return deviceFor(robotOrId)?.id === "tecan_fluent";
}

export function hamiltonFamily(robotOrId: string | undefined): HamiltonFamily | undefined {
  const id = deviceFor(robotOrId)?.id;
  if (id === "hamilton_star") return "star";
  if (id === "hamilton_vantage") return "vantage";
  return undefined;
}

export function usesHamiltonCompile(robotOrId: string | undefined): boolean {
  return hamiltonFamily(robotOrId) != null;
}

export const ROBOT_PRESET = Object.fromEntries(
  DEVICE_REGISTRY.map((d) => [d.legacyRobot, d.hardwarePreset.id])
) as Record<RobotModel, HardwarePresetId>;

export const PRESET_ROBOT = Object.fromEntries(
  DEVICE_REGISTRY.map((d) => [d.hardwarePreset.id, d.legacyRobot])
) as Record<HardwarePresetId, RobotModel>;
