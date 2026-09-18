import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DOWNVOTE_REASONS, isDownvoteReason, tallyReasons, validateDownvote } from "../src/lib/votes.ts";

describe("downvote reasons", () => {
	it("are crash, leak, and error", () => {
		assert.deepEqual([...DOWNVOTE_REASONS], ["crash", "leak", "error"]);
	});

	it("rejects a downvote with no category", () => {
		const result = validateDownvote({ step: 1, stepCount: 5 });
		assert.equal(result.ok, false);
		if (!result.ok) assert.match(result.error, /crash, leak, or error/i);
	});

	it("rejects an unknown category", () => {
		const result = validateDownvote({ reason: "boring", step: 1, stepCount: 5 });
		assert.equal(result.ok, false);
		assert.equal(isDownvoteReason("boring"), false);
	});

	it("rejects a downvote with no step", () => {
		const result = validateDownvote({ reason: "leak", stepCount: 5 });
		assert.equal(result.ok, false);
		if (!result.ok) assert.match(result.error, /which step/i);
	});

	it("accepts each required category with a step", () => {
		for (const reason of DOWNVOTE_REASONS) {
			const result = validateDownvote({ reason, step: "3", stepCount: 5 });
			assert.equal(result.ok, true);
			if (result.ok) {
				assert.equal(result.reason, reason);
				assert.equal(result.step, 3);
			}
		}
	});

	it("tallies crash leak error counts", () => {
		assert.deepEqual(tallyReasons([{ reason: "leak" }, { reason: "leak" }, { reason: "crash" }]), {
			crash: 1,
			leak: 2,
			error: 0,
		});
	});
});
