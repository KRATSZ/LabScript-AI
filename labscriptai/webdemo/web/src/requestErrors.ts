export const REQUEST_ERRORS = {
  network: "Couldn't reach the server. Check your connection and try again.",
  expired: "This session has expired. Start a new protocol.",
  limited: "Too many requests. Please wait a moment and try again.",
  input: "Please check the experiment description or instrument and try again.",
  unavailable: "The service is temporarily unavailable. Please try again later.",
  unexpected: "Something went wrong. Please try again.",
} as const;

/** Inspect known error codes; never display a raw server response or proxy page. */
export async function responseError(response: Response): Promise<Error> {
  let code = "";
  if (response.headers.get("content-type")?.includes("application/json")) {
    try {
      const body = await response.json();
      if (body && typeof body === "object" && typeof body.error === "string") code = body.error;
    } catch { /* Fall back to the HTTP status. */ }
  }
  const message = code === "unknown_session"
    ? REQUEST_ERRORS.expired
    : response.status === 429
      ? REQUEST_ERRORS.limited
      : response.status >= 500 || response.status === 401 || response.status === 403
        ? REQUEST_ERRORS.unavailable
        : response.status === 400 || response.status === 413 || response.status === 422
          ? REQUEST_ERRORS.input
          : REQUEST_ERRORS.unexpected;
  return new Error(message);
}

export async function request(url: string, init?: RequestInit): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch {
    throw new Error(REQUEST_ERRORS.network);
  }
  if (!response.ok) throw await responseError(response);
  return response;
}

/** Keep short experimental diagnostics, while replacing infrastructure failures. */
export function streamErrorMessage(message: string): string {
  if (/api.?key|credentials?|deepseek|ECONN|ENOTFOUND|traceback|<\/?(?:html|body|script)|\bat .+\(.+:\d+/i.test(message) || message.length > 600) {
    return REQUEST_ERRORS.unavailable;
  }
  return message.trim() || REQUEST_ERRORS.unexpected;
}
