export type LabwareKind = "tips" | "plate" | "reservoir" | "other";

export function pipetteLabel(id: string | undefined): string {
	if (!id) return "—";
	const names: Record<string, string> = {
		p300_single_gen2: "P300 Single GEN2",
		star_1000: "STAR 1000 µL",
		liha_1000: "LiHa 1000 µL",
		flex_1channel_1000: "Flex 1-Channel 1000 µL",
	};
	return names[id] ?? id.replaceAll("_", " ");
}

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
