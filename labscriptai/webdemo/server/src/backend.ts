import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { assertLocalBackend, loadDemoEnv } from "./env.ts";
import {
  emptyStatepass,
  inspectAnalyze,
  looksLikeRaiseOnly,
  forceRaiseOnlySim,
  sanitizeLogicpass,
  shouldRunLlmreview,
  skippedLogic,
  type ChecksResult,
  type LogicPassResult,
  type LlmReviewResult,
  type SimResult,
  type StatePassResult,
  unevaluableLogic,
  wrapChecks,
  attachConsequences,
} from "./gate.ts";
import { capSop } from "./session.ts";
import { parseSseBuffer } from "./sse.ts";
import { codeThinkingToken } from "./think.ts";

export type ThinkFn = (token: string, source: "sop" | "code") => void;

const SOP_CODE_MS = 6 * 60 * 1000;
const SIM_ANALYZE_MS = 3 * 60 * 1000;

function localBackend(): string {
  const { backend } = loadDemoEnv();
  return assertLocalBackend(backend);
}

export type CodeServiceStatus = "up" | "down";

export async function checkCodeService(): Promise<CodeServiceStatus> {
  try {
    const response = await fetch(`${localBackend()}/`, { signal: AbortSignal.timeout(1500) });
    return response.ok ? "up" : "down";
  } catch {
    return "down";
  }
}

function isAbort(error: unknown): boolean {
  return error instanceof Error && (error.name === "AbortError" || error.name === "TimeoutError");
}

async function readSse(
  url: string,
  body: unknown,
  onEvent: (payload: Record<string, unknown>) => void,
  timeoutMs: number
): Promise<void> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(timeoutMs),
  });
  if (!response.ok || !response.body) {
    throw new Error(`HTTP ${response.status} ${response.statusText} from ${url}`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      buffer += decoder.decode();
      parseSseBuffer(buffer + "\n\n", onEvent);
      break;
    }
    buffer = parseSseBuffer(buffer + decoder.decode(value, { stream: true }), onEvent);
  }
}

