import { after, before, beforeEach, describe, it } from "node:test";
import assert from "node:assert/strict";
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { createWebdemoServer } from "../server/src/index.ts";
import { flex3dBlocker } from "../server/src/flex3d.ts";
import { createSession, getSession, type SessionState } from "../server/src/session.ts";
import type { ChecksResult } from "../server/src/gate.ts";

const COMMANDS = [{ commandType: "home", id: "c1", params: {} }];

function passingChecks(): ChecksResult {
  return {
    sim: { ok: true } as unknown as ChecksResult["sim"],
    logicpass: { outcome: "pass", logic_pass: true, final_pass_v2: true } as unknown as ChecksResult["logicpass"],
    statepass: {} as ChecksResult["statepass"],
    fab: { lit: true },
    status: "pass",
  };
}

function flexSession(overrides: Partial<SessionState> = {}): SessionState {
  const session = createSession();
  session.robot = "Flex";
  session.analyze = { commands: COMMANDS, createdAt: "2026-10-10T00:00:00Z" };
  session.lastChecks = passingChecks();
  Object.assign(session, overrides);
  return session;
}

describe("flex3dBlocker", () => {
  it("passes a Flex script with commands and passing checks", () => {
    assert.equal(flex3dBlocker(flexSession()), null);
  });

  it("refuses a non-Flex session", () => {
    assert.match(flex3dBlocker(flexSession({ robot: "OT-2" })) ?? "", /不是 Flex/);
  });

  it("refuses when there is no analysis", () => {
    assert.match(flex3dBlocker(flexSession({ analyze: undefined })) ?? "", /分析结果/);
  });

  it("refuses when the checks did not pass", () => {
    const failing = { ...passingChecks(), status: "fail" as const, fab: { lit: false } };
    assert.match(flex3dBlocker(flexSession({ lastChecks: failing })) ?? "", /通过检查/);
  });

  it("refuses when there are no checks yet", () => {
    assert.match(flex3dBlocker(flexSession({ lastChecks: undefined })) ?? "", /通过检查/);
  });
});

async function listen(server: Server): Promise<number> {
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert.ok(address && typeof address === "object");
  return address.port;
}

async function close(server: Server): Promise<void> {
  await new Promise<void>((resolve, reject) =>
    server.close((error) => (error ? reject(error) : resolve()))
  );
}

function readAll(req: IncomingMessage): Promise<string> {
  return new Promise((resolve) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
  });
}

function sendJson(res: ServerResponse, code: number, body: unknown): void {
  res.writeHead(code, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

describe("GET /api/session/:id/flex3d", () => {
  let player: Server;
  let app: Server;
  let baseUrl = "";
  let priorUrl: string | undefined;
  const seen: string[] = [];

  before(async () => {
    player = createServer(async (req, res) => {
      const url = req.url || "";
      seen.push(`${req.method} ${url}`);
      if (req.method === "POST" && url === "/flex3d/load") {
        const body = await readAll(req);
        if (body.includes("BAD_PIPETTE")) {
          sendJson(res, 422, { error: "unsupported", message: "p300 on the left is not in this scene" });
          return;
        }
        sendJson(res, 200, { key: "0123456789abcdef", title: "Chat script", duration: 12.5, steps: [] });
        return;
      }
      if (req.method === "GET" && url === "/flex3d/example/info") {
        sendJson(res, 200, { key: "example", title: "Flex serial dilution (1-channel)", duration: 58.7, steps: [] });
        return;
      }
      sendJson(res, 404, { error: "not_found" });
    });
    const playerPort = await listen(player);
    priorUrl = process.env.FLEX3D_URL;
    process.env.FLEX3D_URL = `http://127.0.0.1:${playerPort}`;
    app = createWebdemoServer();
    baseUrl = `http://127.0.0.1:${await listen(app)}`;
  });

  after(async () => {
    if (priorUrl === undefined) delete process.env.FLEX3D_URL;
    else process.env.FLEX3D_URL = priorUrl;
    await close(app);
    await close(player);
  });

  beforeEach(() => {
    seen.length = 0;
  });

  it("returns 404 for an unknown session", async () => {
    const res = await fetch(`${baseUrl}/api/session/nope/flex3d`);
    assert.equal(res.status, 404);
    assert.equal(((await res.json()) as { error: string }).error, "unknown_session");
  });

  it("shows the session's own passing script with its analysis key", async () => {
    const session = flexSession();
    const res = await fetch(`${baseUrl}/api/session/${session.id}/flex3d`);
    assert.equal(res.status, 200);
    const body = (await res.json()) as { source: string; key: string; note: string; info: { title: string } };
    assert.equal(body.source, "session");
    assert.equal(body.key, "0123456789abcdef");
    assert.equal(body.note, "");
    assert.equal(body.info.title, "Chat script");
    assert.ok(seen.includes("POST /flex3d/load"));
    assert.ok(getSession(session.id));
  });

  it("falls back to the example with a note when the session has no passing script", async () => {
    const session = flexSession({ lastChecks: undefined });
    const res = await fetch(`${baseUrl}/api/session/${session.id}/flex3d`);
    assert.equal(res.status, 200);
    const body = (await res.json()) as { source: string; key: string; note: string };
    assert.equal(body.source, "example");
    assert.equal(body.key, "example");
    assert.match(body.note, /通过检查/);
    assert.ok(!seen.includes("POST /flex3d/load"));
  });

  it("reports a script the player cannot show, without falling back", async () => {
    const session = flexSession({ analyze: { commands: [{ ...COMMANDS[0], params: { note: "BAD_PIPETTE" } }] } });
    const res = await fetch(`${baseUrl}/api/session/${session.id}/flex3d`);
    assert.equal(res.status, 422);
    const body = (await res.json()) as { error: string; message: string };
    assert.equal(body.error, "unsupported");
    assert.match(body.message, /not in this scene/);
  });

  it("says so when the player is not running", async () => {
    process.env.FLEX3D_URL = "http://127.0.0.1:1";
    try {
      const session = flexSession();
      const res = await fetch(`${baseUrl}/api/session/${session.id}/flex3d`);
      assert.equal(res.status, 503);
      assert.equal(((await res.json()) as { error: string }).error, "player_unavailable");
    } finally {
      process.env.FLEX3D_URL = `http://127.0.0.1:${(player.address() as { port: number }).port}`;
    }
  });
});
