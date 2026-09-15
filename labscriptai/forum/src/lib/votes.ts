/** Downvote is only useful if it names the failure. No bare thumbs-down. */
export const DOWNVOTE_REASONS = ["crash", "leak", "error"] as const;

export type DownvoteReason = (typeof DOWNVOTE_REASONS)[number];

export const DOWNVOTE_LABELS: Record<DownvoteReason, string> = {
	crash: "Crash — tip or deck collision",
	leak: "Leak — spill or drip",
	error: "Error — a step threw",
};

export type VoteKind = "up" | "down";

export interface StoredVote {
	kind: VoteKind;
	reason?: DownvoteReason;
	note?: string;
}

export function isDownvoteReason(value: unknown): value is DownvoteReason {
	return typeof value === "string" && (DOWNVOTE_REASONS as readonly string[]).includes(value);
}

export function validateDownvote(input: {
	reason?: unknown;
	note?: unknown;
}): { ok: true; reason: DownvoteReason; note: string } | { ok: false; error: string } {
	if (!isDownvoteReason(input.reason)) {
		return { ok: false, error: "Pick crash, leak, or error." };
	}
	const note = typeof input.note === "string" ? input.note.trim() : "";
	return { ok: true, reason: input.reason, note };
}

export const VOTE_STORAGE_KEY = "labscriptai-forum-votes-v1";
