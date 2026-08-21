import assert from "node:assert/strict";
import test from "node:test";

import { fetchAllRunCommands, parseRunCommandsPage } from "./run-commands.js";

test("parseRunCommandsPage reads meta.nextCursor from top-level envelope", () => {
  const payload = {
    data: [{ commandType: "comment", params: { message: "a" } }],
    meta: { nextCursor: 100 },
  };
  const page = parseRunCommandsPage(payload);
  assert.equal(page.commands.length, 1);
  assert.equal(page.nextCursor, 100);
});

test("fetchAllRunCommands follows cursor until exhausted", async () => {
  const calls = [];
  const requestRobotJson = async (_method, _robotIp, pathname, { searchParams } = {}) => {
    calls.push({ pathname, searchParams: { ...searchParams } });
    if (!searchParams?.cursor) {
      return {
        data: [{ id: "1", commandType: "comment", params: { message: "p1" } }],
        meta: { nextCursor: 100 },
      };
    }
    return {
      data: [{ id: "2", commandType: "comment", params: { message: "PRESSURE_TRACE:A1:1/1:YQ==" } }],
      meta: {},
    };
  };

  const all = await fetchAllRunCommands(requestRobotJson, "10.0.0.1", "run-1", {
    pageLength: 50,
    maxPages: 5,
  });
  assert.equal(all.length, 2);
  assert.equal(calls.length, 2);
  assert.equal(calls[1].searchParams.cursor, 100);
});
