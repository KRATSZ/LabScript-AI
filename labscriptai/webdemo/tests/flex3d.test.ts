import { after, before, beforeEach, describe, it } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { createWebdemoServer } from "../server/src/index.ts";
import { flex3dBlocker } from "../server/src/flex3d.ts";
import { createSession, getSession, type SessionState } from "../server/src/session.ts";
import type { RobotModel } from "../server/src/devices.ts";
import type { ChecksResult } from "../server/src/gate.ts";

function commands(count = 1): Array<Record<string, unknown>> {
  return Array.from({ length: count }, (_, index) => ({
    commandType: "home",
    id: `c${index + 1}`,
    params: {},
  }));
}

function passingChecks(): ChecksResult {
  return {
    sim: { ok: true } as unknown as ChecksResult["sim"],
    logicpass: { outcome: "pass", logic_pass: true, final_pass_v2: true } as unknown as ChecksResult["logicpass"],
    statepass: {} as ChecksResult["statepass"],
    fab: { lit: true },
    status: "pass",
  };
}

function sessionFor(robot: RobotModel, overrides: Partial<SessionState> = {}): SessionState {
  const session = createSession();
  session.robot = robot;
  session.analyze = { commands: commands(), createdAt: "2026-10-10T00:00:00Z" };
  session.lastChecks = passingChecks();
  Object.assign(session, overrides);
  return session;
}

