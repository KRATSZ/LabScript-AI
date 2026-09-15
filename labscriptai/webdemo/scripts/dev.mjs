import { createServer } from "node:net";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

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
  for (const child of children) {
    if (!child.killed) child.kill("SIGTERM");
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

console.log("webdemo: server http://127.0.0.1:8787  ui http://127.0.0.1:5173  code http://127.0.0.1:8010");
