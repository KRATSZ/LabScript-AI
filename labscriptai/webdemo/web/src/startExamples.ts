export const EXAMPLES: Array<{ label: string; goal: string; doc: string; deviceId: string }> = [
  {
    label: "Transfer 50 µL A1→B1",
    goal: "Transfer 50 µL from well A1 to B1 on a 96-well plate.",
    doc: "",
    deviceId: "flex",
  },
  {
    label: "Prepare a PCR mix",
    goal: "Prepare a PCR mix: dispense 20 µL of master mix into 8 sample wells.",
    doc: "Dispense 20 µL of master mix into 8 sample wells.",
    deviceId: "flex",
  },
  {
    label: "Serial dilution",
    goal: "Prepare a 1:2 serial dilution across wells A1 to A8, with 100 µL in each well after mixing.",
    doc: "Use a 96-well plate. Ask me to confirm the stock, diluent and starting volume before generating code.",
    deviceId: "flex",
  },
];
