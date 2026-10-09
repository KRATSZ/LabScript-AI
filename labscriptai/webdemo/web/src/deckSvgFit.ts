/** Phone layout breakpoint. Matches the Watch stack in styles.css. */
export const PHONE_LAYOUT_QUERY = "(max-width: 860px)";

/**
 * Gap between the scaled deck and the cell edge so a step label sitting on
 * the labware is not flush with overflow:hidden or the progress bar.
 */
export const DECK_SVG_FIT_PAD = 8;

export interface DeckBox {
  width: number;
  height: number;
}

export interface DeckSvgFit {
  scale: number;
  left: number;
  top: number;
  width: number;
  height: number;
}

/**
 * Fit a deck SVG into a phone cell by drawing it at its viewBox size and
 * scaling with a CSS transform.
 *
 * Mobile WebKit does not scale foreignObject HTML with the SVG viewBox, so a
 * step highlight stays about one CSS pixel per millimetre (~128px) while the
 * deck drawing shrinks to the cell. A CSS transform scales the highlight and
 * its label with the labware.
 */
export function deckSvgFit(viewBox: DeckBox, box: DeckBox, pad = DECK_SVG_FIT_PAD): DeckSvgFit | null {
  if (!(viewBox.width > 0) || !(viewBox.height > 0) || !(box.width > 0) || !(box.height > 0)) return null;
  const innerW = box.width - pad * 2;
  const innerH = box.height - pad * 2;
  if (!(innerW > 0) || !(innerH > 0)) return null;
  const scale = Math.min(innerW / viewBox.width, innerH / viewBox.height);
  if (!Number.isFinite(scale) || !(scale > 0)) return null;
  const drawnW = viewBox.width * scale;
  const drawnH = viewBox.height * scale;
  return {
    scale,
    left: (box.width - drawnW) / 2,
    top: (box.height - drawnH) / 2,
    width: viewBox.width,
    height: viewBox.height,
  };
}

const FIT_STYLE_PROPS = [
  "position",
  "left",
  "top",
  "width",
  "height",
  "maxWidth",
  "maxHeight",
  "minWidth",
  "minHeight",
  "flex",
  "transform",
  "transformOrigin",
  "overflow",
] as const;

export function clearDeckSvgFit(svg: SVGSVGElement): void {
  for (const prop of FIT_STYLE_PROPS) svg.style[prop] = "";
  delete svg.dataset.deckFit;
}

/** Size `svg` to its viewBox and scale it into `box`. Returns false when the box cannot fit. */
export function applyDeckSvgFit(
  svg: SVGSVGElement,
  viewBox: DeckBox,
  box: DeckBox,
  pad = DECK_SVG_FIT_PAD
): DeckSvgFit | null {
  const fit = deckSvgFit(viewBox, box, pad);
  if (!fit) {
    clearDeckSvgFit(svg);
    return null;
  }
  svg.style.position = "absolute";
  svg.style.left = `${fit.left}px`;
  svg.style.top = `${fit.top}px`;
  svg.style.width = `${fit.width}px`;
  svg.style.height = `${fit.height}px`;
  svg.style.maxWidth = "none";
  svg.style.maxHeight = "none";
  svg.style.minWidth = `${fit.width}px`;
  svg.style.minHeight = `${fit.height}px`;
  svg.style.flex = "none";
  svg.style.transformOrigin = "0 0";
  svg.style.transform = `scale(${fit.scale})`;
  svg.style.overflow = "visible";
  svg.dataset.deckFit = String(fit.scale);
  return fit;
}

export function findDeckSvg(host: ParentNode): SVGSVGElement | null {
  const svg = host.querySelector("[class*='deck_svg_wrapper'] > svg");
  return svg instanceof SVGSVGElement ? svg : null;
}

/** Keep the phone deck SVG scaled to its cell. Desktop inline styles are cleared. */
export function syncPhoneDeckSvg(host: HTMLElement): void {
  const svg = findDeckSvg(host);
  if (!svg) return;
  const phone = typeof window.matchMedia === "function" && window.matchMedia(PHONE_LAYOUT_QUERY).matches;
  if (!phone) {
    clearDeckSvgFit(svg);
    return;
  }
  const wrapper = svg.parentElement;
  const wrapperBox = wrapper?.getBoundingClientRect();
  const hostBox = host.getBoundingClientRect();
  const box = wrapperBox && wrapperBox.width > 40 && wrapperBox.height > 40 ? wrapperBox : hostBox;
  const vb = svg.viewBox.baseVal;
  applyDeckSvgFit(svg, { width: vb.width, height: vb.height }, { width: box.width, height: box.height });
}
