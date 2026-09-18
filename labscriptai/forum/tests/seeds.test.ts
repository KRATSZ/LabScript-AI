import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const dir = join(dirname(fileURLToPath(import.meta.url)), "../src/content/protocols");

describe("seeded protocol packs", () => {
	const files = readdirSync(dir).filter((name) => name.endsWith(".md"));

	it("has two or three fake posts", () => {
		assert.ok(files.length >= 2 && files.length <= 3, files.join(", "));
	});

	it("each post names device, deck, sop, and script", () => {
		for (const name of files) {
			const text = readFileSync(join(dir, name), "utf8");
			for (const field of ["device:", "deck:", "sop:", "script:"]) {
				assert.ok(text.includes(field), `${name} missing ${field}`);
			}
		}
	});
});
