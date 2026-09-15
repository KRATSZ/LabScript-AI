import { Type } from "typebox";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import type { AgentTool, AgentToolResult } from "@earendil-works/pi-agent-core";
import {
  generateCodeStream,
  generateCompactSop,
  patchCodeViaConverse,
  runChecks,
  runPlanChecks,
  validatePlan,
} from "./backend.ts";
import { loadDemoEnv } from "./env.ts";
import {
  animationAllowed,
  compactChecks,
  isReviewMismatch,
  needsPatch,
  PATCH_BUDGET_REFUSAL,
  PATCH_CAP,
  patchCapHit,
  patchInstruction,
  refuseEmptySop,
} from "./gate.ts";
import { DEVICE_REGISTRY, deviceFor } from "./devices.ts";
import {
  applyAskUser,
  authoringGoal,
  beginGoalNotesConflictAsk,
  canEmitPlan,
  canGenerateCode,
  canResolveGoalNotesConflict,
  canRunPipeline,
  reviewIntent,
  checksRoute,
  capSop,
  explainPlanErrors,
  formatHardwareConfig,
  isOpentrons,
  missingList,
  normalizePlanInput,
  planBackendFor,
  presetMismatchWarning,
  resolveGoalNotesConflict,
  shouldCallCompactSop,
  shouldReuseSop,
  snapshot,
  unresolvedGoalNotesConflict,
  type AskUserInput,
  type SessionState,
} from "./session.ts";
import type { SseWriter } from "./sse.ts";

type ToolResult = AgentToolResult<Record<string, unknown>>;

function ok(payload: unknown): ToolResult {
  return {
    content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
    details: { payload },
  };
}

function refusePatchBudget(): ToolResult {
  return {
    content: [{ type: "text", text: PATCH_BUDGET_REFUSAL }],
    details: { refused: true, next: "done" },
    terminate: true,
  };
}

function toolGoal(session: SessionState): string {
  return authoringGoal(session);
}

function unionLiterals(values: string[]) {
  return Type.Union(
    values.map((v) => Type.Literal(v)) as [ReturnType<typeof Type.Literal>, ReturnType<typeof Type.Literal>]
  );
}

const PYTHON_ROBOTS = DEVICE_REGISTRY.filter((d) => d.codegen === "opentrons_python").map((d) => d.legacyRobot);
const PLAN_ROBOTS = DEVICE_REGISTRY.filter((d) => d.codegen === "plan_ir").map((d) => d.legacyRobot);

