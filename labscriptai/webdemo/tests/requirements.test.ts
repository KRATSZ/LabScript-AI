import { it } from "node:test";
import assert from "node:assert/strict";
import { analyzeRequirementIssues, capacityBlocker, groundPlanCapacities, planRequirementIssues, readUserRequirements, retainInitialConditions } from "../server/src/requirements.ts";
import { applyAskUser, applyForm, beginAuthoringTurn, chosenVolumeInText, createSession, goalNotesVolumeConflict, intakeOpen, markIntakeReply, reviewIntent, unresolvedGoalNotesConflict } from "../server/src/session.ts";
import { applyRequirementIssues, pipetteHardwareIssues } from "../server/src/backend.ts";
import { needsPatch, wrapChecks } from "../server/src/gate.ts";
import { checkedReply } from "../server/src/tools.ts";

it("retains original inventory independently of a model rewrite and exports it", () => {
  const s = createSession();
  applyForm(s, { robot: "Flex", goal: "Transfer 80 µL from A1 to B1", doc: "- Reagents: 水，D2/A1，100 µL；D2/B1，0 µL（空）\n1. Transfer 80 µL D2/A1 to D2/B1, no mixing." });
  assert.deepEqual(s.requirements?.initial, [{ location: "D2/A1", ul: 100 }, { location: "D2/B1", ul: 0 }]);
  markIntakeReply(s, "confirmed");
  beginAuthoringTurn(s, "Change the volume to 50 µL");
  applyAskUser(s, { goal: "Transfer 50 µL from A1 to B1", doc: "none" });
  assert.equal(s.requirements?.transferUl, 50);
  assert.equal(s.requirements?.initial[0].ul, 100);
  assert.match(reviewIntent(s), /100 µL initial volume/);
  assert.match(retainInitialConditions("Transfer 50 µL", s.requirements), /D2\/A1: 100 µL initial volume/);
});

it("blocks incompatible capacity with a complete recovery message before generation", () => {
  const f = readUserRequirements("Transfer 250 µL water from reservoir A1 to empty well B1 of a 200 µL 96-well plate. Keep the entire 250 µL; do not split or reduce it.");
  assert.equal(f.wellCapacityUl, 200);
  assert.equal(f.destination, "B1");
  assert.equal(f.transferUl, 250);
  assert.equal(f.noSplit, true);
  assert.match(capacityBlocker(f)!, /larger destination together with compatible pipettes and tips/);
  assert.match(capacityBlocker(f)!, /Splitting into the same well still overflows/);
  const amended = readUserRequirements("Change the transfer to 150 µL", f);
  assert.equal(capacityBlocker(amended), null);
  assert.equal(amended.wellCapacityUl, 200);
  assert.equal(amended.noSplit, true);
  const chinese = readUserRequirements("同意改为每孔 150 µL，仍然从储液槽 A1 到 B1，其余条件保持不变。", f);
  assert.equal(chinese.transferUl, 150);
  assert.equal(capacityBlocker(chinese), null);
});

it("rejects a model-inflated plate and a split plan even if their internal ledger passes", () => {
  const f = readUserRequirements("Transfer 250 µL from A1 to B1 in a 200 µL plate; do not split");
  const issues = planRequirementIssues({ resources: [{ id: "plate", type: "plate", slot: "2", max_volume_ul: 360 }], initial_volumes_ul: { "plate:B1": 0 }, steps: [
    { primitive_type: "DISPENSE", destination: "plate:B1", volume_ul: 125 },
    { primitive_type: "DISPENSE", destination: "plate:B1", volume_ul: 125 },
  ] }, f);
  assert.equal(issues.length, 3);
  assert.match(issues.join(" "), /capacity 360/);
  assert.match(issues.join(" "), /prohibited splitting/);
  assert.match(issues.join(" "), /exceeding user-specified or labware 200/);
  const logic = applyRequirementIssues({ outcome: "pass", logic_pass: true, final_pass_v2: true }, issues);
  const checks = wrapChecks({ ok: true }, logic, {});
  assert.equal(checks.status, "fail");
  assert.equal(needsPatch(checks), false, "cannot patch by changing a human constraint");
});

it("validates source initial state and the revised total in plan output", () => {
  const f = readUserRequirements("Transfer 80 µL from A1 to B1", readUserRequirements("Reagents: D2/A1, 100 µL; D2/B1, 0 µL"));
  const p = { resources: [{ id: "plate", type: "plate", slot: "D2", max_volume_ul: 200 }], initial_volumes_ul: { "plate:A1": 80, "plate:B1": 0 }, steps: [{ primitive_type: "DISPENSE", destination: "plate:B1", volume_ul: 50 }] };
  assert.equal(planRequirementIssues(p, f).length, 2);
  p.initial_volumes_ul["plate:A1"] = 100;
  p.steps[0].volume_ul = 80;
  assert.deepEqual(planRequirementIssues(p, f), []);
});

