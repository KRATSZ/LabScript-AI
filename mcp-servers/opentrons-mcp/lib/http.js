const DEFAULT_VERSION_HEADER = process.env.OPENTRONS_VERSION || "4";
const DEFAULT_PORT = process.env.OPENTRONS_PORT || "31950";

function safeJsonParse(text) {
  if (!text) {
    return null;
  }
  return JSON.parse(text);
}

export function normalizeBaseUrl(robotIp) {
  if (robotIp && /^https?:\/\//i.test(robotIp)) {
    return robotIp.replace(/\/$/, "");
  }
  if (robotIp) {
    if (/^[^/]+:\d+$/.test(robotIp)) {
      return `http://${robotIp}`;
    }
    return `http://${robotIp}:${DEFAULT_PORT}`;
  }
  if (process.env.OPENTRONS_HOST) {
    return process.env.OPENTRONS_HOST.replace(/\/$/, "");
  }
  throw new Error("robot_ip is required unless OPENTRONS_HOST is set.");
}

export function buildRobotUrl(robotIp, pathname, searchParams = null) {
  const url = new URL(`${normalizeBaseUrl(robotIp)}${pathname}`);
  if (searchParams) {
    for (const [key, value] of Object.entries(searchParams)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

export async function requestJson(method, url, { headers = {}, body = null } = {}) {
  try {
    const response = await fetch(url, {
      method,
      headers: {
        "Opentrons-Version": DEFAULT_VERSION_HEADER,
        ...headers,
      },
      body,
    });

    const contentType = response.headers.get("content-type") || "";
    const rawText = await response.text();
    let data;

    if (contentType.includes("application/json")) {
      data = safeJsonParse(rawText || "null");
    } else {
      data = rawText;
    }

    if (!response.ok) {
      const error = new Error(
        JSON.stringify(
          {
            status: response.status,
            statusText: response.statusText,
            error: data,
          },
          null,
          2,
        ),
      );
      error.response = data;
      throw error;
    }

    return data;
  } catch (error) {
    if (error instanceof Error && error.message !== "fetch failed") {
      throw error;
    }

    const causeCode = error?.cause?.code || null;
    const causeMessage = error?.cause?.message || error?.message || "unknown network error";
    throw new Error(
      `Network request failed for ${method} ${url}: ${causeCode ? `${causeCode}: ` : ""}${causeMessage}`,
    );
  }
}

export async function requestBytes(method, url, { headers = {}, body = null } = {}) {
  try {
    const response = await fetch(url, {
      method,
      headers: {
        "Opentrons-Version": DEFAULT_VERSION_HEADER,
        ...headers,
      },
      body,
    });

    const contentType = response.headers.get("content-type") || "";
    const data = Buffer.from(await response.arrayBuffer());

    if (!response.ok) {
      const error = new Error(
        JSON.stringify(
          {
            status: response.status,
            statusText: response.statusText,
            error: contentType.includes("application/json")
              ? safeJsonParse(data.toString("utf8") || "null")
              : data.toString("utf8"),
          },
          null,
          2,
        ),
      );
      error.response = data;
      throw error;
    }

    return {
      data,
      contentType,
      headers: Object.fromEntries(response.headers.entries()),
    };
  } catch (error) {
    if (error instanceof Error && error.message !== "fetch failed") {
      throw error;
    }

    const causeCode = error?.cause?.code || null;
    const causeMessage = error?.cause?.message || error?.message || "unknown network error";
    throw new Error(
      `Network request failed for ${method} ${url}: ${causeCode ? `${causeCode}: ` : ""}${causeMessage}`,
    );
  }
}

export async function requestRobotJson(
  method,
  robotIp,
  pathname,
  { headers = {}, body = null, searchParams = null } = {},
) {
  return requestJson(method, buildRobotUrl(robotIp, pathname, searchParams), {
    headers,
    body,
  });
}

export async function requestRobotBytes(
  method,
  robotIp,
  pathname,
  { headers = {}, body = null, searchParams = null } = {},
) {
  return requestBytes(method, buildRobotUrl(robotIp, pathname, searchParams), {
    headers,
    body,
  });
}
