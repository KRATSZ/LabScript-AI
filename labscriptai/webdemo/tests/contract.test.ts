import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (rel: string) => readFileSync(path.join(root, rel), "utf8");

describe("demo contract lock", () => {
  it("four robots, seven tools, Plan IR fallback for OT when 8010 down", () => {
    const session = read("server/src/session.ts");
    assert.match(session, /Hamilton/);
    assert.match(session, /Tecan/);
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

    const backend = read("server/src/backend.ts");
    assert.match(backend, /runPlanCli/);
    assert.match(backend, /validatePlan/);
    assert.match(backend, /runPlanChecks/);
    assert.match(backend, /eval_plan\.py/);

    const types = read("web/src/types.ts");
    assert.match(types, /^\s*plan:/m);

    const prompt = read("server/src/prompt.ts");
    assert.match(prompt, /Which robot — OT-2, Flex, Hamilton, or Tecan\?/);
    assert.match(prompt, /Hamilton/);
    assert.match(prompt, /emit_plan/);
    assert.match(prompt, /generate_code \(8010 Python\)/);
    assert.match(prompt, /Do not change volumes, wells, or counts the user gave/);
    assert.match(prompt, /Do not skip generate_code/);
    assert.match(prompt, /emit_plan → run_checks/);
    assert.match(prompt, /Watch\/animation is unavailable/);
    assert.doesNotMatch(prompt, /Default path for EVERY robot/);

    const tools = read("server/src/tools.ts");
    assert.match(tools, /Preferred for OT-2 and Flex/);
    assert.match(tools, /Allowed for OT-2\/Flex when 8010 is down/);
    assert.match(tools, /Do not prefer a stored plan/);
    assert.match(tools, /generateCode, emitPlan, runChecksTool/);
    assert.match(tools, /Hamilton/);
    assert.match(tools, /Tecan/);
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
  });
});
