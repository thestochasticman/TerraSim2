/**
 * Which day a horizontal position on a chart refers to.
 *
 * x : pixels from the left edge of the plot area
 * plotWidth : pixels, the plot area's width
 * nDays : dimensionless, days laid across the plot, day 0 at the left edge and
 *     day nDays - 1 at the right edge
 *
 * Returns the nearest day index, clamped to [0, nDays - 1]; null when there
 * are no days or the plot has no width.
 */
export function pickDay(x: number, plotWidth: number, nDays: number): number | null {
  if (nDays <= 0 || plotWidth <= 0) return null;
  if (nDays === 1) return 0;
  const day = Math.round((x / plotWidth) * (nDays - 1));
  return Math.min(nDays - 1, Math.max(0, day));
}
