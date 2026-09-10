import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (rel: string) => readFileSync(path.join(root, rel), "utf8");

describe("demo contract lock", () => {
  it("OT-2/Flex use 8010 Python; six tools; auto-deck", () => {
    const session = read("server/src/session.ts");
    assert.match(session, /session\.code\?\.trim\(\) \? "opentrons" : "blocked"/);
    assert.match(session, /function assumeStandardDeck|deckAssumed/);
    assert.doesNotMatch(session, /Hamilton/);
    assert.doesNotMatch(session, /Tecan/);
    assert.doesNotMatch(session, /canEmitPlan/);
    assert.doesNotMatch(session, /planBackendFor/);
    assert.doesNotMatch(session, /plan\?:/);
    assert.doesNotMatch(session, /plan: session\.plan/);
    assert.doesNotMatch(session, /diti/);

    const backend = read("server/src/backend.ts");
    assert.doesNotMatch(backend, /runPlanCli/);
    assert.doesNotMatch(backend, /validatePlan/);
    assert.doesNotMatch(backend, /runPlanChecks/);
    assert.doesNotMatch(backend, /eval_plan\.py/);

    const types = read("web/src/types.ts");
    assert.doesNotMatch(types, /^\s*plan:/m);

    const prompt = read("server/src/prompt.ts");
    assert.match(prompt, /Which robot — OT-2 or Flex\?/);
    assert.match(prompt, /I'll assume a standard deck/);
    assert.match(prompt, /assumed_deck=true/);
    assert.match(prompt, /generate_code \(8010 Python\)/);
    assert.match(prompt, /Do not change volumes, wells, or counts the user gave/);
    assert.match(prompt, /No bash\. No robot\. No live Flex\./);
    assert.match(prompt, /Replies stay short/);
    assert.match(prompt, /Do not skip generate_code/);
    assert.doesNotMatch(prompt, /emit_plan/);
    assert.doesNotMatch(prompt, /Hamilton/);
    assert.doesNotMatch(prompt, /Tecan/);
    assert.doesNotMatch(prompt, /Plan IR/);
    assert.doesNotMatch(prompt, /Default path for EVERY robot/);

    const tools = read("server/src/tools.ts");
    assert.match(tools, /Preferred for OT-2 and Flex/);
    assert.match(tools, /8010 Python/);
    assert.match(tools, /askUser, generateSop, generateCode, runChecksTool, skillTool, openAnimation/);
    assert.doesNotMatch(tools, /emitPlan/);
    assert.doesNotMatch(tools, /emit_plan/);
    assert.doesNotMatch(tools, /Hamilton/);
    assert.doesNotMatch(tools, /Tecan/);
    assert.doesNotMatch(tools, /must_call/);
    assert.doesNotMatch(tools, /8010_unreachable/);
    assert.doesNotMatch(tools, /Preferred path for every robot/);
  });

  it("scientist-facing copy stays OT-2 or Flex", () => {
    const blob = ["web/src/App.tsx", "web/src/StartForm.tsx", "web/src/ChatPane.tsx", "web/src/startExamples.ts"]
      .map(read)
      .join("\n");
    assert.match(blob, /OT-2 or Flex/);
    assert.doesNotMatch(blob, /Hamilton/);
    assert.doesNotMatch(blob, /Tecan/);
    assert.match(read("web/src/App.tsx"), /robot=\{session\?\.robot\}/);
    assert.match(read("web/src/analysis.ts"), /robotHint/);
    assert.match(read("web/src/App.tsx"), /Code service offline — animation unavailable/);
  });
});
