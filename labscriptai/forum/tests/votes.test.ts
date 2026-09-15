import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DOWNVOTE_REASONS, isDownvoteReason, validateDownvote } from "../src/lib/votes.ts";

describe("downvote reasons", () => {
	it("are crash, leak, and error", () => {
		assert.deepEqual([...DOWNVOTE_REASONS], ["crash", "leak", "error"]);
	});

	it("rejects a downvote with no category", () => {
		const result = validateDownvote({});
		assert.equal(result.ok, false);
		if (!result.ok) assert.match(result.error, /crash, leak, or error/i);
	});

	it("rejects an unknown category", () => {
		const result = validateDownvote({ reason: "boring" });
		assert.equal(result.ok, false);
		assert.equal(isDownvoteReason("boring"), false);
	});

	it("accepts each required category", () => {
		for (const reason of DOWNVOTE_REASONS) {
			const result = validateDownvote({ reason, note: " step 3 " });
			assert.equal(result.ok, true);
			if (result.ok) {
				assert.equal(result.reason, reason);
				assert.equal(result.note, "step 3");
			}
		}
	});
});
