import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  listPublicTools,
  PUBLIC_LIST_TOOL_NAMES,
  TOOL_DEFINITIONS,
  TOOL_HANDLERS,
} from "../index.js";
import { PRESSURE_TRACE_ENV_FLAG } from "./pressure-tools.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const mcpRoot = path.resolve(__dirname, "..");
const readmePath = path.join(mcpRoot, "README.md");
const gatePath = path.resolve(mcpRoot, "../../../agent/gate.py");

const PRESSURE_TOOLS = ["run_pressure_trace", "fetch_pressure_trace", "analyze_pressure_trace"];

const FIXTURE_CSV = [
  "site,well,phase,step_index,z_offset_from_top_mm,pressure_pa,capacitance_pf,elapsed_ms",
  "z,A1,collision_start,0,-2.0,100.0,10.0,1000",
  "z,A1,collision_z,1,-2.4,105.0,10.1,1050",
  "z,A1,collision_z,2,-2.8,118.0,10.2,1100",
  "z,A1,collision_z,3,-3.2,160.0,10.5,1150",
  "z,A1,collision_z,4,-3.6,175.0,10.6,1200",
  "z,A1,collision_z,5,-4.0,178.0,10.7,1250",
].join("\n");

function backtickToolNames(text) {
  return [...text.matchAll(/`([a-z][a-z0-9_]{3,})`/g)].map(match => match[1]);
}

test("TOOL_DEFINITIONS names ≡ Object.keys(TOOL_HANDLERS)", () => {
  const definitionNames = TOOL_DEFINITIONS.map(tool => tool.name).sort();
  const handlerNames = Object.keys(TOOL_HANDLERS).sort();
  assert.deepEqual(definitionNames, handlerNames);
  assert.ok(definitionNames.length > PUBLIC_LIST_TOOL_NAMES.length);
});

test("README-claimed and SAFE_ACTION_TYPES pressure tools exist in handlers", () => {
  const readme = fs.readFileSync(readmePath, "utf8");
  const gateSource = fs.readFileSync(gatePath, "utf8");
  const handlerNames = new Set(Object.keys(TOOL_HANDLERS));

  for (const name of PRESSURE_TOOLS) {
    assert.ok(readme.includes(`\`${name}\``), `README must document ${name}`);
    assert.ok(handlerNames.has(name), `${name} must be registered in TOOL_HANDLERS`);
    assert.equal(typeof TOOL_HANDLERS[name], "function");
    assert.ok(gateSource.includes(`"${name}"`), `gate.py SAFE_ACTION_TYPES must include ${name}`);
  }

  const featureTableTools = [];
  for (const line of readme.split("\n")) {
    const match = line.match(/^\|\s+`([a-z][a-z0-9_]+)`\s+\|/);
    if (match) {
      featureTableTools.push(match[1]);
    }
  }
  assert.ok(featureTableTools.includes("run_pressure_trace"));
  for (const name of featureTableTools) {
    assert.ok(handlerNames.has(name), `README feature table claims ${name} but handler is missing`);
  }

  const readmeTools = backtickToolNames(readme).filter(name => handlerNames.has(name) || PRESSURE_TOOLS.includes(name));
  for (const name of new Set(readmeTools)) {
    if (PRESSURE_TOOLS.includes(name) || featureTableTools.includes(name)) {
      assert.ok(handlerNames.has(name), `${name} claimed by README must exist in handlers`);
    }
  }
});

