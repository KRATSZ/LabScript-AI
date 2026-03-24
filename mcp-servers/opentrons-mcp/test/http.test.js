import test from "node:test";
import assert from "node:assert/strict";

import { buildRobotUrl, normalizeBaseUrl } from "../lib/http.js";

test("normalizeBaseUrl accepts bare host", () => {
  assert.equal(normalizeBaseUrl("10.31.2.149"), "http://10.31.2.149:31950");
});

test("normalizeBaseUrl accepts host with explicit port", () => {
  assert.equal(normalizeBaseUrl("10.31.2.149:31950"), "http://10.31.2.149:31950");
});

test("buildRobotUrl appends path and query params", () => {
  assert.equal(
    buildRobotUrl("10.31.2.149:31950", "/runs", { pageLength: 10 }),
    "http://10.31.2.149:31950/runs?pageLength=10",
  );
});
