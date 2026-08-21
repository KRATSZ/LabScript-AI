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

  if (unwrapped && typeof unwrapped === "object" && !Array.isArray(unwrapped)) {
    const innerMeta = unwrapped.meta;
    if (innerMeta && typeof innerMeta === "object") {
      if (nextCursor == null && innerMeta.nextCursor != null) {
        nextCursor = innerMeta.nextCursor;
      }
      if (totalLength == null && innerMeta.totalLength != null) {
        totalLength = Number(innerMeta.totalLength);
      }
    }
  }

  return { commands, nextCursor, nextHref, totalLength };
}

/**
 * Fetch all commands from a command-history endpoint.
 * Primary strategy (validated on Flex): offset cursor += page.length until >= totalLength.
 * Fallback: meta.nextCursor / links.next.
 */
export async function fetchAllCommands(
  requestRobotJson,
  robotIp,
  commandsPath,
  { pageLength = 100, maxPages = 1000 } = {},
) {
  const normalizedPageLength = Math.max(1, Math.floor(Number(pageLength) || 100));
  const normalizedMaxPages = Math.max(1, Math.floor(Number(maxPages) || 1000));
  const all = [];
  let offset = 0;
  const seenOffsets = new Set();
  const seenCommandIds = new Set();

  for (let page = 0; page < normalizedMaxPages; page += 1) {
    if (seenOffsets.has(offset)) {
      throw new Error(`Command history pagination repeated cursor ${offset} for ${commandsPath}.`);
    }
    seenOffsets.add(offset);
    const payload = await requestRobotJson("GET", robotIp, commandsPath, {
      searchParams: {
        pageLength: normalizedPageLength,
        cursor: offset,
      },
    });

    const { commands, nextCursor, nextHref, totalLength } = parseRunCommandsPage(payload);

    if (commands.length === 0) {
      return all;
    }

    const commandIds = commands
      .map(command => command?.id || command?.command_id)
      .filter(Boolean);
    if (commandIds.length === commands.length) {
      if (commandIds.some(commandId => seenCommandIds.has(commandId))) {
        throw new Error(`Command history pagination repeated commands for ${commandsPath}.`);
      }
      commandIds.forEach(commandId => seenCommandIds.add(commandId));
    }
    all.push(...commands);

    // Preferred Flex pagination
    if (Number.isFinite(totalLength)) {
      offset += commands.length;
      if (offset >= totalLength) {
        return all.slice(0, Math.max(0, Math.floor(totalLength)));
      }
      continue;
    }

    // Fallbacks
    if (nextHref) {
      const href = nextHref.startsWith("http") ? nextHref : null;
      if (href) {
        const more = await requestJson("GET", href);
        const parsed = parseRunCommandsPage(more);
        const linkedIds = parsed.commands
          .map(command => command?.id || command?.command_id)
          .filter(Boolean);
        if (
          linkedIds.length === parsed.commands.length &&
          linkedIds.some(commandId => seenCommandIds.has(commandId))
        ) {
          throw new Error(`Command history pagination repeated commands for ${commandsPath}.`);
        }
        linkedIds.forEach(commandId => seenCommandIds.add(commandId));
        all.push(...parsed.commands);
        // Follow remaining next links up to maxPages
        let href2 = parsed.nextHref;
        let guard = 0;
        while (href2 && guard < normalizedMaxPages - page - 1) {
          const abs = href2.startsWith("http") ? href2 : null;
          if (!abs) {
            break;
          }
          const page2 = parseRunCommandsPage(await requestJson("GET", abs));
          const page2Ids = page2.commands
            .map(command => command?.id || command?.command_id)
            .filter(Boolean);
          if (
            page2Ids.length === page2.commands.length &&
            page2Ids.some(commandId => seenCommandIds.has(commandId))
          ) {
            throw new Error(`Command history pagination repeated commands for ${commandsPath}.`);
          }
          page2Ids.forEach(commandId => seenCommandIds.add(commandId));
          all.push(...page2.commands);
          href2 = page2.nextHref;
          guard += 1;
          if (!page2.commands.length) {
            break;
          }
        }
        if (href2) {
          throw new Error(`Command history pagination exceeded ${normalizedMaxPages} pages for ${commandsPath}.`);
        }
        return all;
      }
      throw new Error(`Command history returned an unusable next link for ${commandsPath}.`);
    }

    if (nextCursor != null) {
      const nextOffset = Number(nextCursor);
      if (!Number.isFinite(nextOffset) || seenOffsets.has(nextOffset)) {
        throw new Error(`Command history pagination did not advance for ${commandsPath}.`);
      }
      offset = nextOffset;
      continue;
    }

    // No totalLength / nextCursor — advance by page size once then stop if short page
    if (commands.length < normalizedPageLength) {
      return all;
    }
    offset += commands.length;
  }

  throw new Error(
    `Command history pagination exceeded ${normalizedMaxPages} pages for ${commandsPath}.`,
  );
}

/**
 * Fetch all commands for a protocol run.
 */
export async function fetchAllRunCommands(
  requestRobotJson,
  robotIp,
  runId,
  options = {},
) {
  return fetchAllCommands(
    requestRobotJson,
    robotIp,
    `/runs/${runId}/commands`,
    options,
  );
}