export function buildTools(session: SessionState, sse: SseWriter): AgentTool[] {
  const askUser: AgentTool = {
    name: "ask_user",
    label: "Ask user / session",
    description:
      "Persist session fields. Do not ask which robot — the user already picked one at start. robot is only for a mid-chat switch the user requested (state-setting, not a question). Passing robot with no custom deck assumes that family's standard layout (assumed_deck=true). Pass deck only when the protocol names labware the assumed deck lacks. If notes_conflict, call this, tell the user both volumes, and stop; after they answer, call again with goal set to the chosen volume. Does not generate code. No deck UI.",
    parameters: Type.Object({
      goal: Type.Optional(Type.String()),
      doc: Type.Optional(Type.String({ description: "SOP draft text, or 'none'" })),
      robot: Type.Optional(unionLiterals(DEVICE_REGISTRY.map((d) => d.legacyRobot))),
      preset: Type.Optional(unionLiterals(DEVICE_REGISTRY.map((d) => d.hardwarePreset.id))),
      left_pipette: Type.Optional(Type.String()),
      right_pipette: Type.Optional(Type.String()),
      use_gripper: Type.Optional(Type.Boolean()),
      api_version: Type.Optional(Type.String()),
      deck: Type.Optional(
        Type.Array(
          Type.Object({
            slot: Type.String(),
            labware: Type.String(),
          })
        )
      ),
    }),
    executionMode: "sequential",
    execute: async (_id, args) => {
      const input = args as AskUserInput;
      const warning = presetMismatchWarning(session.robot, input.preset);
      const conflictBefore = unresolvedGoalNotesConflict(session);
      if (conflictBefore && !canResolveGoalNotesConflict(session, input.goal)) {
        applyAskUser(session, { ...input, goal: undefined, doc: undefined });
        beginGoalNotesConflictAsk(session);
        const waitingForChoice = Boolean(session.conflictUserReplied);
        const ask = waitingForChoice
          ? `I still need to record the chosen volume (${conflictBefore}). Which should I use? I have not made a SOP, plan, or .gwl.`
          : `The goal and notes disagree on volume (${conflictBefore}). Which volume should I use? I have not made a SOP, plan, or .gwl.`;
        sse.write("text", { token: `\n\n${ask}\n` });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  wait: true,
                  conflict: conflictBefore,
                  ask,
                  next_tool: "ask_user",
                  phase: session.phase,
                  missing: missingList(session),
                  ready: false,
                  hint: waitingForChoice
                    ? "Call ask_user with goal set to the volume the user chose. Do not generate_sop, emit_plan, run_checks, or a .gwl."
                    : "Stop. Tell the user both volumes and wait. Do not generate_sop, emit_plan, run_checks, or a .gwl.",
                },
                null,
                2
              ),
            },
          ],
          details: {
            payload: {
              wait: true,
              conflict: conflictBefore,
              ask,
              next_tool: "ask_user",
              ready: false,
            },
          },
          terminate: true,
        };
      }
      applyAskUser(session, input);
      if (conflictBefore) {
        resolveGoalNotesConflict(session);
      }
      return ok({
        phase: session.phase,
        missing: missingList(session),
        ready: canRunPipeline(session) && !unresolvedGoalNotesConflict(session),
        hardware_config: formatHardwareConfig(session),
        doc: session.doc ?? null,
        assumed_deck: Boolean(session.deckAssumed),
        ...(warning ? { warning } : {}),
      });
    },
  };

  const generateSop: AgentTool = {
    name: "generate_sop",
    label: "Generate SOP",
    description:
      "Write a compact SOP from the session goal after phase=ready. Notes/doc are a draft only — do not copy intern junk. Skip if a generated sop is already stored unless force=true. Blocked without robot/slots (returns JSON, does not throw, does not call DeepSeek).",
    parameters: Type.Object({
      force: Type.Optional(Type.Boolean()),
    }),
    executionMode: "sequential",
    execute: async (_id, args, _signal, onUpdate) => {
      const force = Boolean((args as { force?: boolean }).force);
      const conflict = unresolvedGoalNotesConflict(session);
      if (conflict) {
        return ok({
          blocked: true,
          missing: missingList(session),
          conflict,
          hint: "Notes conflict with the goal. Call ask_user and wait. Do not emit a .gwl.",
        });
      }
      if (shouldReuseSop(session, force)) {
        return ok({
          chars: session.sop?.length ?? 0,
          skipped: true,
          sop_markdown: session.sop,
        });
      }
      if (!shouldCallCompactSop(session, force)) {
        return ok({ blocked: true, missing: missingList(session) });
      }
      const sop = await generateCompactSop(
        formatHardwareConfig(session),
        toolGoal(session),
        (token, source) => {
          sse.write("thinking", { token, source });
          onUpdate?.({ content: [{ type: "text", text: token }], details: { source } });
        }
      );
      if (!sop) throw new Error("generate_sop returned empty SOP");
      session.sop = capSop(sop);
      sse.write("snapshot", snapshot(session));
      return ok({ chars: session.sop.length, sop_markdown: session.sop });
    },
  };

  const generateCode: AgentTool = {
    name: "generate_code",
    label: "Generate Opentrons Python",
    description:
      "Preferred for OT-2 and Flex. Call 8010 for Opentrons Python, then run_checks. Returns {chars, patched, skipped?} or {blocked, hint}.",
    parameters: Type.Object({
      instruction: Type.Optional(Type.String()),
    }),
    executionMode: "sequential",
    execute: async (_id, args, _signal, onUpdate) => {
      const conflict = unresolvedGoalNotesConflict(session);
      if (conflict) {
        return ok({
          blocked: true,
          missing: missingList(session),
          conflict,
          hint: "Notes conflict with the goal. Call ask_user and wait. Do not emit a .gwl.",
        });
      }
      if (!canRunPipeline(session)) {
        return ok({ blocked: true, missing: missingList(session) });
      }
      if (deviceFor(session.robot)?.codegen !== "opentrons_python") {
        return ok({
          blocked: true,
          missing: [`emit_plan — ${PLAN_ROBOTS.join("/")} use Plan IR, not Opentrons Python`],
        });
      }
      const refused = refuseEmptySop(session.sop);
      if (refused || !canGenerateCode(session)) {
        const missing = missingList(session);
        if (refused) missing.push("sop");
        return ok({ blocked: true, missing });
      }
      if (patchCapHit(session.patchesUsed ?? 0, session.lastChecks)) {
        return refusePatchBudget();
      }
      const instruction = String((args as { instruction?: string }).instruction ?? "").trim();
      const existing = session.code?.trim() ?? "";
      const fromChecks = needsPatch(session.lastChecks) && (session.patchesUsed ?? 0) < PATCH_CAP;
      if (existing && !fromChecks && !instruction) {
        const next = session.lastChecks
          ? compactChecks(session.lastChecks, session.patchesUsed ?? 0).next
          : "done";
        return ok({ chars: existing.length, patched: false, skipped: true, next });
      }
      const onThink = (token: string, source: "sop" | "code") => {
        sse.write("thinking", { token, source });
        onUpdate?.({ content: [{ type: "text", text: token }], details: { source } });
      };
      let patched = false;
      let code = "";
      if (existing && (fromChecks || instruction)) {
        const findings = session.lastChecks ? patchInstruction(session.lastChecks) : "";
        const patchedCode = await patchCodeViaConverse(
          existing,
          [instruction, findings].filter(Boolean).join("\n\n"),
          onThink
        );
        if (patchedCode) {
          code = patchedCode;
          patched = true;
        }
      }
      if (!code) {
        try {
          code = await generateCodeStream(
            session.sop as string,
            formatHardwareConfig(session),
            session.robot as string,
            onThink
          );
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          return ok({
            blocked: true,
            error: message,
            must_call: "emit_plan",
            hint:
              "8010 unavailable. Tell the user Watch/animation will be unavailable. Call emit_plan then run_checks.",
          });
        }
      }
      if (!code) {
        return ok({
          blocked: true,
          error: "empty_code",
          must_call: "emit_plan",
          hint:
            "8010 returned no Python. Tell the user Watch/animation will be unavailable. Call emit_plan then run_checks.",
        });
      }
      session.code = code;
      if (existing) session.patchesUsed = (session.patchesUsed ?? 0) + 1;
      session.lastChecks = undefined;
      session.analyze = undefined;
      sse.write("snapshot", snapshot(session));
      return ok({ chars: code.length, patched });
    },
  };

  const emitPlan: AgentTool = {
    name: "emit_plan",
    label: "Emit Plan IR",
    description:
      'Preferred for Hamilton STAR, Hamilton Vantage, and Tecan. Allowed for OT-2/Flex when 8010 is down or generate_code was blocked. Store BPL Plan IR (schema bpl.plan_ir.lh.v0) then call run_checks. mode defaults to "replace"; for large protocols, compress parallel channels with multi-well lists (for example source ["plate:A1","plate:B1","plate:C1","plate:D1"]) or send later chunks with mode:"append". Append concatenates steps and rejects duplicate step_id values. There is no small character limit; about 78 compressed steps fit one call. Primitives: PICK_TIPS, ASPIRATE, DISPENSE, MIX, DROP_TIPS, WAIT. A PICK_TIPS step requires empty channels; if tips are held, DROP_TIPS must come first. Locations like plate:A1. Set resources (with max_volume_ul), initial_volumes_ul, steps. Minimal valid plan: {"schema":"bpl.plan_ir.lh.v0","resources":[{"id":"tips","type":"tiprack","slot":"1"},{"id":"plate","type":"plate","slot":"2","max_volume_ul":360}],"initial_volumes_ul":{"plate:A1":100,"plate:B1":0},"steps":[{"step_id":"1","primitive_type":"PICK_TIPS","tip_rack":"tips","tip_positions":["A1"],"dependencies":[]},{"step_id":"2","primitive_type":"ASPIRATE","source":"plate:A1","volume_ul":50,"dependencies":["1"]},{"step_id":"3","primitive_type":"DISPENSE","destination":"plate:B1","volume_ul":50,"dependencies":["2"]},{"step_id":"4","primitive_type":"DROP_TIPS","to_waste":true,"dependencies":["3"]}]}. tip_positions are bare wells ("A1"), never "TIPS:A1". tip_rack is the tiprack resource id. dependencies may be []. Common rejects: (1) tip_positions "TIPS:A1" — write "A1"; (2) PICK_TIPS missing tip_rack matching resources[].id; (3) dependencies not a list — use []. Hamilton standard wells: Corning 96-well 360 µL, 15 mL reservoir 15000 µL. Tecan standard wells: 96-well plate 360 µL, 200 µL DiTi, 15 mL reservoir 15000 µL. Omit max_volume_ul only when capacity is unknown (cannot-verify, never a silent pass). Hamilton STAR/Vantage deliverable is step JSON + a runnable PyLabRobot script (.py). Tecan also compiles a .gwl. Does not generate Python; Watch/animation unavailable without 8010 analyze.',
    parameters: Type.Object({
      plan: Type.Record(Type.String(), Type.Unknown()),
      mode: Type.Optional(Type.Union([Type.Literal("replace"), Type.Literal("append")])),
    }),
    executionMode: "sequential",
    execute: async (_id, args) => {
      const conflict = unresolvedGoalNotesConflict(session);
      if (conflict) {
        return ok({
          blocked: true,
          missing: missingList(session),
          conflict,
          hint: "Notes conflict with the goal. Call ask_user and wait. Do not emit a .gwl.",
        });
      }
      if (!canEmitPlan(session)) {
        const missing = missingList(session);
        if (!session.sop?.trim()) missing.push("sop");
        return ok({ blocked: true, missing });
      }
      const input = args as {
        plan?: Record<string, unknown>;
        mode?: "replace" | "append";
      };
      const mode = input.mode ?? "replace";
      // Appends and all plan construction before the first pass are authoring, not patches.
      const isPatch = mode === "replace" && session.hasPassedChecks === true;
      if (isPatch && (session.patchesUsed ?? 0) >= PATCH_CAP) {
        return refusePatchBudget();
      }
      const raw = { ...(input.plan ?? {}) };
      if (!raw.backend) raw.backend = planBackendFor(session.robot);
      const existing = session.plan;
      const incomingSteps = Array.isArray(raw.steps) ? raw.steps : [];
      let candidate = raw;
      if (mode === "append") {
        const existingSteps = Array.isArray(existing?.steps) ? existing.steps : [];
        const ids = [...existingSteps, ...incomingSteps]
          .map((step) =>
            step && typeof step === "object" && !Array.isArray(step)
              ? String((step as Record<string, unknown>).step_id ?? "")
              : ""
          )
          .filter(Boolean);
        const duplicates = [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];
        if (duplicates.length) {
          return ok({
            ok: false,
            error: "duplicate_step_id",
            errors: [`Append rejected: duplicate step_id(s): ${duplicates.join(", ")}`],
          });
        }
        if (existing) {
          candidate = { ...existing, ...raw, steps: [...existingSteps, ...incomingSteps] };
        }
      }
      const { plan: normalized, notes } = normalizePlanInput(candidate);
      const checked = await validatePlan(normalized);
      if (!checked.ok || !checked.plan) {
        return ok({ ok: false, errors: explainPlanErrors(checked.errors ?? ["invalid_plan"]) });
      }
      session.plan = checked.plan;
      if (isPatch) session.patchesUsed = (session.patchesUsed ?? 0) + 1;
      session.lastChecks = undefined;
      session.analyze = undefined;
      session.artifacts = undefined;
      sse.write("snapshot", snapshot(session));
      return ok({
        ok: true,
        steps: Array.isArray(checked.plan.steps) ? checked.plan.steps.length : 0,
        backend: checked.plan.backend,
        ...(notes.length ? { normalized: notes } : {}),
      });
    },
  };

  const runChecksTool: AgentTool = {
    name: "run_checks",
    label: "Run checks",
    description:
      "Simulate → analyze → LogicPass. For OT-2 or Flex with Python, use 8010 simulate+analyze so session.analyze commands exist for FAB/animation. Do not prefer a stored plan over Python when the robot is OT-2 or Flex. FAB lights only on FinalPass_v2.",
    parameters: Type.Object({}),
    executionMode: "sequential",
    execute: async () => {
      const route = checksRoute(session);
      if (route === "blocked") {
        return ok({
          blocked: true,
          missing: isOpentrons(session)
            ? session.codeService === "down"
              ? ["emit_plan — 8010 down; use Plan IR fallback"]
              : [`generate_code — ${PYTHON_ROBOTS.join("/")} need 8010 Python, or emit_plan if 8010 is down`]
            : [`emit_plan — ${PLAN_ROBOTS.join("/")} need a plan`],
        });
      }
      if (route === "plan") {
        const conflict = unresolvedGoalNotesConflict(session);
        if (conflict) {
          return ok({
            blocked: true,
            missing: missingList(session),
            conflict,
            hint: "Notes conflict with the goal. Call ask_user and wait. Do not emit a .gwl.",
          });
        }
        const { checks, plan, artifacts } = await runPlanChecks(
          session.plan as Record<string, unknown>,
          reviewIntent(session),
          { robot: session.robot }
        );
        session.lastChecks = checks;
        if (checks.status === "pass") session.hasPassedChecks = true;
        if (plan) session.plan = plan;
        session.artifacts = checks.status === "pass" ? artifacts : undefined;
        sse.write("checks", checks);
        sse.write("snapshot", snapshot(session));
        return ok(compactChecks(checks, session.patchesUsed ?? 0));
      }
      const { checks, analyze } = await runChecks(session.code as string, session.goal ?? "");
      session.lastChecks = checks;
      if (checks.status === "pass") session.hasPassedChecks = true;
      session.analyze = analyze ?? undefined;
      sse.write("checks", checks);
      sse.write("snapshot", snapshot(session));
      return ok(compactChecks(checks, session.patchesUsed ?? 0));
    },
  };

  const skillTool: AgentTool = {
    name: "skill",
    label: "Load skill",
    description:
      "Read a skill markdown. Empty name lists skills. authoring-guide and error-taxonomy are for this branch. Live Flex skills are documentation only.",
    parameters: Type.Object({
      name: Type.Optional(Type.String()),
    }),
    executionMode: "sequential",
    execute: async (_id, args) => {
      const env = loadDemoEnv();
      const dir = path.join(env.repoRoot, "labscriptai", "plugins", "skills");
      if (!existsSync(dir)) return ok({ error: "skills directory missing" });
      const requested = String((args as { name?: string }).name ?? "").trim().replace(/\.md$/, "");
      const files = readdirSync(dir).filter((name) => name.endsWith(".md"));
      if (!requested) {
        return ok({
          skills: files.map((name) => name.replace(/\.md$/, "")),
          note: "authoring-guide / error-taxonomy for this branch. Others are live-Flex docs only.",
        });
      }
      const match = files.find((name) => name.replace(/\.md$/, "") === requested);
      if (!match) return ok({ error: `unknown skill ${requested}`, skills: files.map((n) => n.replace(/\.md$/, "")) });
      const liveOnly = ["safety-brief", "recovery-playbooks", "pressure-trace"].includes(requested);
      return ok({
        name: requested,
        text: readFileSync(path.join(dir, match), "utf8"),
        note: liveOnly ? "This branch has no live Flex. Documentation only." : "",
      });
    },
  };

  const openAnimation: AgentTool = {
    name: "open_animation",
    label: "Open animation",
    description:
      "Allowed only after FinalPass_v2 and playable 8010 analyze commands. Watch is hidden otherwise.",
    parameters: Type.Object({}),
    executionMode: "sequential",
    execute: async () => {
      const commands = Array.isArray(session.analyze?.commands) ? session.analyze.commands : [];
      if (!animationAllowed(session.lastChecks, commands.length)) {
        if (isReviewMismatch(session.lastChecks?.llmreview)) {
          return ok({ blocked: true, allowed: false, missing: ["review_match"] });
        }
        if (!session.lastChecks?.fab.lit) {
          return ok({ blocked: true, allowed: false, missing: ["final_pass_v2"] });
        }
        if (!commands.length) {
          return ok({
            blocked: true,
            allowed: false,
            missing: ["opentrons_animation"],
          });
        }
        return ok({ blocked: true, allowed: false, missing: ["review_match"] });
      }
      sse.write("animation", { allowed: true });
      return ok({ allowed: true, commands: commands.length });
    },
  };

  return [askUser, generateSop, generateCode, emitPlan, runChecksTool, skillTool, openAnimation];
}
