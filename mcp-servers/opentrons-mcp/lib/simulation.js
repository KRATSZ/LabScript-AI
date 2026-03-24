import fs from "fs";
import path from "path";
import { spawn } from "child_process";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const helperScriptPath = path.resolve(__dirname, "../scripts/local_simulation.py");
const repoLocalPythonPath = path.resolve(__dirname, "../../../.venv/bin/python");
const DEFAULT_MAX_LOG_CHARS = 20000;

function truncateLog(text = "", maxChars = DEFAULT_MAX_LOG_CHARS) {
  if (typeof text !== "string") {
    return "";
  }
  if (text.length <= maxChars) {
    return text;
  }
  const headChars = Math.floor(maxChars * 0.55);
  const tailChars = maxChars - headChars;
  return `${text.slice(0, headChars)}\n\n...[truncated ${text.length - maxChars} chars]...\n\n${text.slice(-tailChars)}`;
}

function runCommand(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: process.cwd(),
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", chunk => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", chunk => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", code => resolve({ code, stdout, stderr, command, args }));
  });
}

async function runHelper(args, preferredPython) {
  const candidates = [];
  const detectedLocalPython = fs.existsSync(repoLocalPythonPath)
    ? repoLocalPythonPath
    : null;

  for (const candidate of [
    preferredPython,
    process.env.OPENTRONS_PYTHON,
    detectedLocalPython,
    "python3",
    "python",
  ]) {
    if (candidate && !candidates.includes(candidate)) {
      candidates.push(candidate);
    }
  }

  let lastError = null;
  for (const candidate of candidates) {
    try {
      return await runCommand(candidate, args);
    } catch (error) {
      if (error.code === "ENOENT") {
        lastError = error;
        continue;
      }
      throw error;
    }
  }

  throw lastError || new Error("No usable Python interpreter found.");
}

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch (error) {
    return {
      ok: false,
      error: {
        error_type: "InvalidJsonOutput",
        error: error.message,
      },
      raw_stdout: text,
    };
  }
}

function collectLineReferences(logText = "", protocolPath) {
  const references = [];
  const regex = /File "([^"]+)", line (\d+)(?:, in ([^\n]+))?/g;
  let match = regex.exec(logText);
  while (match) {
    references.push({
      file: match[1],
      line: Number(match[2]),
      symbol: match[3] || null,
      is_protocol_file: protocolPath ? path.resolve(match[1]) === path.resolve(protocolPath) : false,
    });
    match = regex.exec(logText);
  }
  return references;
}

function buildEvidence(logText, regex) {
  const match = regex.exec(logText);
  if (!match || match.index === undefined) {
    regex.lastIndex = 0;
    return [];
  }
  const start = Math.max(0, match.index - 160);
  const end = Math.min(logText.length, match.index + 260);
  const snippet = logText.slice(start, end).trim();
  regex.lastIndex = 0;
  return snippet ? [snippet] : [];
}

