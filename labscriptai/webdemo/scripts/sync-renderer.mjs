import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");
const repoRoot = path.resolve(root, "../..");
const renderer = path.join(root, "renderer");
const args = process.argv.slice(2);
const sourceArg = args.indexOf("--source");
const requestedSource = sourceArg >= 0 ? args[sourceArg + 1] : null;

if (sourceArg >= 0 && (!requestedSource || requestedSource.startsWith("--"))) {
  throw new Error("--source requires a virtual-lab directory");
}

const candidates = [
  requestedSource && path.resolve(requestedSource),
  process.env.LABSCRIPTAI_RENDERER_SOURCE && path.resolve(process.env.LABSCRIPTAI_RENDERER_SOURCE),
  path.resolve(repoRoot, "../virtual-lab"),
  path.resolve(repoRoot, "../../virtual-lab"),
].filter(Boolean);
const source = candidates.find((candidate) => existsSync(path.join(candidate, "sim", "web_player.py")));
if (!source) {
  throw new Error(`Cannot find a virtual-lab source tree. Tried:\n${candidates.join("\n")}`);
}

function runRsync(sourcePath, destinationPath, extra = []) {
  mkdirSync(path.dirname(destinationPath), { recursive: true });
  const result = spawnSync("rsync", ["-a", ...extra, `${sourcePath}${sourcePath.endsWith(path.sep) ? "" : path.sep}`, destinationPath], {
    encoding: "utf8",
  });
  if (result.status !== 0) {
    throw new Error(`rsync failed for ${sourcePath}: ${result.stderr || result.stdout}`);
  }
}

function copyFile(relativePath) {
  const sourcePath = path.join(source, relativePath);
  const destinationPath = path.join(renderer, relativePath);
  mkdirSync(path.dirname(destinationPath), { recursive: true });
  const result = spawnSync("rsync", ["-a", sourcePath, destinationPath], { encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(`rsync failed for ${relativePath}: ${result.stderr || result.stdout}`);
  }
}

mkdirSync(renderer, { recursive: true });
for (const relativePath of [
  "sim/__init__.py",
  "sim/web_player.py",
  "sim/ot2_protocol.py",
  "sim/ot2_scene.py",
  "sim/ot2_shell.py",
  "sim/ot2_thermocycler.py",
  "sim/play_ot2_protocol.py",
  "sim/flex_protocol.py",
  "sim/flex_scene.py",
  "sim/flex_shell.py",
  "sim/play_protocol.py",
  "cad/ot2/deck/ot2_standard.json",
  "cad/flex/deck/ot3_standard.json",
  "cad/flex/modules/manifest.json",
  "protocols/flex_serial_dilution.analysis.json",
]) {
  copyFile(relativePath);
}

runRsync(path.join(source, "sim", "flex3d_runtime"), path.join(renderer, "sim", "flex3d_runtime"), [
  "--delete",
  "--delete-excluded",
  "--exclude=PARENT_HANDOFF.md",
  "--exclude=INTEGRATION.md",
  "--exclude=SOURCE.json",
  "--exclude=VALIDATION.json",
  "--exclude=__pycache__/",
]);
runRsync(path.join(source, "cad", "ot2", "modules"), path.join(renderer, "cad", "ot2", "modules"), [
  "--delete",
  "--include=*.json",
  "--exclude=*",
]);
runRsync(path.join(source, "cad", "ot2", "stl"), path.join(renderer, "cad", "ot2", "stl"), [
  "--delete",
  "--include=OT-2 Reference Model Basic.STL",
  "--include=OT-2 Reference Model Detailed.STL",
  "--exclude=*",
]);
runRsync(path.join(source, "cad", "flex", "modules"), path.join(renderer, "cad", "flex", "modules"), [
  "--delete",
  "--include=manifest.json",
  "--include=*.json",
  "--include=*/",
  "--include=*/parts/",
  "--include=*/parts/*.obj",
  "--exclude=*",
]);

function replaceOutputAdaptation(relativePath, pattern, replacement, { required = true } = {}) {
  const file = path.join(renderer, relativePath);
  const text = readFileSync(file, "utf8");
  const next = text.replace(pattern, replacement);
  if (required && next === text && !text.includes(replacement)) {
    throw new Error(`Expected output adaptation target in ${relativePath}`);
  }
  writeFileSync(file, next);
}

// The bundle must write generated MuJoCo files to a cache chosen by the host,
// even when the source checkout still has its historical ROOT/exports default.
replaceOutputAdaptation(
  "sim/flex_scene.py",
  /^import json\n(?!import os\n)/m,
  "import json\nimport os\n",
);
replaceOutputAdaptation(
  "sim/flex_scene.py",
  /^EXPORT = .*$/m,
  '_EXPORT_OVERRIDE = os.environ.get("LABSCRIPTAI_RENDERER_EXPORT")\nEXPORT = Path(_EXPORT_OVERRIDE).expanduser().resolve() if _EXPORT_OVERRIDE else ROOT / "exports" / "mujoco"',
);
replaceOutputAdaptation(
  "sim/ot2_scene.py",
  /^import math\n(?!import os\n)/m,
  "import math\nimport os\n",
);
replaceOutputAdaptation(
  "sim/ot2_scene.py",
  /^EXPORT = .*$/m,
  '_EXPORT_OVERRIDE = os.environ.get("LABSCRIPTAI_RENDERER_EXPORT")\nEXPORT = Path(_EXPORT_OVERRIDE).expanduser().resolve() if _EXPORT_OVERRIDE else ROOT / "exports" / "mujoco"',
);
replaceOutputAdaptation(
  "sim/play_protocol.py",
  /^DEFAULT_OPENTRONS_PYTHON = .*$/m,
  'DEFAULT_OPENTRONS_PYTHON = Path(os.environ.get("OPENTRONS_PYTHON", sys.executable))',
);
replaceOutputAdaptation(
  "sim/play_protocol.py",
  /``OPENTRONS_PYTHON`` \(default: the Flexagent ``labscriptai`` venv next to this\nfolder\),/m,
  "``OPENTRONS_PYTHON`` (default: the current renderer interpreter),",
  { required: false },
);

console.log(`renderer synced from ${source} to ${renderer}`);
