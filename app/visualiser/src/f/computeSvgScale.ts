/**
 * How a viewBox is drawn inside an SVG element's box under the default
 * preserveAspectRatio, "xMidYMid meet": scaled uniformly to fit, and centred
 * along the axis with room to spare.
 *
 * boxWidth, boxHeight : pixels, the element's box on screen
 * viewWidth, viewHeight : the viewBox's width and height, in its own units
 *
 * Returns scale, screen pixels per viewBox unit, and offsetX, offsetY, the
 * screen position of the viewBox's origin within the box, pixels. A box or
 * viewBox without area gives scale 1 and no offset, so a mouse position
 * still maps to something.
 */
export function computeSvgScale(boxWidth: number, boxHeight: number, viewWidth: number, viewHeight: number): { scale: number; offsetX: number; offsetY: number } {
  if (!(boxWidth > 0) || !(boxHeight > 0) || !(viewWidth > 0) || !(viewHeight > 0)) return { scale: 1, offsetX: 0, offsetY: 0 };
  const scale = Math.min(boxWidth / viewWidth, boxHeight / viewHeight);
  return { scale, offsetX: (boxWidth - viewWidth * scale) / 2, offsetY: (boxHeight - viewHeight * scale) / 2 };
}
