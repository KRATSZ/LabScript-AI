import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import { buildProbeWellsProtocol } from "./probe.js";
import { buildPressureTraceProtocol, PRESSURE_CSV_B64_PREFIX } from "./pressure-protocol.js";
import {
  extractPressureTracesFromCommands,
  parsePressureCsv,
  runPressureTraceCheck,
} from "./pressure-trace.js";
import { fetchAllRunCommands, parseRunCommandsPage } from "./run-commands.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pressureCheckScript = path.join(__dirname, "../scripts/pressure_trace_check.py");

test("buildPressureTraceProtocol hover emits PRESSURE_CSV_B64 + read_stem_pressure(mount)", () => {
  const protocol = buildPressureTraceProtocol({
    preset: "hover",
    well: "A1",
    hoverSamples: 3,
  });
  assert.match(protocol, /read_stem_pressure\(mount\)/);
  assert.match(protocol, /OT3Mount\.LEFT/);
  assert.match(protocol, new RegExp(PRESSURE_CSV_B64_PREFIX));
  assert.doesNotMatch(protocol, /PRESSURE_TRACE:[A-Z]/);
  assert.match(protocol, /deck_hover/);
});

test("buildPressureTraceProtocol z_trace steps Z while sampling", () => {
  const protocol = buildPressureTraceProtocol({
    preset: "z_trace",
    zStepMm: 0.5,
    zMaxMm: 2.0,
  });
  assert.match(protocol, /collision_z/);
  assert.match(protocol, /read_stem_pressure\(mount\)/);
});

test("buildProbeWellsProtocol record_pressure uses PRESSURE_CSV_B64", () => {
  const protocol = buildProbeWellsProtocol({
    pipetteName: "flex_1channel_1000",
    mount: "left",
    tiprackLoadName: "opentrons_flex_96_tiprack_200ul",
    tiprackSlot: "B2",
    labwareLoadName: "nest_96_wellplate_200ul_flat",
    labwareSlot: "C2",
    wells: ["A1"],
    mode: "measure_height",
    recordPressure: true,
    pressureSampleCount: 2,
  });
  assert.match(protocol, /measure_liquid_height/);
  assert.match(protocol, /read_stem_pressure\(/);
  assert.match(protocol, /PRESSURE_CSV_B64:/);
});

test("extractPressureTracesFromCommands prefers last PRESSURE_CSV_B64", () => {
  const csv1 = [
    "site,well,phase,step_index,z_offset_from_top_mm,pressure_pa,capacitance_pf,elapsed_ms",
    "hover,A1,deck_hover,1,-2,100.0,,1000",
  ].join("\n");
  const csv2 = [
    "site,well,phase,step_index,z_offset_from_top_mm,pressure_pa,capacitance_pf,elapsed_ms",
    "hover,A1,deck_hover,1,-2,100.0,,1000",
    "hover,A1,deck_hover,2,-2,120.5,,1100",
  ].join("\n");
  const commands = {
    data: [
      {
        commandType: "comment",
        params: { message: `${PRESSURE_CSV_B64_PREFIX}${Buffer.from(csv1, "utf8").toString("base64")}` },
      },
      {
        commandType: "comment",
        params: { message: `${PRESSURE_CSV_B64_PREFIX}${Buffer.from(csv2, "utf8").toString("base64")}` },
      },
    ],
  };
  const parsed = extractPressureTracesFromCommands(commands);
  assert.equal(parsed.traces.length, 1);
  assert.equal(parsed.traces[0].source, "PRESSURE_CSV_B64");
  assert.equal(parsed.traces[0].sample_count, 2);
  assert.equal(parsed.traces[0].samples[1].pressure_pa, 120.5);
  assert.equal(parsed.traces[0].comment_rewrites, 2);
});

test("extractPressureTracesFromCommands still decodes legacy PRESSURE_TRACE chunks", () => {
  const csv = "t_ms,pressure_pa\n0,10\n50,20\n";
  const b64 = Buffer.from(csv, "utf8").toString("base64");
  const mid = Math.ceil(b64.length / 2);
  const commands = {
    data: [
      { commandType: "comment", params: { message: `PRESSURE_TRACE:A1:1/2:${b64.slice(0, mid)}` } },
      { commandType: "comment", params: { message: `PRESSURE_TRACE:A1:2/2:${b64.slice(mid)}` } },
    ],
  };
  const parsed = extractPressureTracesFromCommands(commands);
  assert.equal(parsed.traces[0].legacy, true);
  assert.equal(parsed.traces[0].samples.length, 2);
});

test("parsePressureCsv reads canonical columns", () => {
  const csv = [
    "site,well,phase,step_index,z_offset_from_top_mm,pressure_pa,capacitance_pf,elapsed_ms",
    "z,A1,collision_z,1,-2.4,150.2,12.1,2000",
  ].join("\n");
  const samples = parsePressureCsv(csv);
  assert.equal(samples.length, 1);
  assert.equal(samples[0].phase, "collision_z");
  assert.equal(samples[0].pressure_pa, 150.2);
  assert.equal(samples[0].z_offset_from_top_mm, -2.4);
});

test("pressure_trace_check.py returns phase features for canonical CSV", () => {
  const csvLines = [
    "site,well,phase,step_index,z_offset_from_top_mm,pressure_pa,capacitance_pf,elapsed_ms",
  ];
  for (let i = 0; i < 12; i += 1) {
    const pressure = i < 4 ? 100 : 100 + (i - 4) * 15;
    csvLines.push(`z,A1,collision_z,${i},${(-2 - i * 0.4).toFixed(1)},${pressure},,${1000 + i * 50}`);
  }
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "pressure-trace-"));
  const csvPath = path.join(tmp, "trace.csv");
  fs.writeFileSync(csvPath, `${csvLines.join("\n")}\n`);
  const result = spawnSync("python3", [pressureCheckScript], {
    input: JSON.stringify({ csv_path: csvPath, moving_average_window: 1 }),
    encoding: "utf8",
  });
  assert.equal(result.status, 0, result.stderr);
  const parsed = JSON.parse(result.stdout);
  assert.equal(parsed.observation_only, true);
  assert.equal(parsed.resume_authority, false);
  assert.ok(parsed.advisory_features.phases.collision_z);
  assert.ok(parsed.advisory_features.sample_count >= 12);
});