export async function generateCompactSop(
  hardwareConfig: string,
  userGoal: string,
  onThink: ThinkFn
): Promise<string> {
  const env = loadDemoEnv();
  if (!env.apiKey) throw new Error("DeepSeek key missing for compact SOP");
  const prompt = `Write a compact liquid-handling SOP in English markdown, 400–800 characters. No Phase/Action/Tool/Tips/Workflow/Params. No essay. Do not write Python.

Hardware:
${hardwareConfig}

Goal:
${userGoal}

Output only:
# <one-line objective>
- Robot / pipettes (copy from hardware)
- Deck: slot → labware (one line)
- Reagents: name, slot/well, volume
- Numbered steps, one line each: pipette, µL, source → dest; mix only if needed; new tip vs reuse
- Assume: one line if you guessed

Stop when a technician can run it on the stated deck. No summary, no repeated deck.`;

  let sop = "";
  try {
    const response = await fetch(`${env.baseUrl}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: env.model,
        stream: true,
        messages: [{ role: "user", content: prompt }],
      }),
      signal: AbortSignal.timeout(SOP_CODE_MS),
    });
    if (!response.ok || !response.body) {
      throw new Error(`DeepSeek SOP HTTP ${response.status}`);
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    const onFrame = (data: Record<string, unknown>) => {
      const choices = data.choices;
      const delta =
        Array.isArray(choices) && choices[0] && typeof choices[0] === "object"
          ? ((choices[0] as { delta?: Record<string, unknown> }).delta ?? {})
          : {};
      const reasoning =
        (typeof delta.reasoning_content === "string" && delta.reasoning_content) ||
        (typeof delta.reasoning === "string" && delta.reasoning) ||
        "";
      if (reasoning) onThink(reasoning, "sop");
      if (typeof delta.content === "string" && delta.content) sop += delta.content;
    };
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        parseSseBuffer(buffer + decoder.decode() + "\n\n", onFrame);
        break;
      }
      buffer = parseSseBuffer(buffer + decoder.decode(value, { stream: true }), onFrame);
    }
  } catch (error) {
    if (isAbort(error)) throw new Error("compact SOP timed out");
    throw error;
  }
  return capSop(sop);
}

export async function generateCodeStream(
  sopMarkdown: string,
  hardwareConfig: string,
  robotModel: string,
  onThink: ThinkFn
): Promise<string> {
  const backend = localBackend();
  let code = "";
  try {
  await readSse(
    `${backend}/api/generate-protocol-code`,
    {
      sop_markdown: sopMarkdown,
      hardware_config: hardwareConfig,
      robot_model: robotModel,
    },
    (data) => {
      if (data.event_type === "thinking") {
        const token = codeThinkingToken(data);
        if (token) onThink(token, "code");
      }
      if (data.event_type === "error") {
        throw new Error(String(data.message || "Code generation failed"));
      }
      if (typeof data.generated_code === "string" && data.generated_code.trim()) {
        code = data.generated_code;
      } else if (typeof data.final_code === "string" && data.final_code.trim()) {
        code = data.final_code;
      }
    },
    SOP_CODE_MS
  );
  } catch (error) {
    if (isAbort(error)) throw new Error("8010 code stream timed out (6 min)");
    throw error;
  }
  return code.trim();
}

const PATCH_MS = 3 * 60 * 1000;

export function extractPatchedCode(payload: Record<string, unknown> | null): string | null {
  if (!payload) return null;
  const content = typeof payload.content === "string" ? payload.content.trim() : "";
  if (!content) return null;
  if (payload.type === "edit") return content;
  const fence = content.match(/```(?:python)?\s*\n([\s\S]*?)```/i);
  const body = (fence ? fence[1] : content).trim();
  if (/\bdef\s+run\s*\(/.test(body) && /opentrons|protocol_api|metadata/.test(body)) return body;
  return null;
}

export async function patchCodeViaConverse(
  originalCode: string,
  instruction: string,
  onThink: ThinkFn
): Promise<string | null> {
  const backend = localBackend();
  try {
    const response = await fetch(`${backend}/api/converse-code`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      },
      body: JSON.stringify({
        original_code: originalCode,
        user_instruction: instruction,
      }),
      signal: AbortSignal.timeout(PATCH_MS),
    });
    if (!response.ok || !response.body) return null;
    const ctype = response.headers.get("content-type") || "";
    if (ctype.includes("event-stream")) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let code: string | null = null;
      const onFrame = (data: Record<string, unknown>) => {
        if (data.event_type === "thinking" || data.event === "thinking") {
          const token = codeThinkingToken(data);
          if (token) onThink(token, "code");
        }
        const edited = extractPatchedCode(data);
        if (edited) code = edited;
      };
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          parseSseBuffer(buffer + decoder.decode() + "\n\n", onFrame);
          break;
        }
        buffer = parseSseBuffer(buffer + decoder.decode(value, { stream: true }), onFrame);
      }
      return code;
    }
    const payload = (await response.json().catch(() => null)) as Record<string, unknown> | null;
    return extractPatchedCode(payload);
  } catch (error) {
    if (isAbort(error)) throw new Error("8010 converse-code timed out (3 min)");
    return null;
  }
}

async function simulateProtocol(code: string): Promise<SimResult> {
  try {
    const backend = localBackend();
    const response = await fetch(`${backend}/api/simulate-protocol`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ protocol_code: code }),
      signal: AbortSignal.timeout(SIM_ANALYZE_MS),
    });
    const payload = (await response.json().catch(() => ({}))) as Record<string, unknown>;
    if (!response.ok) {
      return {
        ok: false,
        reason: "sim_http_error",
        errors: [String(payload.detail || response.statusText)],
      };
    }
    const ok = payload.success === true;
    const errors: string[] = [];
    if (payload.error_message) errors.push(String(payload.error_message));
    return {
      ok,
      reason: ok ? undefined : String(payload.final_status_message || "sim_failed"),
      errors: errors.length ? errors : undefined,
    };
  } catch (error) {
    return {
      ok: false,
      reason: isAbort(error) ? "sim_timeout" : "sim_failed",
      errors: [error instanceof Error ? error.message : String(error)],
    };
  }
}

async function analyzeProtocol(code: string): Promise<Record<string, unknown> | null> {
  try {
    const backend = localBackend();
    const form = new FormData();
    form.append(
      "protocol",
      new Blob([code], { type: "text/x-python" }),
      "protocol.py"
    );
    const response = await fetch(`${backend}/api/visualizer/analyze`, {
      method: "POST",
      body: form,
      signal: AbortSignal.timeout(SIM_ANALYZE_MS),
    });
    if (!response.ok) return null;
    const payload = (await response.json().catch(() => null)) as Record<string, unknown> | null;
    return payload && typeof payload === "object" ? payload : null;
  } catch {
    return null;
  }
}

function runLogicpassCli(
  analyzeJson: Record<string, unknown>,
  protocolPath: string
): Promise<Record<string, unknown>> {
  const env = loadDemoEnv();
  const script = path.join(env.webdemoRoot, "python", "eval_logicpass.py");
  return new Promise((resolve) => {
    const child = spawn(env.python, [script, "--protocol", protocolPath, "--sim-pass", "true"], {
      env: { ...process.env, PYTHONPATH: env.repoRoot },
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.on("error", () => {
      resolve({
        outcome: "unevaluable",
        logic_pass: false,
        issues: [],
        reason: "logicpass_cli_spawn_failed",
        statepass: emptyStatepass("logicpass_cli_spawn_failed"),
      });
    });
    child.on("close", () => {
      try {
        const parsed = JSON.parse(stdout) as Record<string, unknown>;
        resolve(parsed);
      } catch {
        resolve({
          outcome: "unevaluable",
          logic_pass: false,
          issues: [],
          reason: "logicpass_cli_bad_json",
          statepass: emptyStatepass("logicpass_cli_bad_json"),
        });
      }
    });
    child.stdin.write(JSON.stringify(analyzeJson));
    child.stdin.end();
  });
}

function runLlmreviewCli(userIntent: string, protocolSource: string): Promise<LlmReviewResult> {
  const env = loadDemoEnv();
  const script = path.join(env.webdemoRoot, "python", "eval_llmreview.py");
  return new Promise((resolve) => {
    const child = spawn(env.python, [script], {
      env: { ...process.env, PYTHONPATH: env.repoRoot },
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    const fail = (reason: string): LlmReviewResult => ({
      match: false,
      findings: [
        {
          severity: "error",
          claim: "reviewer_exception",
          evidence: reason.slice(0, 400),
          suggestion: "Return JSON {match, findings}.",
        },
      ],
      reason,
    });
    child.on("error", () => resolve(fail("llmreview_cli_spawn_failed")));
    child.on("close", () => {
      try {
        const parsed = JSON.parse(stdout) as LlmReviewResult;
        resolve(parsed && typeof parsed === "object" ? parsed : fail("llmreview_cli_bad_json"));
      } catch {
        resolve(fail("llmreview_cli_bad_json"));
      }
    });
    child.stdin.write(JSON.stringify({ user_intent: userIntent, protocol_source: protocolSource }));
    child.stdin.end();
  });
}

async function withOptionalReview(
  checks: ChecksResult,
  code: string,
  userIntent: string
): Promise<ChecksResult> {
  if (!shouldRunLlmreview(checks.sim, checks.logicpass)) return checks;
  const llmreview = await runLlmreviewCli(userIntent, code);
  return attachConsequences({ ...checks, llmreview });
}

function runPlanCli(payload: unknown): Promise<Record<string, unknown>> {
  const env = loadDemoEnv();
  const script = path.join(env.webdemoRoot, "python", "eval_plan.py");
  return new Promise((resolve) => {
    const child = spawn(env.python, [script], {
      env: { ...process.env, PYTHONPATH: env.repoRoot },
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    const fail = (reason: string): Record<string, unknown> => ({
      sim: { ok: false, reason },
      logicpass: skippedLogic(reason),
      fab: { lit: false },
      errors: [reason],
      ok: false,
    });
    child.on("error", () => resolve(fail("plan_cli_spawn_failed")));
    child.on("close", () => {
      try {
        const parsed = JSON.parse(stdout) as Record<string, unknown>;
        resolve(parsed && typeof parsed === "object" ? parsed : fail("plan_cli_bad_json"));
      } catch {
        resolve(fail("plan_cli_bad_json"));
      }
    });
    child.stdin.write(JSON.stringify(payload));
    child.stdin.end();
  });
}

export async function validatePlan(
  plan: Record<string, unknown>
): Promise<{ ok: boolean; plan?: Record<string, unknown>; errors?: string[] }> {
  const raw = await runPlanCli({ plan, validate_only: true });
  if (raw.ok === true && raw.plan && typeof raw.plan === "object") {
    return { ok: true, plan: raw.plan as Record<string, unknown> };
  }
  const errors = Array.isArray(raw.errors) ? raw.errors.map(String) : [String(raw.reason || "invalid_plan")];
  return { ok: false, errors };
}

export async function runPlanChecks(
  plan: Record<string, unknown>,
  userIntent = ""
): Promise<{ checks: ChecksResult; plan: Record<string, unknown> | null }> {
  const raw = await runPlanCli({ plan, user_intent: userIntent });
  const simRaw = (raw.sim && typeof raw.sim === "object" ? raw.sim : raw) as Record<string, unknown>;
  const sim: SimResult = {
    ok: simRaw.ok === true,
    reason: typeof simRaw.reason === "string" ? simRaw.reason : undefined,
    errors: Array.isArray(simRaw.errors) ? simRaw.errors.map(String) : undefined,
  };
  if (!sim.ok) {
    return {
      checks: await withOptionalReview(
        wrapChecks(sim, skippedLogic(String(sim.reason || "sim_failed")), emptyStatepass(String(sim.reason || "sim_failed"))),
        JSON.stringify(plan),
        userIntent
      ),
      plan: (raw.plan as Record<string, unknown>) || plan,
    };
  }
  const logicpass = sanitizeLogicpass(
    raw.logicpass && typeof raw.logicpass === "object" ? (raw.logicpass as Record<string, unknown>) : null
  );
  const checks = await withOptionalReview(
    wrapChecks(sim, logicpass, emptyStatepass()),
    JSON.stringify(plan),
    userIntent
  );
  return { checks, plan: (raw.plan as Record<string, unknown>) || plan };
}

export async function runChecks(
  code: string,
  userIntent = ""
): Promise<{
  checks: ChecksResult;
  analyze: Record<string, unknown> | null;
}> {
  const raiseOnly = looksLikeRaiseOnly(code);
  const sim = await simulateProtocol(code).catch(
    (error): SimResult => ({
      ok: false,
      reason: raiseOnly ? "raise_only" : "sim_failed",
      errors: [error instanceof Error ? error.message : String(error)],
    })
  );

  if (raiseOnly) {
    return {
      checks: await withOptionalReview(
        wrapChecks(forceRaiseOnlySim(sim), skippedLogic("raise_only"), emptyStatepass("raise_only")),
        code,
        userIntent
      ),
      analyze: null,
    };
  }

  if (!sim.ok) {
    return {
      checks: await withOptionalReview(
        wrapChecks(sim, skippedLogic("sim_failed"), emptyStatepass("sim_failed")),
        code,
        userIntent
      ),
      analyze: null,
    };
  }

  const analyze = await analyzeProtocol(code);
  const artifact = inspectAnalyze(analyze);
  if (!artifact.ok || !analyze) {
    return {
      checks: await withOptionalReview(
        wrapChecks(sim, unevaluableLogic(artifact.reason), emptyStatepass(artifact.reason)),
        code,
        userIntent
      ),
      analyze: artifact.reason === "missing_analyze_artifact" ? null : analyze,
    };
  }

  const tmp = mkdtempSync(path.join(tmpdir(), "webdemo-lp-"));
  const protocolPath = path.join(tmp, "protocol.py");
  try {
    writeFileSync(protocolPath, code, "utf8");
    const raw = await runLogicpassCli(analyze, protocolPath);
    const logicpass: LogicPassResult = sanitizeLogicpass(raw);
    const statepass: StatePassResult =
      raw.statepass && typeof raw.statepass === "object"
        ? (raw.statepass as StatePassResult)
        : {
            issues: logicpass.issues,
            coverage: logicpass.coverage,
            input_conflicts: raw.input_conflicts,
          };
    return {
      checks: await withOptionalReview(wrapChecks(sim, logicpass, statepass), code, userIntent),
      analyze,
    };
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}
