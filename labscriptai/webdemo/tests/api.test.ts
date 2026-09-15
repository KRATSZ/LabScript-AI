import { after, before, describe, it } from "node:test";
import assert from "node:assert/strict";
import { createServer, type Server } from "node:http";
import { createWebdemoServer } from "../server/src/index.ts";

let backend: Server;
let app: Server;
let baseUrl = "";
let priorBackend: string | undefined;

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

describe("HTTP device API", () => {
  before(async () => {
    backend = createServer((_req, res) => {
      res.writeHead(200);
      res.end("ok");
    });
    const backendPort = await listen(backend);
    priorBackend = process.env.LABSCRIPTAI_BACKEND;
    process.env.LABSCRIPTAI_BACKEND = `http://127.0.0.1:${backendPort}`;

    app = createWebdemoServer();
    baseUrl = `http://127.0.0.1:${await listen(app)}`;
  });

  after(async () => {
    await close(app);
    await close(backend);
    if (priorBackend == null) delete process.env.LABSCRIPTAI_BACKEND;
    else process.env.LABSCRIPTAI_BACKEND = priorBackend;
  });

  it("GET /api/health reports model, key presence, and 8010 without leaking a key", async () => {
    const response = await fetch(`${baseUrl}/api/health`);
    assert.equal(response.status, 200);
    const body = (await response.json()) as Record<string, unknown>;
    assert.equal(body.ok, true);
    assert.equal(typeof body.model, "string");
    assert.equal(typeof body.hasKey, "boolean");
    assert.ok(body.code_service === "up" || body.code_service === "down");
    assert.doesNotMatch(JSON.stringify(body), /sk-/);
  });

  it("GET /api/devices returns five registry entries with capabilities", async () => {
    const response = await fetch(`${baseUrl}/api/devices`);
    assert.equal(response.status, 200);
    const devices = (await response.json()) as Array<Record<string, unknown>>;
    assert.equal(devices.length, 5);
    assert.deepEqual(
      devices.map(({ id }) => id),
      ["ot2", "flex", "hamilton_star", "hamilton_vantage", "tecan_fluent"]
    );
    for (const device of devices) {
      assert.equal(typeof device.label, "string");
      assert.equal(typeof device.capabilities, "object");
    }
  });

  it("POST /api/session maps registry ids and legacy robot strings identically", async () => {
    const pairs = [
      ["tecan_fluent", "Tecan"],
      ["hamilton_star", "Hamilton"],
      ["hamilton_vantage", "Vantage"],
      ["ot2", "OT-2"],
      ["flex", "Flex"],
    ] as const;

    for (const [id, legacy] of pairs) {
      const snapshots = await Promise.all(
        [id, legacy].map(async (robot) => {
          const response = await fetch(`${baseUrl}/api/session`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ goal: "transfer 50 uL", robot }),
          });
          assert.equal(response.status, 200, robot);
          return (await response.json()) as {
            robot: string;
            hardware_config: string;
            hardware: unknown;
          };
        })
      );
      assert.equal(snapshots[0].robot, legacy);
      assert.equal(snapshots[1].robot, legacy);
      assert.deepEqual(snapshots[0].hardware, snapshots[1].hardware);
      assert.equal(snapshots[0].hardware_config, snapshots[1].hardware_config);
    }

    const unknown = await fetch(`${baseUrl}/api/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal: "transfer 50 uL", robot: "unknown_robot" }),
    });
    assert.ok(unknown.status >= 400 && unknown.status < 500);
  });
});
