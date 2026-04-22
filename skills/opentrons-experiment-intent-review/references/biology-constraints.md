# Biology constraints (reference)

Use this file when filling **`biology_constraints`** in the intent-review handoff. Content here is **advisory** for protocol design; it must not bypass the **simulation gate** or MCP safety rules.

## Liquid property → automation strategy

Match each reagent to its liquid property class. When the user does not specify, classify by reagent name and note the assumption.

| Liquid class | Examples | Transfer strategy | Liquid class API | Fallback |
|-------------|----------|-------------------|-----------------|----------|
| Aqueous | Water, PBS, TE buffer, TBE | Standard transfer | `water` | Default flow rate |
| Volatile | Ethanol ≥70%, isopropanol | air_gap=20µL, blow_out | `ethanol_80` | Slow dispense |
| Viscous | Glycerol ≥50%, DMSO, Ficoll | Slow aspirate, blow_out | `glycerol_50` | `flow_rate.aspirate` reduced |
| Bead suspension | Magnetic beads in liquid | Off-center aspirate, resuspend before transfer | — | mix before aspirate, air_gap |
| Protein solution | Serum, BSA, antibodies | Low-retention tips preferred, touch_tip | — | `flow_rate.aspirate` slightly reduced |
| Enzymatic mix | Polymerase, ligase, restriction enzyme | Minimize dead volume, keep cold | — | Temperature Module 4°C |

### Bead-specific handling

Bead suspensions require special care because beads settle:

- **Resuspend before every transfer**: mix 10 reps at 50% of well volume, dispense at 500 µL/s.
- **Off-center aspiration**: aspirate from well center, not bottom, to avoid pulling beads with supernatant.
- **Air gap**: 20 µL air gap after aspirating bead suspension to prevent carryover.
- **Supernatant removal**: aspirate at 25-30 µL/s (slow) to avoid disturbing bead pellet; dispense waste at 150 µL/s.
- **On Flex**: Magnetic Block is **passive** (no engage/disengage API). Use gripper to move plate on/off block. Incubation time on block replaces the OT-2 "engage → settle" pattern.

## Temperature handling

| Requirement | Solution | Notes |
|------------|----------|-------|
| Ice bucket for reagents | Temperature Module GEN2 set to 4°C | Pre-cool labware on module before transfer |
| Heat inactivation | Temperature Module or Heater-Shaker at 95°C | Heater-Shaker: 37-95°C range |
| Enzyme incubation | Temperature Module at target temp | Up to 95°C |
| On-deck cooling | Temperature Module at 4°C | Ambient must be <22°C for optimal cooling |
| PCR thermocycling | Thermocycler GEN2 at A1+B1 | Block: 4-99°C, Lid: 37-110°C |
| Shaking incubation | Heater-Shaker (200-3000 rpm) | Requires thermal adapter + labware latch |

**Rules:**
- Heat-sensitive reagents (enzymes, cells): schedule cold-handling steps early, minimize time on deck at ambient.
- Temperature Module can replace ice bucket for on-deck cold storage.
- Multiple Temperature Modules can run at different temperatures simultaneously.

## Contamination policy

| Experiment type | Tip strategy | Rationale |
|----------------|-------------|-----------|
| PCR / qPCR | New tip per well | Cross-contamination destroys quantitation |
| Enzymatic reaction | New tip per destination | Enzyme carryover affects kinetics |
| Magnetic bead purification | New tip per destination; same tip OK for same reagent across wells | Reagent-to-well cross-contamination matters, not well-to-well for same reagent |
| Normalization | New tip per destination | Volume accuracy matters per well |
| Serial dilution | New tip per step | Prevents concentration gradient contamination |
| Standard liquid transfer | New tip per destination | Default safe behavior |

## Timing constraints (from reference protocols)

| Step | Typical time | Notes |
|------|-------------|-------|
| Bead binding (after adding beads) | 2-5 min at RT | Gentle mixing during incubation helps |
| Magnetic separation (on block) | 2-5 min | Flex: passive block, no engage; just wait |
| Ethanol wash (each) | 30s-1 min incubation | Do not let beads dry during wash |
| Bead drying | 5-15 min at RT | Over-drying (>15 min) reduces recovery |
| Elution incubation | 2-5 min at RT | Mix well to resuspend beads |
| PCR reagent on ice | Keep cold until thermocycler starts | Use Temperature Module at 4°C |
| Enzymatic reaction start | Add enzyme within 5-10 min of mixing | Activity decreases at RT |

## Suggested fields for intent-review

- **Sample / material types** — DNA, RNA, cells, protein, beads; fixation or infectious material flag.
- **Reagent list with liquid class** — Classify each reagent using the table above. If unknown, ask.
- **Contamination policy** — Select from the table above based on experiment type.
- **Temperature requirements** — Which steps need heating/cooling, and which module.
- **Success criteria** — What "done" means (volumes, mixing, incubation if stated by user).

## Scope

- Prefer **short, explicit bullets** the author can copy into docstrings or comments.
- If the user has not provided biological detail, say **`unknown`** and list one blocking question rather than inventing SOPs.
