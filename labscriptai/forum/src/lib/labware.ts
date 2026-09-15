export type LabwareKind = "tips" | "plate" | "reservoir" | "other";

export function labwareKind(name: string): LabwareKind {
	const n = name.toLowerCase();
	if (/tip\s*rack|tiprack|diti/.test(n)) return "tips";
	if (/reservoir/.test(n)) return "reservoir";
	if (/wellplate|plate/.test(n)) return "plate";
	return "other";
}

export function labwareLabel(name: string): string {
	const n = name.toLowerCase();
	if (n.includes("diti")) return "DiTi 200 µL";
	if (n.includes("tiprack_300") || n.includes("tiprack_300ul") || n.includes("96_tiprack_300")) {
		return "300 µL tips";
	}
	if (n.includes("tiprack_1000") || n.includes("1000ul")) return "1000 µL tips";
	if (n.includes("wellplate") || n.includes("96_well")) return "96-well plate";
	if (n.includes("reservoir")) return "reservoir";
	return name.replaceAll("_", " ");
}
