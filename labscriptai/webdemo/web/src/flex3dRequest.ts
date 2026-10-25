export class ReplayRequestError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
  }
}

/** A revision cancellation is silent; a live revision's interrupted request is not. */
export async function getReplayJson<T>(
  url: string,
  signal: AbortSignal,
  timeoutMs = 15_000,
): Promise<T> {
  signal.throwIfAborted();
  const deadline = AbortSignal.timeout(timeoutMs);
  try {
    const res = await fetch(url, { signal: AbortSignal.any([signal, deadline]) });
    const body = (await res.json().catch((err: unknown) => {
      // Only tolerate a non-JSON error response; interrupted body reads must
      // reach the caller, even when neither of our controllers was cancelled.
      if (signal.aborted || deadline.aborted || !(err instanceof SyntaxError)) throw err;
      return {};
    })) as Record<string, unknown>;
    if (!res.ok) {
      throw new ReplayRequestError(res.status, typeof body.message === "string" ? body.message : `HTTP ${res.status}`);
    }
    return body as T;
  } catch (err) {
    if (signal.aborted) throw err;
    if (deadline.aborted || (err instanceof DOMException && ["AbortError", "TimeoutError"].includes(err.name))) {
      throw new Error("三维预演请求中断或超时，请重新打开后重试。");
    }
    throw err;
  }
}
