/**
 * Generate advisory pressure-trace protocols aligned with the validated Flex
 * DNA pressure workflow:
 *   - hw.read_stem_pressure(mount) with OT3Mount
 *   - rewrite full CSV after every sample (crash-safe)
 *   - emit PRESSURE_CSV_B64:<base64> comments (fetch takes the last one)
 *
 * Presets: hover | z_trace | during_probe
 * Observation-only — never writes liquid state / never authorizes resume.
 */

function pythonLiteral(value) {
  return JSON.stringify(value);
}

export const PRESSURE_PRESETS = Object.freeze(["hover", "z_trace", "during_probe"]);

export const PRESSURE_CSV_FIELDNAMES = Object.freeze([
  "site",
  "well",
  "phase",
  "step_index",
  "z_offset_from_top_mm",
  "pressure_pa",
  "capacitance_pf",
  "elapsed_ms",
]);

/** Canonical comment prefix (validated on Flex). Legacy PRESSURE_TRACE kept only in parsers. */
export const PRESSURE_CSV_B64_PREFIX = "PRESSURE_CSV_B64:";

function resolveOt3Mount(mount) {
  const m = String(mount || "left").toLowerCase();
  return m === "right" ? "OT3Mount.RIGHT" : "OT3Mount.LEFT";
}

function sharedHelpers({ robotCsvPath, mountExpr }) {
  return [
    "import base64",
    "import csv",
    "import io",
    "import time",
    "from pathlib import Path",
    "",
    "from opentrons import protocol_api",
    "from opentrons.hardware_control.types import OT3Mount",
    "from opentrons.types import Point",
    "",
    `ROBOT_CSV = Path(${pythonLiteral(robotCsvPath)})`,
    "FIELDNAMES = [",
    ...PRESSURE_CSV_FIELDNAMES.map(name => `    ${pythonLiteral(name)},`),
    "]",
    "",
    "def _csv_paths(protocol):",
    "    paths = [ROBOT_CSV]",
    "    if protocol.is_simulating():",
    '        paths.insert(0, Path("artifacts/pressure-traces/sim_pressure_log.csv"))',
    "    return paths",
    "",
    "def _sample(hw, mount, *, site, well_name, step_index, z_offset_mm, phase):",
    "    pressure_pa = None",
    "    capacitance_pf = None",
    "    try:",
    "        pressure_pa = hw.read_stem_pressure(mount)",
    "        if isinstance(pressure_pa, (list, tuple)):",
    "            pressure_pa = pressure_pa[0]",
    "        pressure_pa = float(pressure_pa)",
    "    except Exception:",
    "        pass",
    "    try:",
    "        capacitance_pf = hw.read_stem_capacitance(mount)",
    "        if isinstance(capacitance_pf, (list, tuple)):",
    "            capacitance_pf = capacitance_pf[0]",
    "        capacitance_pf = float(capacitance_pf)",
    "    except Exception:",
    "        pass",
    "    return {",
    '        "site": site,',
    '        "well": well_name,',
    '        "phase": phase,',
    '        "step_index": step_index,',
    '        "z_offset_from_top_mm": round(float(z_offset_mm), 3),',
    '        "pressure_pa": pressure_pa,',
    '        "capacitance_pf": capacitance_pf,',
    '        "elapsed_ms": int(time.time() * 1000),',
    "    }",
    "",
    "def _write_csv(protocol, rows):",
    "    if not rows:",
    "        return None",
    "    buffer = io.StringIO()",
    "    writer = csv.DictWriter(buffer, fieldnames=FIELDNAMES)",
    "    writer.writeheader()",
    "    writer.writerows(rows)",
    "    csv_text = buffer.getvalue()",
    "    saved_path = None",
    "    for path in _csv_paths(protocol):",
    "        try:",
    "            path.parent.mkdir(parents=True, exist_ok=True)",
    "            path.write_text(csv_text, encoding='utf-8')",
    "            saved_path = str(path)",
    "        except OSError:",
    "            continue",
    "    try:",
    "        encoded = base64.b64encode(csv_text.encode('utf-8')).decode('ascii')",
    `        protocol.comment(${pythonLiteral(PRESSURE_CSV_B64_PREFIX)} + encoded)`,
    "    except Exception:",
    "        pass",
    "    if saved_path:",
    '        protocol.comment(f"Saved {len(rows)} pressure samples -> {saved_path}")',
    "    return saved_path",
    "",
    "def _record(protocol, rows, hw, mount, row):",
    "    rows.append(row)",
    "    _write_csv(protocol, rows)",
    "",
  ];
}

/**
 * Build a standalone pressure-trace protocol.
 *
 * @param {object} opts
 * @param {'hover'|'z_trace'|'during_probe'} opts.preset
 */