describe("flex3dBlocker", () => {
  it("passes OT-2 and Flex scripts with commands and passing checks", () => {
    assert.equal(flex3dBlocker(sessionFor("Flex")), null);
    assert.equal(flex3dBlocker(sessionFor("OT-2")), null);
  });

  it("refuses unsupported robots", () => {
    for (const robot of ["Hamilton", "Vantage", "Tecan"] as const) {
      assert.match(flex3dBlocker(sessionFor(robot)) ?? "", /不支持三维预演/);
    }
  });

  it("refuses when there is no analysis or no command", () => {
    assert.match(flex3dBlocker(sessionFor("OT-2", { analyze: undefined })) ?? "", /分析结果/);
    assert.match(flex3dBlocker(sessionFor("OT-2", { analyze: { commands: [] } })) ?? "", /分析结果/);
  });

  it("refuses when the checks did not pass", () => {
    const failing = { ...passingChecks(), status: "fail" as const, fab: { lit: false } };
    assert.match(flex3dBlocker(sessionFor("OT-2", { lastChecks: failing })) ?? "", /通过检查/);
  });

  it("refuses when there are no checks yet", () => {
    assert.match(flex3dBlocker(sessionFor("OT-2", { lastChecks: undefined })) ?? "", /通过检查/);
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

interface LoadedBody {
  robotType?: unknown;
  createdAt?: unknown;
  commands?: Array<{ id?: string; params?: Record<string, unknown> }>;
  [key: string]: unknown;
}

interface ViewBody {
  source: string;
  key: string;
  note: string;
  info: { title: string };
  error?: string;
  message?: string;
}

describe("GET /api/session/:id/flex3d", () => {
  let player: Server;
  let app: Server;
  let baseUrl = "";
  let priorUrl: string | undefined;
  const seen: string[] = [];
  const loadedBodies: LoadedBody[] = [];
  let exampleRequests = 0;

  before(async () => {
    player = createServer(async (req, res) => {
      const url = req.url || "";
      seen.push(`${req.method} ${url}`);
      if (req.method === "POST" && url === "/flex3d/load") {
        const raw = await readAll(req);
        const body = JSON.parse(raw) as LoadedBody;
        loadedBodies.push(body);
        if (raw.includes("BAD_PIPETTE")) {
          sendJson(res, 422, { error: "unsupported", message: "p300 on the left is not in this scene" });
          return;
        }
        const key = createHash("sha256").update(raw).digest("hex").slice(0, 16);
        sendJson(res, 200, {
          key,
          title: `${String(body.robotType)} chat script`,
          duration: 12.5,
          steps: [],
        });
        return;
      }
      if (req.method === "GET" && url === "/flex3d/example/info") {
        exampleRequests += 1;
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
    loadedBodies.length = 0;
    exampleRequests = 0;
  });

  async function viewFor(session: SessionState): Promise<{ status: number; body: ViewBody }> {
    const res = await fetch(`${baseUrl}/api/session/${session.id}/flex3d`);
    return { status: res.status, body: (await res.json()) as ViewBody };
  }

  function assertNoExample(): void {
    assert.equal(exampleRequests, 0);
    assert.ok(!seen.some((request) => request.includes("/flex3d/example")));
  }

  it("returns 404 for an unknown session", async () => {
    const res = await fetch(`${baseUrl}/api/session/nope/flex3d`);
    assert.equal(res.status, 404);
    assert.equal(((await res.json()) as { error: string }).error, "unknown_session");
  });

  it("forwards an OT-2 session with the canonical OT-2 scene", async () => {
    const session = sessionFor("OT-2");
    const { status, body } = await viewFor(session);

    assert.equal(status, 200);
    assert.equal(body.source, "session");
    assert.equal(body.note, "");
    assert.equal(body.info.title, "OT-2 Standard chat script");
    assert.match(body.key, /^[0-9a-f]{16}$/);
    assert.equal(loadedBodies.length, 1);
    assert.equal(loadedBodies[0].robotType, "OT-2 Standard");
    assert.equal((session.analyze as Record<string, unknown>).robotType, undefined);
    assert.ok(getSession(session.id));
    assertNoExample();
  });

  it("forwards a Flex session with the canonical Flex scene", async () => {
    const session = sessionFor("Flex");
    const { status, body } = await viewFor(session);

    assert.equal(status, 200);
    assert.equal(body.source, "session");
    assert.equal(body.note, "");
    assert.equal(body.info.title, "OT-3 Standard chat script");
    assert.equal(loadedBodies.length, 1);
    assert.equal(loadedBodies[0].robotType, "OT-3 Standard");
    assert.equal((session.analyze as Record<string, unknown>).robotType, undefined);
    assertNoExample();
  });

  it("accepts an explicit robotType that matches the session scene", async () => {
    const session = sessionFor("Flex", {
      analyze: { commands: commands(), createdAt: "2026-10-10T00:00:00Z", robotType: "OT-3 Standard" },
    });
    const { status, body } = await viewFor(session);

    assert.equal(status, 200);
    assert.equal(body.source, "session");
    assert.equal(loadedBodies[0].robotType, "OT-3 Standard");
    assert.equal((session.analyze as Record<string, unknown>).robotType, "OT-3 Standard");
    assertNoExample();
  });

  it("rejects an explicit robotType that conflicts with the session robot", async () => {
    const cases: Array<[RobotModel, string]> = [
      ["OT-2", "OT-3 Standard"],
      ["Flex", "OT-2 Standard"],
    ];
    for (const [robot, wrongType] of cases) {
      const session = sessionFor(robot, {
        analyze: { commands: commands(), createdAt: "2026-10-10T00:00:00Z", robotType: wrongType },
      });
      const { status, body } = await viewFor(session);

      assert.equal(status, 422);
      assert.equal(body.error, "robot_type_mismatch");
      assert.match(body.message ?? "", /不一致/);
      assert.equal((session.analyze as Record<string, unknown>).robotType, wrongType);
    }
    assert.equal(loadedBodies.length, 0);
    assertNoExample();
  });

  it("rejects an unrecognised explicit robotType instead of guessing a scene", async () => {
    const session = sessionFor("OT-2", {
      analyze: { commands: commands(), createdAt: "2026-10-10T00:00:00Z", robotType: "OT-2R" },
    });
    const { status, body } = await viewFor(session);

    assert.equal(status, 422);
    assert.equal(body.error, "robot_type_mismatch");
    assert.equal(loadedBodies.length, 0);
    assert.equal((session.analyze as Record<string, unknown>).robotType, "OT-2R");
    assertNoExample();
  });

  it("rejects explicit malformed robot types without forwarding or mutation", async () => {
    for (const robotType of [[], {}, 0, false, null, "", "  "]) {
      const session = sessionFor("OT-2", { analyze: { commands: commands(), robotType } });
      const { status, body } = await viewFor(session);
      assert.equal(status, 422);
      assert.equal(body.error, "robot_type_mismatch");
      assert.equal(session.analyze?.robotType, robotType);
    }
    assert.equal(loadedBodies.length, 0);
    assertNoExample();
  });

  it("rejects not-ready sessions without loading the example", async () => {
    const failing = { ...passingChecks(), status: "fail" as const, fab: { lit: false } };
    const cases: Array<[string, Partial<SessionState>]> = [
      ["no analysis", { analyze: undefined }],
      ["no commands", { analyze: { commands: [], createdAt: "2026-10-10T00:00:00Z" } }],
      ["no checks", { lastChecks: undefined }],
      ["failed checks", { lastChecks: failing }],
    ];
    for (const [name, overrides] of cases) {
      const { status, body } = await viewFor(sessionFor("Flex", overrides));
      assert.equal(status, 422, name);
      assert.equal(body.error, "not_ready", name);
    }
    assert.equal(loadedBodies.length, 0);
    assertNoExample();
  });

  it("rejects unsupported STAR, Vantage and Fluent sessions without loading the example", async () => {
    for (const robot of ["Hamilton", "Vantage", "Tecan"] as const) {
      const { status, body } = await viewFor(sessionFor(robot));
      assert.equal(status, 422, robot);
      assert.equal(body.error, "unsupported", robot);
      assert.match(body.message ?? "", /不支持三维预演/);
    }
    assert.equal(loadedBodies.length, 0);
    assertNoExample();
  });

  it("serves a changed 80-command analysis as a different current view, not the example", async () => {
    const session = sessionFor("Flex", {
      analyze: { commands: commands(80), createdAt: "version-1" },
    });
    const first = await viewFor(session);
    assert.equal(first.status, 200);
    assert.equal(first.body.source, "session");
    assert.equal(loadedBodies[0].commands?.length, 80);

    session.analyze = { commands: commands(80), createdAt: "version-2" };
    const second = await viewFor(session);
    assert.equal(second.status, 200);
    assert.equal(second.body.source, "session");
    assert.notEqual(second.body.key, first.body.key);
    assert.equal(loadedBodies[1].commands?.length, 80);
    assert.equal(loadedBodies[1].createdAt, "version-2");
    assertNoExample();
  });

  it("preserves the player's unsupported-protocol 422 without falling back", async () => {
    const session = sessionFor("Flex", {
      analyze: {
        commands: [{ ...commands()[0], params: { note: "BAD_PIPETTE" } }],
        createdAt: "2026-10-10T00:00:00Z",
      },
    });
    const { status, body } = await viewFor(session);

    assert.equal(status, 422);
    assert.equal(body.error, "unsupported");
    assert.match(body.message ?? "", /not in this scene/);
    assert.equal(loadedBodies.length, 1);
    assertNoExample();
  });

  it("says so when the player is not running", async () => {
    const currentUrl = process.env.FLEX3D_URL;
    process.env.FLEX3D_URL = "http://127.0.0.1:1";
    try {
      const { status, body } = await viewFor(sessionFor("OT-2"));
      assert.equal(status, 503);
      assert.equal(body.error, "player_unavailable");
      assert.match(body.message ?? "", /稍后重试/);
      assert.doesNotMatch(body.message ?? "", /npm|webdemo|127\.0\.0\.1|fetch failed/);
      assert.equal(loadedBodies.length, 0);
      assertNoExample();
    } finally {
      process.env.FLEX3D_URL = currentUrl;
    }
  });
});
