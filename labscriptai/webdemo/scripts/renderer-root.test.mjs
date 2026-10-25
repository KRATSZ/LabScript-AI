import assert from "node:assert/strict";
import test from "node:test";
import path from "node:path";
import { rendererCandidates, resolveRendererRoot } from "./renderer-root.mjs";

const root = "/product/webdemo";
const repoRoot = "/product";
const bundled = path.join(root, "renderer");
const sibling = path.resolve(repoRoot, "../virtual-lab");

function existsFor(...roots) {
  const accepted = new Set(roots);
  return (candidate) => [...accepted].some((rootPath) => candidate === path.join(rootPath, "sim", "web_player.py"));
}

test("bundled renderer wins when no override is set", () => {
  assert.deepEqual(rendererCandidates({ root, repoRoot, env: {} }), [bundled, sibling, "/virtual-lab"]);
  assert.equal(resolveRendererRoot({ root, repoRoot, env: {}, exists: existsFor(bundled) }), bundled);
});

test("explicit LABSCRIPTAI_PLAYER_ROOT remains first and exclusive", () => {
  const override = "/tmp/labscriptai-renderer";
  assert.deepEqual(rendererCandidates({ root, repoRoot, env: { LABSCRIPTAI_PLAYER_ROOT: override } }), [override]);
  assert.equal(resolveRendererRoot({ root, repoRoot, env: { LABSCRIPTAI_PLAYER_ROOT: override }, exists: existsFor(override) }), override);
});

test("external checkout is only used when the bundled runtime is absent", () => {
  assert.equal(resolveRendererRoot({ root, repoRoot, env: {}, exists: existsFor(sibling) }), sibling);
});

test("missing roots retain the bundled path for the existing not-started diagnostic", () => {
  assert.equal(resolveRendererRoot({ root, repoRoot, env: {}, exists: () => false }), bundled);
});