export function buildPressureTraceProtocol({
  preset = "hover",
  pipetteName = "flex_1channel_1000",
  mount = "left",
  tiprackLoadName = "opentrons_flex_96_tiprack_200ul",
  tiprackSlot = "C2",
  labwareLoadName = "nest_96_wellplate_200ul_flat",
  labwareSlot = "B3",
  trashSlot = "A3",
  well = "A1",
  startingTip = null,
  apiLevel = "2.24",
  robotType = "Flex",
  zHoverMm = -2.0,
  zStepMm = 0.4,
  zMaxMm = 8.0,
  moveSpeed = 50,
  zSpeed = 4.0,
  hoverSamples = 5,
  hoverIntervalS = 0.2,
  robotCsvPath = "/data/user_storage/labscriptai/pressure_trace.csv",
} = {}) {
  const normalizedPreset = String(preset || "hover").toLowerCase();
  if (!PRESSURE_PRESETS.includes(normalizedPreset)) {
    throw new Error(`Unsupported pressure preset: ${preset}. Use one of: ${PRESSURE_PRESETS.join(", ")}`);
  }

  const wellName = String(well || "A1").toUpperCase();
  const mountExpr = resolveOt3Mount(mount);
  const helpers = sharedHelpers({ robotCsvPath, mountExpr });

  const header = [
    ...helpers,
    `metadata = {"protocolName": "LabscriptAI Pressure Trace (${normalizedPreset})", "author": "Opentrons Lab MCP"}`,
    `requirements = {"robotType": ${pythonLiteral(robotType)}, "apiLevel": ${pythonLiteral(apiLevel)}}`,
    "",
    "def run(protocol: protocol_api.ProtocolContext) -> None:",
    `    protocol.load_trash_bin(${pythonLiteral(String(trashSlot).toUpperCase())})`,
    `    target = protocol.load_labware(${pythonLiteral(labwareLoadName)}, ${pythonLiteral(String(labwareSlot).toUpperCase())})`,
    `    tiprack = protocol.load_labware(${pythonLiteral(tiprackLoadName)}, ${pythonLiteral(String(tiprackSlot).toUpperCase())})`,
    "    pipette = protocol.load_instrument(",
    `        ${pythonLiteral(pipetteName)},`,
    `        ${pythonLiteral(String(mount).toLowerCase())},`,
    "        tip_racks=[tiprack],",
    "    )",
    ...(startingTip
      ? [`    pipette.starting_tip = tiprack[${pythonLiteral(String(startingTip).toUpperCase())}]`]
      : []),
    "    hw = protocol._hw_manager.hardware",
    `    mount = ${mountExpr}`,
    "    rows = []",
    `    well_name = ${pythonLiteral(wellName)}`,
    "    well = target[well_name]",
    "    top = well.top()",
    `    z_hover = ${Number(zHoverMm)}`,
    "",
    "    pipette.pick_up_tip()",
    "    try:",
  ];

  let body = [];
  if (normalizedPreset === "hover") {
    body = [
      `        protocol.comment("Pressure hover at " + well_name)`,
      `        pipette.move_to(top.move(Point(z=z_hover)), speed=${Number(moveSpeed)})`,
      `        for step in range(1, ${Math.max(1, Math.floor(hoverSamples))} + 1):`,
      "            _record(protocol, rows, hw, mount, _sample(",
      "                hw, mount,",
      '                site="hover_" + well_name,',
      "                well_name=well_name,",
      "                step_index=step,",
      "                z_offset_mm=z_hover,",
      '                phase="deck_hover",',
      "            ))",
      `            protocol.delay(seconds=${Number(hoverIntervalS)})`,
    ];
  } else if (normalizedPreset === "z_trace") {
    const steps = Math.max(1, Math.floor(Number(zMaxMm) / Math.max(0.05, Number(zStepMm))));
    body = [
      `        protocol.comment("Pressure Z-trace into " + well_name)`,
      `        pipette.move_to(top.move(Point(z=z_hover)), speed=${Number(moveSpeed)})`,
      "        _record(protocol, rows, hw, mount, _sample(",
      "            hw, mount,",
      '            site="z_trace_" + well_name,',
      "            well_name=well_name,",
      "            step_index=0,",
      "            z_offset_mm=z_hover,",
      '            phase="collision_start",',
      "        ))",
      `        for step in range(1, ${steps} + 1):`,
      `            z_off = z_hover - step * ${Number(zStepMm)}`,
      `            pipette.move_to(top.move(Point(z=z_off)), speed=${Number(zSpeed)})`,
      "            _record(protocol, rows, hw, mount, _sample(",
      "                hw, mount,",
      '                site="z_trace_" + well_name,',
      "                well_name=well_name,",
      "                step_index=step,",
      "                z_offset_mm=z_off,",
      '                phase="collision_z",',
      "            ))",
    ];
  } else {
    // during_probe: sample before/after measure_liquid_height
    body = [
      `        protocol.comment("Pressure during liquid probe at " + well_name)`,
      `        pipette.move_to(top.move(Point(z=z_hover)), speed=${Number(moveSpeed)})`,
      "        _record(protocol, rows, hw, mount, _sample(",
      "            hw, mount,",
      '            site="before_probe_" + well_name,',
      "            well_name=well_name,",
      "            step_index=0,",
      "            z_offset_mm=z_hover,",
      '            phase="before_probe",',
      "        ))",
      "        height_mm = None",
      "        try:",
      "            height_mm = pipette.measure_liquid_height(well)",
      "            protocol.comment('PROBE_RESULT:' + __import__('json').dumps({",
      "                'well': well_name, 'mode': 'measure_height', 'success': True, 'value': height_mm,",
      "                'pressure_trace_advisory': True,",
      "            }))",
      "        except Exception as probe_exc:",
      "            protocol.comment('PROBE_RESULT:' + __import__('json').dumps({",
      "                'well': well_name, 'mode': 'measure_height', 'success': False, 'value': None,",
      "                'error': str(probe_exc), 'pressure_trace_advisory': True,",
      "            }))",
      "        _record(protocol, rows, hw, mount, _sample(",
      "            hw, mount,",
      '            site="after_probe_" + well_name,',
      "            well_name=well_name,",
      "            step_index=1,",
      "            z_offset_mm=z_hover,",
      '            phase="after_probe",',
      "        ))",
    ];
  }

  const footer = [
    "    finally:",
    "        if pipette.has_tip:",
    "            pipette.drop_tip()",
    "    if rows:",
    "        _write_csv(protocol, rows)",
    '    protocol.comment(f"Pressure trace finished with {len(rows)} sample(s); advisory-only.")',
    "",
  ];

  return [...header, ...body, ...footer].join("\n");
}

