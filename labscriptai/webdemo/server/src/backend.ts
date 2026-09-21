import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { assertLocalBackend, loadDemoEnv } from "./env.ts";
import { usesFluentCompile, usesHamiltonCompile, hamiltonFamily } from "./devices.ts";
import {
  emptyStatepass,
  inspectAnalyze,
  logicpassFromPlanCli,
  looksLikeRaiseOnly,
  forceRaiseOnlySim,
  sanitizeLogicpass,
  shouldRunLlmreview,
  skippedLogic,
  type ChecksResult,
  type CompileResult,
  type LogicPassResult,
  type LlmReviewResult,
  type SimResult,
  type StatePassResult,
  unevaluableLogic,
  wrapChecks,
  attachConsequences,
  withCompile,
} from "./gate.ts";
import { applyTipCountOverlay, capSop } from "./session.ts";
import { parseSseBuffer } from "./sse.ts";
import { codeThinkingToken } from "./think.ts";
import { DEEPSEEK_MAX_TOKENS } from "./agent.ts";

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
  onThink: ThinkFn,
  language: "en" | "zh" = "en"
): Promise<string> {
  const env = loadDemoEnv();
  if (!env.apiKey) throw new Error("DeepSeek key missing for compact SOP");
  const langLine =
    language === "zh"
      ? "Write a compact liquid-handling SOP in Chinese markdown, 400–800 characters."
      : "Write a compact liquid-handling SOP in English markdown, 400–800 characters.";
  const prompt = `${langLine} No Phase/Action/Tool/Tips/Workflow/Params. No essay. Do not write Python.

Hardware:
${hardwareConfig}

Goal:
${userGoal}

Notes (if any "Existing SOP draft") are intern notes, not the SOP. Write from the Goal volumes and wells. Do not copy junk or contradictory notes.

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

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function pollAnalyzeJob(
  backend: string,
  jobId: string,
  deadline: number
): Promise<Record<string, unknown> | null> {
  const urls = [`${backend}/api/visualizer/jobs/${jobId}`, `${backend}/jobs/${jobId}`];
  while (Date.now() < deadline) {
    for (const url of urls) {
      try {
        const response = await fetch(url, { signal: AbortSignal.timeout(15_000) });
        if (!response.ok) continue;
        const job = (await response.json().catch(() => null)) as Record<string, unknown> | null;
        if (!job || typeof job !== "object") continue;
        const status = String(job.status || "");
        const result = job.result && typeof job.result === "object" ? (job.result as Record<string, unknown>) : null;
        if (status === "succeeded") return result;
        if (status === "failed") return result;
        break;
      } catch {
        continue;
      }
    }
    await sleep(400);
  }
  return null;
}

async function analyzeProtocolSync(
  backend: string,
  form: FormData
): Promise<Record<string, unknown> | null> {
  const response = await fetch(`${backend}/api/visualizer/analyze`, {
    method: "POST",
    body: form,
    signal: AbortSignal.timeout(SIM_ANALYZE_MS),
  });
  if (!response.ok) return null;
  const payload = (await response.json().catch(() => null)) as Record<string, unknown> | null;
  return payload && typeof payload === "object" ? payload : null;
}

async function analyzeProtocol(code: string): Promise<Record<string, unknown> | null> {
  try {
    const backend = localBackend();
    const form = new FormData();
    form.append("protocol", new Blob([code], { type: "text/x-python" }), "protocol.py");
    try {
      const started = await fetch(`${backend}/api/visualizer/analyze/start`, {
        method: "POST",
        body: form,
        signal: AbortSignal.timeout(30_000),
      });
      if (started.ok) {
        const body = (await started.json().catch(() => null)) as Record<string, unknown> | null;
        const jobId = body && body.id != null ? String(body.id) : "";
        if (jobId) {
          const polled = await pollAnalyzeJob(backend, jobId, Date.now() + SIM_ANALYZE_MS);
          if (polled) return polled;
        }
      }
    } catch {
      // Production-shaped start/poll missing — fall back to the sync analyze POST.
    }
    const retry = new FormData();
    retry.append("protocol", new Blob([code], { type: "text/x-python" }), "protocol.py");
    return await analyzeProtocolSync(backend, retry);
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

export { DEEPSEEK_MAX_TOKENS as WEBDEMO_REVIEW_MAX_TOKENS } from "./agent.ts";

export function reviewerProcessEnv(base: NodeJS.ProcessEnv = process.env): NodeJS.ProcessEnv {
  const configured = [base.LABSCRIPTAI_MAX_TOKENS, base.DEEPSEEK_REVIEW_MAX_TOKENS]
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value) && value > 0);
  const maxTokens = Math.max(DEEPSEEK_MAX_TOKENS, ...configured);
  return {
    ...base,
    LABSCRIPTAI_MAX_TOKENS: String(maxTokens),
    DEEPSEEK_REVIEW_MAX_TOKENS: String(maxTokens),
  };
}

export function runLlmreviewCli(
  userIntent: string,
  protocolSource: string
): Promise<LlmReviewResult> {
  const env = loadDemoEnv();
  const script = path.join(env.webdemoRoot, "python", "eval_llmreview.py");
  return new Promise((resolve) => {
    const child = spawn(env.python, [script], {
      env: { ...reviewerProcessEnv(), PYTHONPATH: env.repoRoot },
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

const FLUENT_COMPILE_MS = 30_000;

export interface SessionArtifacts {
  worklistGwl?: string;
  scriptXml?: string;
  hamiltonScript?: string;
}

export type FluentCompileOk = {
  ok: true;
  worklist_gwl: string;
  script_xml: string;
  command_count: number;
  warnings: string[];
};

export type FluentCompileFail = {
  ok: false;
  stage: string;
  error: string;
  hint: string;
};

export type FluentCompileResult = FluentCompileOk | FluentCompileFail;

export type StdinJsonSpawn = (input: {
  argv: string[];
  stdin: string;
  timeoutMs: number;
  env?: NodeJS.ProcessEnv;
}) => Promise<{ stdout: string; timedOut?: boolean; spawnError?: string }>;

function compileFail(stage: string, error: string, hint: string): FluentCompileFail {
  return { ok: false, stage, error, hint };
}

export function spawnStdinJson(input: {
  argv: string[];
  stdin: string;
  timeoutMs: number;
  env?: NodeJS.ProcessEnv;
}): Promise<{ stdout: string; timedOut?: boolean; spawnError?: string }> {
  const { argv, stdin, timeoutMs, env } = input;
  return new Promise((resolve) => {
    let stdout = "";
    let settled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const finish = (result: { stdout: string; timedOut?: boolean; spawnError?: string }) => {
      if (settled) return;
      settled = true;
      if (timer) clearTimeout(timer);
      resolve(result);
    };
    let child: ReturnType<typeof spawn>;
    try {
      child = spawn(argv[0], argv.slice(1), {
        env: env ?? process.env,
        stdio: ["pipe", "pipe", "pipe"],
      });
    } catch {
      finish({ stdout: "", spawnError: "spawn_failed" });
      return;
    }
    timer = setTimeout(() => {
      child.kill("SIGKILL");
      finish({ stdout, timedOut: true });
    }, timeoutMs);
    const stdinStream = child.stdin;
    const stdoutStream = child.stdout;
    const stderrStream = child.stderr;
    if (!stdinStream || !stdoutStream || !stderrStream) {
      finish({ stdout: "", spawnError: "spawn_failed" });
      return;
    }
    stdoutStream.setEncoding("utf8");
    stdoutStream.on("data", (chunk) => {
      stdout += chunk;
    });
    stderrStream.resume();
    child.on("error", () => finish({ stdout, spawnError: "spawn_failed" }));
    child.on("close", () => finish({ stdout }));
    try {
      stdinStream.write(stdin);
      stdinStream.end();
    } catch {
      finish({ stdout, spawnError: "stdin_failed" });
    }
  });
}

function asStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => String(item)).filter((item) => item.trim());
}

export function parseFluentCompileStdout(
  stdout: string,
  failReason?: { timedOut?: boolean; spawnError?: string }
): FluentCompileResult {
  if (failReason?.timedOut) {
    return compileFail("internal", "Fluent compiler timed out.", "Retry, or shorten the plan.");
  }
  if (failReason?.spawnError) {
    return compileFail(
      "internal",
      "Fluent compiler did not start.",
      "Confirm python3 can run python/compile_fluent.py."
    );
  }
  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(stdout) as Record<string, unknown>;
  } catch {
    return compileFail("internal", "Fluent compiler returned invalid JSON.", "Retry the check.");
  }
  if (!parsed || typeof parsed !== "object") {
    return compileFail("internal", "Fluent compiler returned invalid JSON.", "Retry the check.");
  }
  if (parsed.ok === true) {
    const worklist = typeof parsed.worklist_gwl === "string" ? parsed.worklist_gwl : "";
    const script = typeof parsed.script_xml === "string" ? parsed.script_xml : "";
    if (!worklist.trim()) {
      return compileFail("internal", "Fluent compiler returned no worklist.", "Retry the check.");
    }
    const count = typeof parsed.command_count === "number" && Number.isFinite(parsed.command_count)
      ? parsed.command_count
      : 0;
    return {
      ok: true,
      worklist_gwl: worklist,
      script_xml: script,
      command_count: count,
      warnings: asStringList(parsed.warnings),
    };
  }
  const stage = typeof parsed.stage === "string" && parsed.stage.trim() ? parsed.stage : "internal";
  const error =
    typeof parsed.error === "string" && parsed.error.trim()
      ? parsed.error
      : "Fluent compiler rejected the plan.";
  const hint =
    typeof parsed.hint === "string" && parsed.hint.trim()
      ? parsed.hint
      : "Fix the plan and run checks again.";
  return compileFail(stage, error, hint);
}

function publicCompile(raw: FluentCompileResult): CompileResult {
  if (raw.ok) {
    return { ok: true, warnings: raw.warnings, command_count: raw.command_count };
  }
  return { ok: false, stage: raw.stage, error: raw.error, hint: raw.hint };
}

export async function runFluentCompile(
  plan: Record<string, unknown>,
  spawnFn: StdinJsonSpawn = spawnStdinJson
): Promise<FluentCompileResult> {
  const env = loadDemoEnv();
  const script = path.join(env.webdemoRoot, "python", "compile_fluent.py");
  try {
    const result = await spawnFn({
      argv: [env.python, script],
      stdin: JSON.stringify(plan),
      timeoutMs: FLUENT_COMPILE_MS,
      env: { ...process.env, PYTHONPATH: env.repoRoot },
    });
    return parseFluentCompileStdout(result.stdout, result);
  } catch {
    return compileFail("internal", "Fluent compiler did not start.", "Retry the check.");
  }
}

export async function attachFluentCompile(
  checks: ChecksResult,
  plan: Record<string, unknown>,
  robot?: string,
  compileFn: (plan: Record<string, unknown>) => Promise<FluentCompileResult> = runFluentCompile
): Promise<{ checks: ChecksResult; artifacts?: SessionArtifacts }> {
  if (!usesFluentCompile(robot)) return { checks };
  let compiled: FluentCompileResult;
  try {
    compiled = await compileFn(plan);
  } catch {
    compiled = compileFail("internal", "Fluent compiler did not start.", "Retry the check.");
  }
  const next = withCompile(checks, publicCompile(compiled));
  if (compiled.ok && next.status === "pass") {
    return {
      checks: next,
      artifacts: { worklistGwl: compiled.worklist_gwl, scriptXml: compiled.script_xml },
    };
  }
  return { checks: next };
}

export type HamiltonCompileOk = {
  ok: true;
  script: string;
  command_count: number;
  warnings: string[];
};

export type HamiltonCompileFail = {
  ok: false;
  stage: string;
  error: string;
  hint: string;
};

export type HamiltonCompileResult = HamiltonCompileOk | HamiltonCompileFail;

function hamiltonFail(stage: string, error: string, hint: string): HamiltonCompileFail {
  return { ok: false, stage, error, hint };
}

export function parseHamiltonCompileStdout(
  stdout: string,
  failReason?: { timedOut?: boolean; spawnError?: string }
): HamiltonCompileResult {
  if (failReason?.timedOut) {
    return hamiltonFail("internal", "Hamilton compiler timed out.", "Retry, or shorten the plan.");
  }
  if (failReason?.spawnError) {
    return hamiltonFail(
      "internal",
      "Hamilton compiler did not start.",
      "Confirm python3 can run python/compile_hamilton.py."
    );
  }
  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(stdout) as Record<string, unknown>;
  } catch {
    return hamiltonFail("internal", "Hamilton compiler returned invalid JSON.", "Retry the check.");
  }
  if (!parsed || typeof parsed !== "object") {
    return hamiltonFail("internal", "Hamilton compiler returned invalid JSON.", "Retry the check.");
  }
  if (parsed.ok === true) {
    const script = typeof parsed.script === "string" ? parsed.script : "";
    if (!script.trim()) {
      return hamiltonFail("internal", "Hamilton compiler returned no script.", "Retry the check.");
    }
    const count =
      typeof parsed.command_count === "number" && Number.isFinite(parsed.command_count)
        ? parsed.command_count
        : 0;
    return { ok: true, script, command_count: count, warnings: asStringList(parsed.warnings) };
  }
  const stage = typeof parsed.stage === "string" && parsed.stage.trim() ? parsed.stage : "internal";
  const error =
    typeof parsed.error === "string" && parsed.error.trim()
      ? parsed.error
      : "Hamilton compiler rejected the plan.";
  const hint =
    typeof parsed.hint === "string" && parsed.hint.trim()
      ? parsed.hint
      : "Fix the plan and run checks again.";
  return hamiltonFail(stage, error, hint);
}

export async function runHamiltonCompile(
  plan: Record<string, unknown>,
  spawnFn: StdinJsonSpawn = spawnStdinJson,
  family: "star" | "vantage" = "vantage"
): Promise<HamiltonCompileResult> {
  const env = loadDemoEnv();
  const script = path.join(env.webdemoRoot, "python", "compile_hamilton.py");
  try {
    const result = await spawnFn({
      argv: [env.python, script, "--family", family],
      stdin: JSON.stringify(plan),
      timeoutMs: FLUENT_COMPILE_MS,
      env: { ...process.env, PYTHONPATH: env.repoRoot },
    });
    return parseHamiltonCompileStdout(result.stdout, result);
  } catch {
    return hamiltonFail("internal", "Hamilton compiler did not start.", "Retry the check.");
  }
}

/** Gift translator: never changes FAB/status. Script is stored only when checks already passed. */
export async function attachHamiltonCompile(
  checks: ChecksResult,
  plan: Record<string, unknown>,
  robot?: string,
  compileFn?: (plan: Record<string, unknown>) => Promise<HamiltonCompileResult>
): Promise<{ checks: ChecksResult; artifacts?: SessionArtifacts }> {
  if (!usesHamiltonCompile(robot) || checks.status !== "pass") return { checks };
  const family = hamiltonFamily(robot) ?? "vantage";
  const run = compileFn ?? ((next) => runHamiltonCompile(next, spawnStdinJson, family));
  let compiled: HamiltonCompileResult;
  try {
    compiled = await run(plan);
  } catch {
    return { checks };
  }
  if (compiled.ok) return { checks, artifacts: { hamiltonScript: compiled.script } };
  return { checks };
}

export async function runPlanChecks(
  plan: Record<string, unknown>,
  userIntent = "",
  opts?: {
    robot?: string;
    compileFn?: (plan: Record<string, unknown>) => Promise<FluentCompileResult>;
    hamiltonCompileFn?: (plan: Record<string, unknown>) => Promise<HamiltonCompileResult>;
  }
): Promise<{
  checks: ChecksResult;
  plan: Record<string, unknown> | null;
  artifacts?: SessionArtifacts;
}> {
  const raw = await runPlanCli({ plan, user_intent: userIntent, robot: opts?.robot ?? "" });
  const simRaw = (raw.sim && typeof raw.sim === "object" ? raw.sim : raw) as Record<string, unknown>;
  const sim: SimResult = {
    ok: simRaw.ok === true,
    reason: typeof simRaw.reason === "string" ? simRaw.reason : undefined,
    errors: Array.isArray(simRaw.errors) ? simRaw.errors.map(String) : undefined,
  };
  const outPlan = (raw.plan as Record<string, unknown>) || plan;
  const rawLogic =
    raw.logicpass && typeof raw.logicpass === "object" ? (raw.logicpass as Record<string, unknown>) : null;
  const logicpass = applyTipCountOverlay(
    logicpassFromPlanCli(sim, rawLogic),
    outPlan,
    userIntent
  );
  const checks = await withOptionalReview(
    wrapChecks(sim, logicpass, emptyStatepass(sim.ok ? undefined : String(sim.reason || "sim_failed"))),
    JSON.stringify(plan),
    userIntent
  );
  const fluent = await attachFluentCompile(checks, outPlan, opts?.robot, opts?.compileFn);
  const ham = await attachHamiltonCompile(fluent.checks, outPlan, opts?.robot, opts?.hamiltonCompileFn);
  return {
    checks: ham.checks,
    artifacts: ham.artifacts ?? fluent.artifacts,
    plan: outPlan,
  };
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
    const reason = artifact.ok ? "missing_analyze_artifact" : artifact.reason;
    return {
      checks: await withOptionalReview(
        wrapChecks(sim, unevaluableLogic(reason), emptyStatepass(reason)),
        code,
        userIntent
      ),
      analyze: reason === "missing_analyze_artifact" ? null : analyze,
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
            input_conflicts: Array.isArray(raw.input_conflicts) ? raw.input_conflicts : [],
          };
    return {
      checks: await withOptionalReview(wrapChecks(sim, logicpass, statepass), code, userIntent),
      analyze,
    };
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}