function uniqueIssues(issues) {
  const seen = new Set();
  return issues.filter(issue => {
    const key = `${issue.category}:${issue.message}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

export function parseSimulationLog({
  simulation_output_json,
  stdout = "",
  stderr = "",
  exit_code = null,
  protocol_path = null,
} = {}) {
  let simulation = null;
  if (simulation_output_json) {
    simulation =
      typeof simulation_output_json === "string"
        ? safeJsonParse(simulation_output_json)
        : simulation_output_json;
    stdout = simulation.stdout || stdout;
    stderr = simulation.stderr || stderr;
    exit_code = simulation.exit_code ?? exit_code;
    protocol_path = simulation.protocol || protocol_path;
  }

  const combinedLog = [stderr, stdout].filter(Boolean).join("\n");
  const lineReferences = collectLineReferences(combinedLog, protocol_path);
  const issues = [];

  const patterns = [
    {
      category: "RUNTIME_UNAVAILABLE",
      severity: "error",
      regex: /(No module named ['"]opentrons['"]|could not locate workspace root|probe produced no output|ModuleNotFoundError: No module named ['"]opentrons['"])/i,
      message: "本地 Opentrons 运行时不可用，当前无法进行真实仿真。",
      fixable_by_edit: false,
      suggested_edit_direction: "先修复本地运行环境，或显式传入 workspace_root/api_root/shared_data_root/python_executable。",
    },
    {
      category: "MISSING_TRASH_OR_SETUP",
      severity: "error",
      regex: /(NoTrashDefinedError|No trash container has been defined|drop_tip\(\) without)/i,
      message: "协议缺少垃圾槽或必要 deck setup。",
      fixable_by_edit: true,
      suggested_edit_direction: "在 `run()` 开头显式声明 trash，例如 Flex 使用 `protocol.load_trash_bin(\"A3\")`，再调用 `drop_tip()`。",
    },
    {
      category: "SYNTAX_OR_IMPORT",
      severity: "error",
      regex: /(SyntaxError|IndentationError|ImportError|ModuleNotFoundError|NameError)/i,
      message: "协议存在 Python 语法或导入错误。",
      fixable_by_edit: true,
      suggested_edit_direction: "优先修复 traceback 指向的首个报错行，保持最小改动。",
    },
    {
      category: "API_MISUSE",
      severity: "error",
      regex: /(AttributeError|TypeError|unexpected keyword argument|required positional argument|has no attribute|APIVersionError|not available in API version)/i,
      message: "协议调用了错误的 Opentrons API、参数或 apiLevel。",
      fixable_by_edit: true,
      suggested_edit_direction: "对照当前 `requirements` 和 API 文档，修正方法名、参数签名或提升支持该功能的 `apiLevel`。",
    },
    {
      category: "LABWARE_OR_MODULE_COMPAT",
      severity: "error",
      regex: /(LabwareDefinitionDoesNotExist|LabwareNotLoadedError|ModuleNotLoadedError|DeckConflictError|LocationIsOccupiedError|not compatible|Unsupported.*labware|not valid for this robot)/i,
      message: "labware、module、robotType 或 deck 组合不兼容。",
      fixable_by_edit: true,
      suggested_edit_direction: "核对 robotType、labware load name、module 兼容性和 pipette/tiprack 平台。",
    },
    {
      category: "VOLUME_OR_RANGE_VIOLATION",
      severity: "error",
      regex: /(minimum volume|maximum volume|out of range|InvalidAspirateVolumeError|InvalidDispenseVolumeError|must be between|exceeds pipette volume)/i,
      message: "吸液/分液体积超出移液器或命令允许范围。",
      fixable_by_edit: true,
      suggested_edit_direction: "检查移液器量程和 transfer 体积，必要时拆分步骤或更换 pipette。",
    },
  ];

  for (const pattern of patterns) {
    if (pattern.regex.test(combinedLog)) {
      issues.push({
        category: pattern.category,
        severity: pattern.severity,
        message: pattern.message,
        fixable_by_edit: pattern.fixable_by_edit,
        suggested_edit_direction: pattern.suggested_edit_direction,
        evidence: buildEvidence(combinedLog, pattern.regex),
      });
    }
    pattern.regex.lastIndex = 0;
  }

  if ((exit_code ?? 1) !== 0 && issues.length === 0) {
    issues.push({
      category: "UNKNOWN_NEEDS_HUMAN",
      severity: "error",
      message: "仿真失败，但未匹配到已知问题模式。",
      fixable_by_edit: false,
      suggested_edit_direction: "先阅读原始 stdout/stderr，再决定是补规则还是人工处理。",
      evidence: [truncateLog(combinedLog, 1200)],
    });
  }

  const normalizedIssues = uniqueIssues(issues);
  const status =
    (exit_code ?? 1) === 0 && normalizedIssues.length === 0 ? "passed" : "failed";

  return {
    success: status === "passed",
    status,
    exit_code,
    protocol_path,
    line_references: lineReferences,
    issue_count: normalizedIssues.length,
    issues: normalizedIssues,
    suggested_next_step:
      status === "passed"
        ? "simulation_passed_ready_for_execution"
        : normalizedIssues[0]?.fixable_by_edit
          ? "edit_protocol_and_retry_simulation"
          : "inspect_runtime_or_escalate",
    raw_log_excerpt: truncateLog(combinedLog, 4000),
  };
}

export async function runDoctorTool(args = {}) {
  const helperArgs = [helperScriptPath, "doctor"];
  for (const [key, flag] of [
    ["workspace_root", "--workspace-root"],
    ["api_root", "--api-root"],
    ["shared_data_root", "--shared-data-root"],
    ["python_executable", "--python"],
  ]) {
    if (args[key]) {
      helperArgs.push(flag, args[key]);
    }
  }

  const result = await runHelper(helperArgs, args.python_executable);
  const payload = safeJsonParse(result.stdout.trim());
  payload.helper = {
    runner_python: result.command,
    helper_script: helperScriptPath,
    helper_exit_code: result.code,
  };
  return payload;
}

export async function runSimulationTool(args = {}) {
  if (!args.protocol_path) {
    throw new Error("protocol_path is required");
  }

  const helperArgs = [helperScriptPath, "simulate"];
  for (const [key, flag] of [
    ["workspace_root", "--workspace-root"],
    ["api_root", "--api-root"],
    ["shared_data_root", "--shared-data-root"],
    ["python_executable", "--python"],
  ]) {
    if (args[key]) {
      helperArgs.push(flag, args[key]);
    }
  }
  helperArgs.push(path.resolve(args.protocol_path));

  if (Array.isArray(args.extra_args) && args.extra_args.length > 0) {
    helperArgs.push("--", ...args.extra_args);
  }

  const result = await runHelper(helperArgs, args.python_executable);
  const payload = safeJsonParse(result.stdout.trim());
  payload.stdout = truncateLog(payload.stdout || "", args.max_log_chars || DEFAULT_MAX_LOG_CHARS);
  payload.stderr = truncateLog(payload.stderr || "", args.max_log_chars || DEFAULT_MAX_LOG_CHARS);
  payload.helper = {
    runner_python: result.command,
    helper_script: helperScriptPath,
    helper_exit_code: result.code,
  };
  return payload;
}
