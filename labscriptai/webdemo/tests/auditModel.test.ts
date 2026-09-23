import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { checksAudit } from "../web/src/auditModel.ts";

const pass = {
  status: "pass" as const,
  sim: { ok: true },
  logicpass: { outcome: "pass" },
  statepass: {},
  compile: { ok: true, stage: "gwl" },
};

describe("checksAudit", () => {
  it("lists simulation, logic, state, compile, assumptions, and authoring-only unverified items", () => {
    const session = {
      robot: "Hamilton" as const,
      goal: "Transfer 50 µL from A1 to B1",
      hardware: { deck: { "1": "tips" } },
      deck_assumed: true,
      checks: pass,
    };
    const model = checksAudit(pass, session);
    assert.ok(model);
    assert.deepEqual(
      model.checks.map((row) => row.key),
      ["sim", "logic", "state", "compile"]
    );
    assert.equal(model.checks[0].tone, "pass");
    assert.ok(model.assumptions.some((line) => /50 µL/.test(line) && /A1/.test(line)));
    assert.ok(model.unverified.some((line) => /not a live-hardware safety clearance/i.test(line)));
    assert.ok(model.unverified.some((line) => /authoring-only/i.test(line)));
  });

  it("marks a failed check and still lists the rest", () => {
    const model = checksAudit({
      ...pass,
      status: "fail",
      logicpass: { outcome: "fail", reason: "tip order" },
    });
    assert.ok(model);
    const logic = model.checks.find((row) => row.key === "logic");
    assert.equal(logic?.tone, "fail");
    assert.match(logic?.result || "", /Failed/);
    assert.match(logic?.result || "", /tip order/);
  });
});
