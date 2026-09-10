import { Type } from "typebox";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import type { AgentTool } from "@earendil-works/pi-agent-core";
import {
  generateCodeStream,
  generateCompactSop,
  patchCodeViaConverse,
  runChecks,
  runPlanChecks,
  validatePlan,
} from "./backend.ts";
import { loadDemoEnv } from "./env.ts";
import { compactChecks, needsPatch, PATCH_CAP, patchInstruction, refuseEmptySop } from "./gate.ts";
import {
  applyAskUser,
  canEmitPlan,
  canGenerateCode,
  canRunPipeline,
  checksRoute,
  capSop,
  formatHardwareConfig,
  isOpentrons,
  missingList,
  planBackendFor,
  presetMismatchWarning,
  shouldCallCompactSop,
  shouldReuseSop,
  snapshot,
  type AskUserInput,
  type SessionState,
} from "./session.ts";
import type { SseWriter } from "./sse.ts";

type ToolResult = {
  content: Array<{ type: "text"; text: string }>;
  details?: Record<string, unknown>;
};

function ok(payload: unknown): ToolResult {
  return {
    content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
    details: { payload },
  };
}

function toolGoal(session: SessionState): string {
  const goal = session.goal ?? "";
  if (session.doc && session.doc !== "none") {
    return `${goal}\n\nExisting SOP draft:\n${session.doc}`;
  }
  return goal;
}

export function buildTools(session: SessionState, sse: SseWriter): AgentTool[] {
  const askUser: AgentTool = {
    name: "ask_user",
    label: "Ask user / session",
    description:
      "Persist collected answers and read the session machine. Use after the user gives goal, doc=none/draft, robot, pipettes, or deck slots. Naming any supported robot with no custom deck assumes that family's standard layout (assumed_deck=true). Pass deck only when the user names specific labware. Does not generate code. No deck UI.",
    parameters: Type.Object({
      goal: Type.Optional(Type.String()),
      doc: Type.Optional(Type.String({ description: "SOP draft text, or 'none'" })),
      robot: Type.Optional(
        Type.Union([
          Type.Literal("OT-2"),
          Type.Literal("Flex"),
          Type.Literal("Hamilton"),
          Type.Literal("Tecan"),
        ])
      ),
      preset: Type.Optional(
        Type.Union([
          Type.Literal("ot2_p300_standard3"),
          Type.Literal("flex_1000_standard3"),
          Type.Literal("hamilton_star_standard"),
          Type.Literal("tecan_evo_standard"),
        ])
      ),
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
      applyAskUser(session, input);
      return ok({
        phase: session.phase,
        missing: missingList(session),
        ready: canRunPipeline(session),
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
      "Write a compact SOP via DeepSeek only after phase=ready. Skip if sop already stored unless force=true. Blocked without robot/slots (returns JSON, does not throw, does not call DeepSeek).",
    parameters: Type.Object({
      force: Type.Optional(Type.Boolean()),
    }),
    executionMode: "sequential",
    execute: async (_id, args, _signal, onUpdate) => {
      const force = Boolean((args as { force?: boolean }).force);
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
      if (!canRunPipeline(session)) {
        return ok({ blocked: true, missing: missingList(session) });
      }
      if (!isOpentrons(session)) {
        return ok({
          blocked: true,
          missing: ["emit_plan — Hamilton/Tecan use Plan IR, not Opentrons Python"],
        });
      }
      const refused = refuseEmptySop(session.sop);
      if (refused || !canGenerateCode(session)) {
        const missing = missingList(session);
        if (refused) missing.push("sop");
        return ok({ blocked: true, missing });
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
      "Preferred for Hamilton and Tecan. Allowed for OT-2/Flex when 8010 is down or generate_code was blocked. Store BPL Plan IR (schema bpl.plan_ir.lh.v0) then call run_checks. Primitives: PICK_TIPS, ASPIRATE, DISPENSE, MIX, DROP_TIPS, WAIT. Locations like plate:A1. Set resources (with max_volume_ul), initial_volumes_ul, steps. Does not generate Python; Watch/animation unavailable without 8010 analyze.",
    parameters: Type.Object({
      plan: Type.Record(Type.String(), Type.Unknown()),
    }),
    executionMode: "sequential",
    execute: async (_id, args) => {
      if (!canEmitPlan(session)) {
        const missing = missingList(session);
        if (!session.sop?.trim()) missing.push("sop");
        return ok({ blocked: true, missing });
      }
      const raw = { ...((args as { plan?: Record<string, unknown> }).plan ?? {}) };
      if (!raw.backend) raw.backend = planBackendFor(session.robot);
      const replacing = Boolean(session.plan && session.lastChecks);
      const checked = await validatePlan(raw);
      if (!checked.ok || !checked.plan) {
        return ok({ ok: false, errors: checked.errors ?? ["invalid_plan"] });
      }
      session.plan = checked.plan;
      if (replacing) session.patchesUsed = (session.patchesUsed ?? 0) + 1;
      session.lastChecks = undefined;
      session.analyze = undefined;
      sse.write("snapshot", snapshot(session));
      return ok({
        ok: true,
        steps: Array.isArray(checked.plan.steps) ? checked.plan.steps.length : 0,
        backend: checked.plan.backend,
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
              : ["generate_code — OT-2/Flex need 8010 Python, or emit_plan if 8010 is down"]
            : ["emit_plan — Hamilton/Tecan need a plan"],
        });
      }
      if (route === "plan") {
        const { checks, plan } = await runPlanChecks(session.plan as Record<string, unknown>, session.goal ?? "");
        session.lastChecks = checks;
        if (plan) session.plan = plan;
        sse.write("checks", checks);
        sse.write("snapshot", snapshot(session));
        return ok(compactChecks(checks, session.patchesUsed ?? 0));
      }
      const { checks, analyze } = await runChecks(session.code as string, session.goal ?? "");
      session.lastChecks = checks;
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
      const lit = Boolean(session.lastChecks?.fab.lit);
      const commands = Array.isArray(session.analyze?.commands) ? session.analyze.commands : [];
      if (!lit) {
        return ok({ blocked: true, allowed: false, missing: ["final_pass_v2"] });
      }
      if (!commands.length) {
        return ok({
          blocked: true,
          allowed: false,
          missing: ["opentrons_animation"],
        });
      }
      sse.write("animation", { allowed: true });
      return ok({ allowed: true, commands: Array.isArray(session.analyze?.commands) ? session.analyze?.commands.length : 0 });
    },
  };

  return [askUser, generateSop, generateCode, emitPlan, runChecksTool, skillTool, openAnimation];
}
