import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SYSTEM_PROMPT } from "../server/src/prompt.ts";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (rel: string) => readFileSync(path.join(root, rel), "utf8");

describe("demo contract lock", () => {
  it("four robots, seven tools, Plan IR fallback for OT when 8010 down", () => {
    const session = read("server/src/session.ts");
    assert.match(session, /canEmitPlan/);
    assert.match(session, /planBackendFor/);
    assert.match(session, /plan\?:/);
    assert.match(session, /plan: session\.plan/);
    assert.match(session, /diti/);
    assert.match(
      session,
      /if \(isOpentrons\(session\) && session\.code\?\.trim\(\)\) return "opentrons"/
    );
    assert.doesNotMatch(session, /&& !isOpentrons\(session\)/);

    const devices = read("server/src/devices.ts");
    assert.match(devices, /Hamilton/);
    assert.match(devices, /Tecan/);
    assert.match(devices, /DEVICE_REGISTRY/);
    assert.match(devices, /tecan_fluent/);
    assert.match(devices, /pyfluent_compile/);
    assert.match(devices, /artifactExt: "\.gwl"/);
    assert.doesNotMatch(devices, /compiler pending \(R4\)/);
    assert.match(devices, /diti/);

    const backend = read("server/src/backend.ts");
    assert.match(backend, /runPlanCli/);
    assert.match(backend, /validatePlan/);
    assert.match(backend, /runPlanChecks/);
    assert.match(backend, /runFluentCompile/);
    assert.match(backend, /compile_fluent\.py/);
    assert.match(backend, /runHamiltonCompile/);
    assert.match(backend, /compile_hamilton\.py/);
    assert.match(backend, /eval_plan\.py/);

    const types = read("web/src/types.ts");
    assert.match(types, /^\s*plan:/m);

    const prompt = read("server/src/prompt.ts");
    assert.doesNotMatch(SYSTEM_PROMPT, /Which robot/);
    assert.doesNotMatch(SYSTEM_PROMPT, /If robot is unset/);
    assert.match(SYSTEM_PROMPT, /Never ask which machine/);
    assert.match(SYSTEM_PROMPT, /volumes, wells, sample counts/);
    assert.match(SYSTEM_PROMPT, /Hamilton: step JSON \+ runnable PyLabRobot script \(\.py\)/);
    assert.match(SYSTEM_PROMPT, /Deliverables:/);
    assert.match(SYSTEM_PROMPT, /OT-2: Python \(\.py\), Watch\/animation/);
    assert.match(SYSTEM_PROMPT, /Tecan: \.gwl worklist \+ step JSON, no Watch/);
    assert.ok(SYSTEM_PROMPT.trim().split("\n").length <= 32);
    assert.match(prompt, /emit_plan/);
    assert.match(prompt, /generate_code \(8010 Python\)/);
    assert.match(SYSTEM_PROMPT, /Patch only mechanical issues/);
    assert.match(SYSTEM_PROMPT, /Never change volumes, wells, counts/);
    assert.match(SYSTEM_PROMPT, /each user message gives you one fresh patch-and-recheck/i);
    assert.match(SYSTEM_PROMPT, /review\.match=false/);
    assert.match(SYSTEM_PROMPT, /call open_animation immediately/);
    assert.match(SYSTEM_PROMPT, /do not ask permission/);
    assert.match(SYSTEM_PROMPT, /refuses to adjust/);
    assert.match(SYSTEM_PROMPT, /do not keep asking/);
    assert.match(SYSTEM_PROMPT, /compress by column with multi-well lists/i);
    assert.match(SYSTEM_PROMPT, /no small character limit/i);
    assert.match(SYSTEM_PROMPT, /mode:"append"/);
    assert.match(SYSTEM_PROMPT, /DROP_TIPS must come before PICK_TIPS/);
    assert.match(
      SYSTEM_PROMPT,
      /DROP_TIPS \(if tips held\) → PICK_TIPS → ASPIRATE → DISPENSE → optional MIX/
    );
    assert.match(SYSTEM_PROMPT, /PICK_TIPS count must equal the number of transfer rounds/);
    assert.match(SYSTEM_PROMPT, /never aspirate without a just-picked tip/);
    assert.match(prompt, /Do not skip generate_code/);
    assert.match(prompt, /emit_plan → run_checks/);
    assert.match(prompt, /Watch\/animation is unavailable/);
    assert.doesNotMatch(prompt, /Default path for EVERY robot/);

    const tools = read("server/src/tools.ts");
    assert.match(tools, /Do not ask which robot/);
    assert.match(tools, /Preferred for OT-2 and Flex/);
    assert.match(tools, /Allowed for OT-2\/Flex when 8010 is down/);
    assert.match(tools, /Do not prefer a stored plan/);
    assert.match(tools, /generateCode, emitPlan, runChecksTool/);
    assert.match(tools, /Hamilton/);
    assert.match(tools, /Tecan/);
    assert.match(tools, /runnable PyLabRobot script/);
    assert.match(tools, /"tip_positions":\["A1"\]/);
    assert.match(tools, /never "TIPS:A1"/);
    assert.match(tools, /tip_rack is the tiprack resource id/);
    assert.match(tools, /dependencies may be \[\]/);
    assert.match(tools, /mode defaults to "replace"/);
    assert.match(tools, /mode:"append"/);
    assert.match(tools, /DROP_TIPS must come first/);
    assert.match(tools, /Tecan standard wells: 96-well plate 360/);
    assert.match(tools, /1000 µL DiTi/);
    assert.match(tools, /must_call: "emit_plan"/);
    assert.match(tools, /Call emit_plan then run_checks/);
    assert.doesNotMatch(tools, /8010_unreachable/);
    assert.doesNotMatch(tools, /Preferred path for every robot/);
  });

  it("scientist-facing copy names all four robots", () => {
    const blob = ["web/src/App.tsx", "web/src/StartForm.tsx", "web/src/ChatPane.tsx", "web/src/startExamples.ts"]
      .map(read)
      .join("\n");
    assert.match(blob, /OT-2/);
    assert.match(blob, /Flex/);
    assert.match(blob, /Hamilton/);
    assert.match(blob, /Tecan/);
    assert.match(read("web/src/App.tsx"), /robot=\{session\?\.robot\}/);
    assert.match(read("web/src/analysis.ts"), /robotHint/);
    assert.match(read("web/src/App.tsx"), /Code service offline — animation unavailable/);
    assert.match(read("web/src/artifacts.ts"), /export function downloadable/);
    assert.match(read("web/src/pipelineLogic.ts"), /Checks passed — step table below/);
    assert.match(read("web/src/pipelineLogic.ts"), /Cannot verify/);
    assert.doesNotMatch(read("web/src/ExportsPanel.tsx"), /Watch is Opentrons-only/);
    assert.match(read("web/src/StartForm.tsx"), /DEVICE_CARDS/);
    assert.match(read("web/src/StartForm.tsx"), /Pick a robot first/);
    assert.doesNotMatch(read("web/src/StartForm.tsx"), /Robot is asked in chat/);
    assert.match(read("web/src/App.tsx"), /Change device/);
    assert.match(read("web/src/types.ts"), /export interface StartInput/);
    assert.match(read("web/src/types.ts"), /export interface DeviceCard/);
    assert.match(read("web/src/api.ts"), /StartInput/);
    assert.match(read("server/src/index.ts"), /invalid robot/);
    assert.match(read("server/src/index.ts"), /robot: body\.robot/);
  });
});
