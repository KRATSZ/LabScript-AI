import { requestJson } from "./http.js";

function unwrapData(payload) {
  if (payload && typeof payload === "object" && "data" in payload) {
    return payload.data;
  }
  return payload;
}

function asArray(value) {
  if (Array.isArray(value)) {
    return value;
  }
  if (value && typeof value === "object") {
    return Object.values(value);
  }
  return [];
}

/**
 * Extract one page of run commands plus pagination hints from a robot HTTP payload.
 * Prefer Flex-validated offset pagination (cursor += len(data), totalLength).
 * Also reads meta.nextCursor / links.next when present.
 */
export function parseRunCommandsPage(payload) {
  const unwrapped = unwrapData(payload);
  let commands = [];
  if (Array.isArray(unwrapped)) {
    commands = unwrapped;
  } else if (unwrapped && typeof unwrapped === "object") {
    if (Array.isArray(unwrapped.data)) {
      commands = unwrapped.data;
    } else if (Array.isArray(unwrapped.commands)) {
      commands = unwrapped.commands;
    } else {
      commands = asArray(unwrapped);
    }
  }

  let nextCursor = null;
  let nextHref = null;
  let totalLength = null;

  if (payload && typeof payload === "object") {
    const meta = payload.meta;
    if (meta && typeof meta === "object") {
      if (meta.nextCursor != null) {
        nextCursor = meta.nextCursor;
      }
      if (meta.totalLength != null) {
        totalLength = Number(meta.totalLength);
      }
    }
    const links = payload.links;
    if (links && typeof links === "object") {
      const nxt = links.next;
      if (typeof nxt === "string") {
        nextHref = nxt;
      } else if (nxt && typeof nxt === "object" && nxt.href) {
        nextHref = nxt.href;
      }
    }
  }

  if (nextCursor == null && unwrapped && typeof unwrapped === "object" && !Array.isArray(unwrapped)) {
    const innerMeta = unwrapped.meta;
    if (innerMeta && typeof innerMeta === "object" && innerMeta.nextCursor != null) {
      nextCursor = innerMeta.nextCursor;
    }
  }

  return { commands, nextCursor, nextHref, totalLength };
}

/**
 * Fetch all commands for a run.
 * Primary strategy (validated on Flex): offset cursor += page.length until >= totalLength.
 * Fallback: meta.nextCursor / links.next.
 */
export async function fetchAllRunCommands(
  requestRobotJson,
  robotIp,
  runId,
  { pageLength = 100, maxPages = 50 } = {},
) {
  const all = [];
  let offset = 0;

  for (let page = 0; page < maxPages; page += 1) {
    const payload = await requestRobotJson("GET", robotIp, `/runs/${runId}/commands`, {
      searchParams: {
        pageLength,
        cursor: offset,
      },
    });

    const { commands, nextCursor, nextHref, totalLength } = parseRunCommandsPage(payload);
    all.push(...commands);

    if (commands.length === 0) {
      break;
    }

    // Preferred Flex pagination
    if (Number.isFinite(totalLength)) {
      offset += commands.length;
      if (offset >= totalLength) {
        break;
      }
      continue;
    }

    // Fallbacks
    if (nextHref) {
      const href = nextHref.startsWith("http") ? nextHref : null;
      if (href) {
        const more = await requestJson("GET", href);
        const parsed = parseRunCommandsPage(more);
        all.push(...parsed.commands);
        // Follow remaining next links up to maxPages
        let href2 = parsed.nextHref;
        let guard = 0;
        while (href2 && guard < maxPages - page - 1) {
          const abs = href2.startsWith("http") ? href2 : null;
          if (!abs) {
            break;
          }
          const page2 = parseRunCommandsPage(await requestJson("GET", abs));
          all.push(...page2.commands);
          href2 = page2.nextHref;
          guard += 1;
          if (!page2.commands.length) {
            break;
          }
        }
      }
      break;
    }

    if (nextCursor != null) {
      offset = nextCursor;
      continue;
    }

    // No totalLength / nextCursor — advance by page size once then stop if short page
    if (commands.length < pageLength) {
      break;
    }
    offset += commands.length;
  }

  return all;
}
