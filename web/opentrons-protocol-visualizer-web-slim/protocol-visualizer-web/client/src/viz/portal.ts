/** Portal root for tooltips / overlays (desktop app uses a dedicated DOM node). */
export function getTopPortalEl(): HTMLElement {
  if (typeof document === 'undefined') {
    throw new Error('getTopPortalEl requires a browser document')
  }
  return document.body
}
