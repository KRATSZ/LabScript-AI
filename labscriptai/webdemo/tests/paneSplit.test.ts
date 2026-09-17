import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { CHAT_DEFAULT, CHAT_MAX, CHAT_MIN, clampChatPct, historyWidthPx } from "../web/src/paneSplit.ts";
import { archiveThread, railThreads, threadTitle } from "../web/src/threadArchive.ts";
import type { SessionSnapshot } from "../web/src/types.ts";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

describe("paneSplit", () => {
  it("clamps chat to 28–46% and at least 280px", () => {
    assert.equal(clampChatPct(0.38, 1440), CHAT_DEFAULT);
    assert.equal(clampChatPct(0.1, 1440), CHAT_MIN);
    assert.equal(clampChatPct(0.9, 1440), CHAT_MAX);
    assert.equal(clampChatPct(0.2, 800), 280 / 800);
    assert.equal(historyWidthPx(false, true), 32);
    assert.equal(historyWidthPx(true, true), 220);
    assert.equal(historyWidthPx(true, false), 0);
  });
});

describe("threadArchive", () => {
  it("titles and upserts the current run without eating older ones", () => {
    assert.match(threadTitle("Transfer 20 µL from well A1 to B1", "OT-2"), /^OT-2 · Transfer 20/);
    const session = { id: "s1", goal: "20 µL A1 to B1", robot: "OT-2", device_label: "OT-2" } as SessionSnapshot;
    const first = archiveThread([], session, [{ role: "user", text: "go" }], []);
    assert.equal(first.length, 1);
    assert.equal(first[0].id, "s1");
    const second = archiveThread(first, { ...session, id: "s2", goal: "STAR run" }, [{ role: "user", text: "star" }], []);
    assert.equal(second.length, 2);
    assert.equal(second[0].id, "s2");
    const live = railThreads([], session, [{ role: "user", text: "go" }], []);
    assert.equal(live[0].id, "s1");
    assert.equal(live.length, 1);
  });
});

describe("locked right-pane layout", () => {
  it("keeps chat 28–46% default 38%, one seam, and a right history rail", () => {
    const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
    const css = readFileSync(path.join(root, "web/src/styles.css"), "utf8");
    const app = readFileSync(path.join(root, "web/src/App.tsx"), "utf8");
    const traj = readFileSync(path.join(root, "web/src/TrajectoryPane.tsx"), "utf8");
    assert.match(css, /--chat-pct:\s*38%/);
    assert.match(css, /minmax\(280px,\s*var\(--chat-pct\)\)/);
    assert.match(css, /--history-collapsed:\s*32px/);
    assert.match(css, /--history-open:\s*220px/);
    assert.match(css, /\.split-seam/);
    assert.match(css, /\.history-rail\.present\.open/);
    assert.match(css, /\.activity-pane[\s\S]*width:\s*100%/);
    assert.doesNotMatch(css, /\.activity-pane[\s\S]{0,120}width:\s*min\(520px/);
    assert.match(app, /data-testid="split-seam"/);
    assert.match(app, /HistoryRail/);
    assert.doesNotMatch(app, /10%\s*[–-]\s*90%/);
    assert.match(traj, /activity-stream/);
    assert.match(traj, /activity-line/);
    assert.match(traj, /data-testid="activity-note"/);
    assert.match(traj, /data-testid="activity-file"/);
    assert.match(traj, /step\.status === "run" \? "" : formatDuration/);
    assert.match(traj, /activityFollowsTail/);
    assert.match(traj, /pinRef/);
    assert.match(traj, /data-status=\{step\.status\}/);
  });
});