/**
 * Snippet lines (indented for probe_wells try-block) that sample once and
 * append/rewrite PRESSURE_CSV_B64 — used when record_pressure=true on probe.
 */
export function buildProbeAttachedPressureLines({
  mount = "left",
  sampleCount = 3,
  sampleIntervalS = 0.15,
  robotCsvPath = "/data/user_storage/labscriptai/pressure_trace.csv",
} = {}) {
  const mountExpr = resolveOt3Mount(mount);
  const count = Math.max(1, Math.floor(Number(sampleCount) || 3));
  const interval = Math.max(0.05, Number(sampleIntervalS) || 0.15);
  return [
    "            # Advisory pressure samples (PRESSURE_CSV_B64); does not write liquid state.",
    "            import base64 as _b64",
    "            import csv as _csv",
    "            import io as _io",
    "            import time as _ptime",
    "            from pathlib import Path as _Path",
    "            from opentrons.hardware_control.types import OT3Mount as _OT3Mount",
    "            _press_rows = []",
    "            _press_fields = [" + PRESSURE_CSV_FIELDNAMES.map(n => pythonLiteral(n)).join(", ") + "]",
    "            try:",
    "                _hw = protocol._hw_manager.hardware",
    `                _mount = ${mountExpr}`,
    `                for _si in range(1, ${count} + 1):`,
    "                    _p = None",
    "                    _c = None",
    "                    try:",
    "                        _p = _hw.read_stem_pressure(_mount)",
    "                        if isinstance(_p, (list, tuple)):",
    "                            _p = _p[0]",
    "                        _p = float(_p)",
    "                    except Exception:",
    "                        pass",
    "                    try:",
    "                        _c = _hw.read_stem_capacitance(_mount)",
    "                        if isinstance(_c, (list, tuple)):",
    "                            _c = _c[0]",
    "                        _c = float(_c)",
    "                    except Exception:",
    "                        pass",
    "                    _press_rows.append({",
    "                        'site': 'probe_' + well_name,",
    "                        'well': well_name,",
    "                        'phase': 'during_probe',",
    "                        'step_index': _si,",
    "                        'z_offset_from_top_mm': 0.0,",
    "                        'pressure_pa': _p,",
    "                        'capacitance_pf': _c,",
    "                        'elapsed_ms': int(_ptime.time() * 1000),",
    "                    })",
    `                    protocol.delay(seconds=${interval})`,
    "                if _press_rows:",
    "                    _buf = _io.StringIO()",
    "                    _w = _csv.DictWriter(_buf, fieldnames=_press_fields)",
    "                    _w.writeheader()",
    "                    _w.writerows(_press_rows)",
    "                    _csv_text = _buf.getvalue()",
    "                    try:",
    `                        _robot_csv = _Path(${pythonLiteral(robotCsvPath)})`,
    "                        _robot_csv.parent.mkdir(parents=True, exist_ok=True)",
    "                        _robot_csv.write_text(_csv_text, encoding='utf-8')",
    "                    except OSError:",
    "                        pass",
    "                    protocol.comment(",
    `                        ${pythonLiteral(PRESSURE_CSV_B64_PREFIX)} + _b64.b64encode(_csv_text.encode('utf-8')).decode('ascii')`,
    "                    )",
    "            except Exception as _press_exc:",
    "                protocol.comment(",
    "                    'PRESSURE_TRACE_ERROR:' + __import__('json').dumps({",
    "                        'well': well_name, 'error': str(_press_exc), 'observation_only': True,",
    "                    })",
    "                )",
  ];
}
