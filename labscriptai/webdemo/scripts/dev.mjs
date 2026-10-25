import { createServer } from "node:net";
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { resolveRendererRoot } from "./renderer-root.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(root, "../..");
const python = process.env.LABSCRIPTAI_PYTHON || "python3";

function canBind(host, port) {
  return new Promise((resolve) => {
    const server = createServer();
    server.unref();
    server.once("error", () => resolve(false));
    server.listen(port, host, () => {
      server.close(() => resolve(true));
    });
  });
}

const host = "127.0.0.1";
const required = [8787, 5173];
for (const port of required) {
  if (!(await canBind(host, port))) {
    console.error(`Cannot bind ${host}:${port}. Do not start.`);
    process.exit(1);
  }
}

const children = [
  spawn("npx", ["tsx", "watch", "server/src/index.ts"], {
    cwd: root,
    stdio: "inherit",
    env: process.env,
  }),
  spawn("npx", ["vite", "--config", "web/vite.config.ts"], {
    cwd: root,
    stdio: "inherit",
    env: process.env,
  }),
];

const flex3dPort = 8791;
const rendererRoot = resolveRendererRoot({ root, repoRoot });
const rendererExport = path.resolve(
  process.env.LABSCRIPTAI_RENDERER_EXPORT || path.join(root, ".local", "renderer"),
);
const playerReady =
  existsSync(path.join(rendererRoot, "sim", "web_player.py")) &&
  (await canBind(host, flex3dPort));
const player = playerReady
  ? spawn(python, ["-m", "sim.web_player"], {
      cwd: rendererRoot,
      stdio: "inherit",
      env: {
        ...process.env,
        PYTHONPATH: rendererRoot,
        PYTHONUNBUFFERED: "1",
        FLEX3D_ROOT: process.env.FLEX3D_ROOT || rendererRoot,
        FLEX3D_MODULE_ASSETS:
          process.env.FLEX3D_MODULE_ASSETS || path.join(rendererRoot, "cad", "flex", "modules", "manifest.json"),
        FLEX3D_EXPORT: process.env.FLEX3D_EXPORT || path.join(rendererExport, "flex3d"),
        LABSCRIPTAI_RENDERER_EXPORT: process.env.LABSCRIPTAI_RENDERER_EXPORT || path.join(rendererExport, "mujoco"),
        PLUGIN_DATA: process.env.PLUGIN_DATA || rendererExport,
      },
    })
  : null;
if (!playerReady) {
  console.error(`3D player not started (${host}:${flex3dPort}, ${rendererRoot}). The chat site will still start.`);
}

if (await canBind(host, 8010)) {
  children.push(
    spawn(python, ["python/code_service.py"], {
      cwd: root,
      stdio: "inherit",
      env: { ...process.env, PYTHONPATH: `${root}/python${path.delimiter}${repoRoot}` },
    })
  );
} else {
  console.log("8010 already bound; reusing existing code service");
}

const stop = () => {
  for (const child of [...children, player]) {
    if (child && !child.killed) child.kill("SIGTERM");
  }
};

process.on("SIGINT", stop);
process.on("SIGTERM", stop);
for (const child of children) {
  child.on("exit", (code) => {
    if (code && code !== 0) {
      stop();
      process.exit(code);
    }
  });
}

console.log(
  `webdemo: server http://127.0.0.1:8787  ui http://127.0.0.1:5173  code http://127.0.0.1:8010  flex3d http://127.0.0.1:${flex3dPort}`
);