test("ListTools public set is the chat whitelist, not the full catalog", () => {
  const publicTools = listPublicTools(TOOL_DEFINITIONS, TOOL_HANDLERS);
  const publicNames = publicTools.map(tool => tool.name);
  assert.notEqual(TOOL_DEFINITIONS.length, publicTools.length);
  assert.notEqual(publicTools.length, 77);
  assert.ok(publicTools.length < 30, `public ListTools too large: ${publicTools.length}`);
  assert.ok(TOOL_DEFINITIONS.length >= 77, `full catalog unexpectedly small: ${TOOL_DEFINITIONS.length}`);

  const expected = PUBLIC_LIST_TOOL_NAMES.filter(name => {
    if (name === "live_readiness_check") {
      return typeof TOOL_HANDLERS[name] === "function";
    }
    return TOOL_DEFINITIONS.some(tool => tool.name === name);
  });
  assert.deepEqual(publicNames, expected);
  for (const name of PRESSURE_TOOLS) {
    assert.ok(publicNames.includes(name));
  }
  assert.ok(publicNames.includes("simulate_protocol"));
  assert.ok(typeof TOOL_HANDLERS.live_readiness_check === "function");
  assert.ok(publicNames.includes("live_readiness_check"));
  assert.ok(!publicNames.includes("vision_check"));
  assert.ok(!publicNames.includes("runtime_watch_loop"));
  assert.ok(!publicNames.includes("generate_liquid_source_substitution_protocol"));
  assert.equal(typeof TOOL_HANDLERS.vision_check, "function");
  assert.equal(typeof TOOL_HANDLERS.runtime_watch_loop, "function");
});

test("run_pressure_trace(execute_on_robot=false) writes PRESSURE_CSV_B64 protocol", async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "pressure-run-"));
  const outputPath = path.join(tmp, "hover.py");
  const previous = process.env[PRESSURE_TRACE_ENV_FLAG];
  delete process.env[PRESSURE_TRACE_ENV_FLAG];
  try {
    const result = await TOOL_HANDLERS.run_pressure_trace({
      preset: "hover",
      well: "A1",
      hover_samples: 3,
      execute_on_robot: false,
      output_path: outputPath,
    });
    assert.equal(result.observation_only, true);
    assert.equal(result.resume_authority, false);
    assert.equal(result.data.observation_only, true);
    assert.equal(result.data.execute_on_robot, false);
    assert.equal(result.data.generated_protocol_path, outputPath);
    assert.equal(fs.existsSync(outputPath), true);
    const protocol = fs.readFileSync(outputPath, "utf8");
    assert.match(protocol, /PRESSURE_CSV_B64:/);
    assert.match(protocol, /read_stem_pressure/);
  } finally {
    if (previous === undefined) {
      delete process.env[PRESSURE_TRACE_ENV_FLAG];
    } else {
      process.env[PRESSURE_TRACE_ENV_FLAG] = previous;
    }
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test("run_pressure_trace execute_on_robot=true without env flag is rejected", async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "pressure-reject-"));
  const outputPath = path.join(tmp, "hover.py");
  const previous = process.env[PRESSURE_TRACE_ENV_FLAG];
  delete process.env[PRESSURE_TRACE_ENV_FLAG];
  try {
    await assert.rejects(
      () =>
        TOOL_HANDLERS.run_pressure_trace({
          preset: "hover",
          well: "A1",
          execute_on_robot: true,
          robot_ip: "127.0.0.1",
          output_path: outputPath,
        }),
      error => {
        assert.match(String(error.message), /OPENTRONS_ENABLE_PRESSURE_TRACE=1/);
        return true;
      },
    );
    assert.equal(fs.existsSync(outputPath), true);
  } finally {
    if (previous === undefined) {
      delete process.env[PRESSURE_TRACE_ENV_FLAG];
    } else {
      process.env[PRESSURE_TRACE_ENV_FLAG] = previous;
    }
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test("analyze_pressure_trace on fixture CSV returns observation_only", async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "pressure-analyze-"));
  const csvPath = path.join(tmp, "trace.csv");
  fs.writeFileSync(csvPath, `${FIXTURE_CSV}\n`);
  try {
    const result = await TOOL_HANDLERS.analyze_pressure_trace({
      csv_path: csvPath,
      moving_average_window: 1,
    });
    assert.equal(result.observation_only, true);
    assert.equal(result.resume_authority, false);
    assert.equal(result.data.observation_only, true);
    assert.equal(result.data.resume_authority, false);
    assert.ok(result.data.advisory_features);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});
