/** Downvote is only useful if it names the failure and the step. No bare thumbs-down. */
export const DOWNVOTE_REASONS = ["crash", "leak", "error"] as const;

export type DownvoteReason = (typeof DOWNVOTE_REASONS)[number];

export const DOWNVOTE_LABELS: Record<DownvoteReason, string> = {
	crash: "Crash — tip or deck collision",
	leak: "Leak — spill or drip",
	error: "Error — a step threw",
};

export type VoteKind = "up" | "down";

export interface FailureReport {
	reason: DownvoteReason;
	step: number;
}

export interface StoredVote {
	kind: VoteKind;
	reason?: DownvoteReason;
	step?: number;
}

export function isDownvoteReason(value: unknown): value is DownvoteReason {
	return typeof value === "string" && (DOWNVOTE_REASONS as readonly string[]).includes(value);
}

export function tallyReasons(reports: Iterable<{ reason: DownvoteReason }>): Record<DownvoteReason, number> {
	const tally: Record<DownvoteReason, number> = { crash: 0, leak: 0, error: 0 };
	for (const report of reports) tally[report.reason] += 1;
	return tally;
}

export function validateDownvote(input: {
	reason?: unknown;
	step?: unknown;
	stepCount?: unknown;
}): { ok: true; reason: DownvoteReason; step: number } | { ok: false; error: string } {
	if (!isDownvoteReason(input.reason)) {
		return { ok: false, error: "Pick crash, leak, or error." };
	}
	const step = typeof input.step === "number" ? input.step : Number(input.step);
	const stepCount = typeof input.stepCount === "number" ? input.stepCount : Number(input.stepCount);
	if (!Number.isInteger(step) || !Number.isInteger(stepCount) || step < 1 || step > stepCount) {
		return { ok: false, error: "Say which step failed." };
	}
	return { ok: true, reason: input.reason, step };
}

export const VOTE_STORAGE_KEY = "labscriptai-forum-votes-v2";