it("grounds a valid recovery in the user's actual capacity without editing transfer steps", () => {
  const f = readUserRequirements("Transfer 150 µL from A1 to B1 in a 200 µL plate; do not split");
  const plan = { resources: [{ id: "plate", type: "plate", max_volume_ul: 360, slot: "2" }], steps: [{ primitive_type: "DISPENSE", destination: "plate:B1", volume_ul: 150 }] };
  const grounded = groundPlanCapacities(plan, f);
  assert.equal(grounded.resources[0].max_volume_ul, 200);
  assert.equal(plan.resources[0].max_volume_ul, 360, "do not mutate the model's input");
  assert.equal(grounded.steps, plan.steps, "steps are unchanged");
  assert.deepEqual(planRequirementIssues(grounded, f), []);
  plan.resources[0].max_volume_ul = 100;
  assert.equal(groundPlanCapacities(plan, f).resources[0].max_volume_ul, 100, "cannot enlarge a smaller known resource");
  plan.steps[0].volume_ul = 250;
  assert.ok(planRequirementIssues(groundPlanCapacities(plan, f), f).length > 0, "over-capacity steps remain blocked");
});

it("parses comma-separated inventories and an ordinary single sample well", () => {
  const f = readUserRequirements("Transfer 50 µL from A1 to sample well B1", readUserRequirements("Reagents: water D2/A1, 100 µL, buffer D2/B1, 0 µL"));
  assert.equal(f.transferUl, 50);
  assert.equal(f.destination, "B1");
  assert.deepEqual(f.initial, [{ location: "D2/A1", ul: 100 }, { location: "D2/B1", ul: 0 }]);
});

it("projects actual Opentrons commands from user inventory and checks net liquid in order", () => {
  const f = readUserRequirements("Transfer 50 µL from A1 to B1", readUserRequirements("Reagents: D2/A1, 100 µL, D2/B1, 180 µL"));
  const a = { labware: [{ id: "p", location: { slotName: "D2" }, loadName: "nest_96_wellplate_200ul_flat" }], commands: [
    { commandType: "aspirate", params: { labwareId: "p", wellName: "A1", volume: 50 } },
    { commandType: "dispense", params: { labwareId: "p", wellName: "B1", volume: 50 } },
  ] };
  assert.match(analyzeRequirementIssues(a, f).join(" "), /230 µL/);
  f.initial[0].ul = 20;
  assert.match(analyzeRequirementIssues(a, f).join(" "), /aspirated below/);
  const p = { resources: [{ id: "p", type: "plate", slot: "D2", max_volume_ul: 200 }], initial_volumes_ul: { "p:A1": 200 }, steps: [
    { primitive_type: "ASPIRATE", source: "p:A1", volume_ul: 100 },
    { primitive_type: "DISPENSE", destination: "p:A1", volume_ul: 100 },
  ] };
  assert.deepEqual(planRequirementIssues(p, { initial: [], wellCapacityUl: 200 }), [], "withdraw then replace is not an overflow");
});

it("uses the human's conflict choice in checks without rewriting unrelated source inventory", async () => {
  const s = createSession();
  applyForm(s, { robot: "Hamilton", goal: "Transfer 50 µL from A1 to B1", doc: "Transfer 80 µL from A1 to B1" });
  const ask = (await import("../server/src/tools.ts")).buildTools(s, { write() {}, close() {} }).find(t => t.name === "ask_user")!;
  await ask.execute("question", {});
  const { markConflictUserReply } = await import("../server/src/session.ts");
  markConflictUserReply(s, "Use 80 µL, not 50 µL");
  await ask.execute("choice", { goal: "Transfer 80 µL from A1 to B1" });
  assert.equal(s.requirements?.transferUl, 80);
  assert.deepEqual(planRequirementIssues({ resources: [{ id: "plate", type: "plate", slot: "2", max_volume_ul: 360 }], steps: [{ primitive_type: "DISPENSE", destination: "plate:B1", volume_ul: 80 }] }, s.requirements), []);
});

it("parses slash-separated source well inventories without confusing wells with Flex slots", () => {
  const f = readUserRequirements("源板A1/B1/C1/D1各初始150 µL；目标板A2/B2/C2/D2为空。");
  assert.deepEqual(f.initial.map(v => v.location), ["A1", "B1", "C1", "D1", "A2", "B2", "C2", "D2"]);
  assert.deepEqual(f.initial.slice(4).map(v => v.ul), [0, 0, 0, 0]);
  const plan = { resources: [{ id: "source", type: "plate", slot: "2", max_volume_ul: 200 }, { id: "target", type: "plate", slot: "4", max_volume_ul: 200 }], initial_volumes_ul: Object.fromEntries([...['A1', 'B1', 'C1', 'D1'].map(w => [`source:${w}`, 150]), ...['A2', 'B2', 'C2', 'D2'].map(w => [`target:${w}`, 0])]), steps: ["A", "B", "C", "D"].flatMap(row => [
    { primitive_type: "ASPIRATE", source: `source:${row}1`, volume_ul: 50 }, { primitive_type: "DISPENSE", destination: `target:${row}2`, volume_ul: 50 },
  ]) };
  assert.deepEqual(planRequirementIssues(plan, f), []);
  assert.equal(readUserRequirements("Reagents: D2/A1, 100 µL").initial[0].location, "D2/A1");
});

