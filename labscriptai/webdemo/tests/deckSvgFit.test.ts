import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { applyDeckSvgFit, clearDeckSvgFit, deckSvgFit, DECK_SVG_FIT_PAD } from "../web/src/deckSvgFit.ts";

describe("deckSvgFit", () => {
  it("scales a Flex viewBox into a phone deck cell with padding for the step label", () => {
    const viewBox = { width: 854.995, height: 581.74 };
    const box = { width: 390, height: 265 };
    const fit = deckSvgFit(viewBox, box);
    assert.ok(fit);
    const pad = DECK_SVG_FIT_PAD;
    const scale = Math.min((box.width - pad * 2) / viewBox.width, (box.height - pad * 2) / viewBox.height);
    assert.equal(fit.scale, scale);
    assert.ok(scale < 0.5);
    assert.equal(fit.width, viewBox.width);
    assert.equal(fit.height, viewBox.height);
    assert.ok(Math.abs(fit.left - (box.width - viewBox.width * scale) / 2) < 1e-9);
    assert.ok(Math.abs(fit.top - (box.height - viewBox.height * scale) / 2) < 1e-9);
    assert.ok(fit.top >= pad - 0.01);
    assert.ok(fit.left >= pad - 0.01);
  });

  it("uses the tighter axis so a wide cell does not crop the deck", () => {
    const fit = deckSvgFit({ width: 855, height: 582 }, { width: 200, height: 400 });
    assert.ok(fit);
    assert.equal(fit.scale, (200 - DECK_SVG_FIT_PAD * 2) / 855);
  });

  it("returns null when the cell is too small to pad", () => {
    assert.equal(deckSvgFit({ width: 855, height: 582 }, { width: 0, height: 265 }), null);
    assert.equal(deckSvgFit({ width: 855, height: 582 }, { width: 10, height: 10 }), null);
    assert.equal(deckSvgFit({ width: 0, height: 582 }, { width: 390, height: 265 }), null);
  });

  it("writes a CSS scale that overrides the phone width:100% rule and can be cleared", () => {
    const style = {} as CSSStyleDeclaration;
    const svg = { style, dataset: {} as DOMStringMap } as SVGSVGElement;
    const fit = applyDeckSvgFit(svg, { width: 855, height: 582 }, { width: 390, height: 265 });
    assert.ok(fit);
    assert.equal(style.position, "absolute");
    assert.equal(style.width, "855px");
    assert.equal(style.maxWidth, "none");
    assert.equal(style.flex, "none");
    assert.equal(style.transformOrigin, "0 0");
    assert.match(style.transform, /^scale\(0\.4/);
    assert.doesNotMatch(style.transform, /scaleY/);
    assert.equal(style.overflow, "visible");
    assert.equal(svg.dataset.deckFit, String(fit.scale));
    clearDeckSvgFit(svg);
    assert.equal(style.transform, "");
    assert.equal(style.position, "");
    assert.equal(svg.dataset.deckFit, undefined);
  });
});
