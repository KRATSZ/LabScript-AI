import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import {
  applyForm,
  createSession,
  getSession,
  snapshot,
  type RobotModel,
} from "./session.ts";
import { createSseWriter } from "./sse.ts";
import { runChatTurn } from "./agent.ts";
import { loadDemoEnv } from "./env.ts";

const HOST = "127.0.0.1";
const PORT = Number(process.env.WEBDEMO_PORT || 8787);

function json(res: ServerResponse, code: number, body: unknown): void {
  res.writeHead(code, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(body));
}

async function readBody(req: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(Buffer.from(chunk));
  return Buffer.concat(chunks).toString("utf8");
}

function notFound(res: ServerResponse): void {
  json(res, 404, { error: "not_found" });
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url || "/", `http://${HOST}:${PORT}`);
  const path = url.pathname;

  if (req.method === "GET" && (path === "/" || path === "/index.html")) {
    res.writeHead(302, { Location: "http://127.0.0.1:5173/" });
    res.end();
    return;
  }

  if (req.method === "GET" && path === "/api/health") {
    const env = loadDemoEnv();
    json(res, 200, {
      ok: true,
      bind: `${HOST}:${PORT}`,
      backend: env.backend,
      model: env.model,
      hasKey: Boolean(env.apiKey),
    });
    return;
  }

  if (req.method === "POST" && path === "/api/session") {
    const raw = await readBody(req);
    const body = raw ? (JSON.parse(raw) as { goal?: string; doc?: string; robot?: string }) : {};
    const goal = (body.goal || "").trim();
    const robot =
      body.robot === "OT-2" ||
      body.robot === "Flex" ||
      body.robot === "Hamilton" ||
      body.robot === "Tecan"
        ? (body.robot as RobotModel)
        : undefined;
    if (!goal) {
      json(res, 400, { error: "goal is required" });
      return;
    }
    const session = createSession();
    applyForm(session, { goal, doc: body.doc, robot });
    json(res, 200, snapshot(session));
    return;
  }

  const sessionMatch = path.match(/^\/api\/session\/([^/]+)$/);
  if (req.method === "GET" && sessionMatch) {
    const session = getSession(sessionMatch[1]);
    if (!session) {
      json(res, 404, { error: "unknown_session" });
      return;
    }
    json(res, 200, snapshot(session));
    return;
  }

  if (req.method === "POST" && path === "/api/chat/stream") {
    const raw = await readBody(req);
    const body = raw
      ? (JSON.parse(raw) as { sessionId?: string; message?: string })
      : {};
    const session = body.sessionId ? getSession(body.sessionId) : undefined;
    if (!session) {
      json(res, 404, { error: "unknown_session" });
      return;
    }
    const sse = createSseWriter(res);
    try {
      await runChatTurn(session, body.message || "", sse);
      sse.write("done", { ok: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      sse.write("error", { message });
      sse.write("done", { ok: false });
    } finally {
      sse.close();
    }
    return;
  }

  notFound(res);
});

server.on("error", (error: NodeJS.ErrnoException) => {
  if (error.code === "EADDRINUSE" || error.code === "EADDRNOTAVAIL") {
    console.error(`Cannot bind ${HOST}:${PORT}. Do not start.`);
    process.exit(1);
  }
  throw error;
});

try {
  loadDemoEnv();
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}

server.listen(PORT, HOST, () => {
  console.log(`webdemo server http://${HOST}:${PORT}`);
});