it("keeps the form document immutable so model-generated old notes cannot reopen a recovery conflict", () => {
  const s = createSession();
  const goal = "Tecan Fluent：从 reservoir A1 转移250 µL到 plate B1；目标 B1 初始为空，B1 容量200 µL。要求不减量、不拆分。";
  applyForm(s, { robot: "Tecan", goal });
  assert.equal(s.requirements?.wellCapacityUl, 200);
  assert.deepEqual(s.requirements?.initial, [{ location: "B1", ul: 0 }]);
  applyAskUser(s, { doc: goal });
  assert.equal(s.doc, "none");
  beginAuthoringTurn(s, "同意恢复：将每孔转移量改为150 µL，其余条件保持不变（目标 B1 初始为空，仍不拆分）。");
  applyAskUser(s, { goal: "从 reservoir A1 转移150 µL到 plate B1；B1容量200 µL，初始0 µL", doc: goal });
  assert.equal(s.doc, "none");
  assert.equal(s.requirements?.transferUl, 150);
  assert.equal(capacityBlocker(s.requirements), null);
  assert.equal(unresolvedGoalNotesConflict(s), null);
  assert.equal(chosenVolumeInText("最终选用150 µL。200 µL仅是B1容量，0 µL是B1初始量，250 µL是已放弃的原始请求", [200, 150, 0, 250]), 150);
  assert.equal(chosenVolumeInText("Do not use 150. Use 250 µL", [150, 250]), 250);
  assert.equal(chosenVolumeInText("Use 200 µL tips, transfer 150 µL. The target initially has 0 µL.", [200, 150, 0, 250]), 150);
  assert.deepEqual(readUserRequirements("B1容量200 µL，初始0 µL").initial, [{ location: "B1", ul: 0 }]);
  assert.deepEqual(readUserRequirements("B1初始180 µL，孔容量200 µL").initial, [{ location: "B1", ul: 180 }]);
});

it("does not treat reagent per-sample volumes or final state as inventory", () => {
  const f = readUserRequirements("Transfer 20 µL to each of 8 samples A1–H1.\nReagents: water C1/A1, 10 µL/孔; premix C1/A2, 8 µL/孔\nFinal D2/A1 remaining 20 µL");
  assert.equal(f.transferUl, undefined);
  // Per-well recipe quantities are not initial source inventory.
  assert.equal(f.initial.length, 0);
});

it("does not ask users to choose between transfer volume and a reagent inventory row", () => {
  assert.equal(goalNotesVolumeConflict("Transfer 50 µL A1 to B1", "Reagents: 2/A1, 150 µL; 2/B1, 0 µL"), null);
  assert.ok(goalNotesVolumeConflict("Transfer 50 µL A1 to B1", "Reagents: 2/A1, 150 µL\nTransfer 80 µL to B1"));
});

it("requires confirmation for a proposed different pipette and catches silent code substitutions", () => {
  const s = createSession();
  applyForm(s, { robot: "Flex", goal: "Transfer 2 µL A1 to B1" });
  markIntakeReply(s, "confirmed");
  applyAskUser(s, { goal: s.goal, left_pipette: "flex_1channel_50" });
  assert.equal(intakeOpen(s), true);
  const a = { pipettes: [{ mount: "left", pipetteName: "p1000_single_flex" }] };
  assert.equal(pipetteHardwareIssues(a, s.hardware).length, 1);
  a.pipettes[0].pipetteName = "p50_single_flex";
  assert.deepEqual(pipetteHardwareIssues(a, s.hardware), []);
});

it("reports only the files actually available and only opens a checked Opentrons preview", () => {
  const s = createSession();
  applyForm(s, { robot: "Hamilton", goal: "Transfer 50 µL" });
  s.plan = { steps: [] };
  const checks = wrapChecks({ ok: true }, { outcome: "pass", logic_pass: true, final_pass_v2: true }, {});
  const events: Array<[string, any]> = [];
  const sink = { write(e: string, d: any) { events.push([e, d]); }, close() {} };
  const result = checkedReply(s, checks, sink);
  assert.equal(result.terminate, true);
  assert.match(events.at(-1)![1].token, /step JSON/);
  assert.doesNotMatch(events.at(-1)![1].token, /PyLabRobot|deck|remaining|left in/);
  assert.equal(events.filter(e => e[0] === "animation").length, 0);
  s.robot = "OT-2";
  s.code = "protocol";
  s.analyze = { commands: [{ commandType: "aspirate" }] };
  checkedReply(s, checks, sink);
  assert.equal(events.filter(e => e[0] === "animation").length, 1);
});
