import { createServer } from "node:net";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

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
const ports = [8787, 5173];
for (const port of ports) {
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

console.log("webdemo: server http://127.0.0.1:8787  ui http://127.0.0.1:5173");