test("runPressureTraceCheck JS wrapper marks advisory-only", async () => {
  const result = await runPressureTraceCheck({
    csvText: [
      "site,well,phase,step_index,z_offset_from_top_mm,pressure_pa,capacitance_pf,elapsed_ms",
      "h,A1,deck_hover,1,-2,10,,0",
      "h,A1,deck_hover,2,-2,40,,10",
      "h,A1,deck_hover,3,-2,42,,20",
      "h,A1,deck_hover,4,-2,41,,30",
      "h,A1,deck_hover,5,-2,41,,40",
    ].join("\n"),
    movingAverageWindow: 1,
  });
  assert.equal(result.observation_only, true);
  assert.equal(result.resume_authority, false);
});

test("parseRunCommandsPage reads totalLength for offset pagination", () => {
  const page = parseRunCommandsPage({
    data: [{ id: "1" }],
    meta: { totalLength: 250 },
  });
  assert.equal(page.totalLength, 250);
  assert.equal(page.commands.length, 1);
});

test("fetchAllRunCommands uses offset += len until totalLength", async () => {
  const calls = [];
  const requestRobotJson = async (_method, _robotIp, pathname, { searchParams } = {}) => {
    calls.push({ pathname, searchParams: { ...searchParams } });
    const cursor = Number(searchParams?.cursor || 0);
    if (cursor === 0) {
      return {
        data: Array.from({ length: 100 }, (_, i) => ({ id: String(i) })),
        meta: { totalLength: 150 },
      };
    }
    return {
      data: Array.from({ length: 50 }, (_, i) => ({ id: String(100 + i) })),
      meta: { totalLength: 150 },
    };
  };
  const all = await fetchAllRunCommands(requestRobotJson, "10.0.0.1", "run-1", {
    pageLength: 100,
    maxPages: 5,
  });
  assert.equal(all.length, 150);
  assert.equal(calls.length, 2);
  assert.equal(calls[1].searchParams.cursor, 100);
});
