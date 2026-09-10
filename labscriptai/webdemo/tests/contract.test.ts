import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (rel: string) => readFileSync(path.join(root, rel), "utf8");

describe("demo contract lock", () => {
  it("OT-2/Flex must use 8010 Python, not emit_plan", () => {
    const session = read("server/src/session.ts");
    assert.match(session, /if \(isOpentrons\(session\)\) \{\s*return session\.code\?\.trim\(\) \? "opentrons" : "blocked"/);
    assert.match(session, /&& !isOpentrons\(session\)/);

    const prompt = read("server/src/prompt.ts");
    assert.match(prompt, /Which robot — OT-2 or Flex\?/);
    assert.match(prompt, /generate_code \(8010 Python\)/);
    assert.match(prompt, /Do not skip generate_code/);
    assert.match(prompt, /Do not call emit_plan for OT-2 or Flex/);
    assert.doesNotMatch(prompt, /Default path for EVERY robot/);
    assert.doesNotMatch(prompt, /MUST emit_plan/);

    const tools = read("server/src/tools.ts");
    assert.match(tools, /Preferred for OT-2 and Flex/);
    assert.match(tools, /Not for OT-2 or Flex/);
    assert.match(tools, /Do not prefer a stored plan/);
    assert.match(tools, /generateCode, emitPlan/);
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
  });
});
