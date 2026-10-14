import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { formatFetchedPages, parseSearchHtml } from "../server/src/fetch_url.ts";

describe("parseSearchHtml", () => {
  it("extracts DuckDuckGo titles, decoded links, and snippets", () => {
    const html = `
      <div class="result">
        <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fprotocol">
          Plate reader calibration
        </a>
        <a class="result__snippet">Serial 2-fold 100 µL protocol</a>
      </div>
    `;
    const hits = parseSearchHtml(html);
    assert.equal(hits.length, 1);
    assert.equal(hits[0].title, "Plate reader calibration");
    assert.equal(hits[0].url, "https://example.com/protocol");
    assert.match(hits[0].snippet, /Serial 2-fold/);
  });
});

describe("formatFetchedPages", () => {
  it("includes the opened page text and truncates a long body", () => {
    const text = formatFetchedPages([{ url: "https://example.com/a", chars: 3, body: "100 µL from A1" }], 80);
    assert.match(text, /https:\/\/example\.com\/a/);
    assert.match(text, /100 µL from A1/);
    const long = formatFetchedPages([{ url: "https://example.com/b", chars: 200, body: "x".repeat(200) }], 40);
    assert.match(long, /\[truncated\]/);
    assert.equal(long.includes("x".repeat(80)), false);
  });
});
