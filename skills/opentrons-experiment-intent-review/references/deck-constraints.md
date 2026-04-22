# Deck constraints (reference)

Use this file as a checklist when filling **`deck_constraints`** in the intent-review handoff. It does not override MCP tools: **`reconcile_state`**, **`robot_status`**, and simulation remain authoritative for what is actually on the robot.

## Flex deck layout

```
         Col 1        Col 2        Col 3        Staging
Row A  [  A1  ]    [  A2  ]    [  A3  ]    [  A4  ]
Row B  [  B1  ]    [  B2  ]    [  B3  ]    [  B4  ]
Row C  [  C1  ]    [  C2  ]    [  C3  ]    [  C4  ]
Row D  [  D1  ]    [  D2  ]    [  D3  ]    [  D4  ]
         ^working area^              ^pipettes only^  ^gripper only^
```

- **Working area**: A1-D3 (12 slots). Pipettes can reach all positions.
- **Staging area**: A4-D4 (4 slots). Only gripper can reach; pipettes cannot.
- **Expansion slot**: behind A1, used only by Thermocycler.
- Slots are interchangeable within a column (1, 2, or 3) but NOT across columns.

## Fixture placement

| Fixture | Allowed slots |
|---------|--------------|
| Trash bin | A1-D1, A3-D3 |
| Waste chute | D3 only |
| Staging area slots | Replaces A3-D3 (moves trash bin) |

## Module placement

| Module | Allowed slots | Notes |
|--------|--------------|-------|
| Heater-Shaker GEN1 | Column 1 or 3 caddy slot | Requires thermal adapter |
| Temperature Module GEN2 | Column 1 or 3 caddy slot | 4-95°C, needs calibration |
| Thermocycler GEN2 | A1+B1 only (2 slots) | GEN1 not supported on Flex |
| Plate Reader | A3-D3 only | Requires gripper for lid |
| Magnetic Block GEN1 | Any working area slot (A1-D3) | Passive, no power, no caddy |
| HEPA/UV Module | Top-mounted, not on deck | No slot consumed |

**Rules:**
- Caddies for single-slot modules go in column 1 or 3 only.
- Thermocycler occupies A1+B1 simultaneously — no other labware in those slots.
- Multiple Temperature Modules are allowed (e.g., one at 4°C for cold storage, one at 37°C for incubation).
- Only load modules the run actually needs; unstated modules are an `open_question`.

## Pipettes

### Available models (Flex only)

| Load name | Channels | Volume range | Tips |
|-----------|----------|-------------|------|
| `flex_1channel_50` | 1 | 1-50 µL | 50 µL |
| `flex_1channel_1000` | 1 | 5-1000 µL | 50 / 200 / 1000 µL |
| `flex_8channel_50` | 8 | 1-50 µL | 50 µL |
| `flex_8channel_1000` | 8 | 5-1000 µL | 50 / 200 / 1000 µL |
| `flex_96channel_1000` | 96 | 5-1000 µL | 50 / 200 / 1000 µL |

**Do NOT use:** `flex_1channel_200`, `flex_8channel_200` — these do not exist.

### Tip selection rules

| Tip size | Best for | Avoid |
|----------|----------|-------|
| 50 µL | Volumes 1-50 µL | >50 µL (exceeds capacity) |
| 200 µL | Volumes 5-200 µL | <5 µL (poor accuracy) |
| 1000 µL | Volumes 20-1000 µL | <20 µL (poor accuracy) |

**Rule:** Use the smallest tip that meets the volume requirement.

### Accuracy reference (Flex 8-Channel, key ranges)

| Pipette | Tip | Volume | Accuracy %D | Precision %CV |
|---------|-----|--------|------------|--------------|
| 8-Ch 50 µL | 50 µL | 1 µL | 10.0% | 8.0% |
| 8-Ch 50 µL | 50 µL | 10 µL | 2.5% | 1.0% |
| 8-Ch 50 µL | 50 µL | 50 µL | 1.25% | 0.6% |
| 8-Ch 1000 µL | 200 µL | 200 µL | 1.0% | 0.25% |
| 8-Ch 1000 µL | 1000 µL | 1000 µL | 0.7% | 0.15% |

**Implication:** For volumes <10 µL, expect reduced accuracy. Flag to operator if precision matters for the experiment.

### 96-Channel special rules

- Requires **tip rack adapter** on deck — cannot place rack directly on slot.
- Supports partial tip pickup: column, row, or single tip.
- Occupies **both** pipette mounts — no other pipette simultaneously.
- When picking up <96 tips, rack must be on deck (not in adapter).

## What to capture in intent-review

- **Robot type** — OT-2 vs Flex (affects trash, requirements, pipette API).
- **Intended slots** — Which deck positions hold which labware load names (as planned before run).
- **Pipettes** — Mounts, volumes, and whether the plan matches available hardware.
- **Modules** — Only load what the run needs; unstated modules are an `open_question`.
- **Orientation** — Human "top" of plate vs robot indexing (A1 corner); state explicitly if ambiguous.
- **Tip racks** — Density (50 µL / 200 µL / 1000 µL) and whether multiple racks are needed.
- **Tip budget** — Total tips consumed must be ≤ tips available (96 per rack).

## Consistency

- Anything safety-critical that is still unknown belongs in **`open_questions`**, not assumed here.
- After live preflight, deck truth comes from **`reconcile_state`** and related MCP tools, not from this text alone.
