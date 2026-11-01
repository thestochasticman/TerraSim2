/**
 * Which day a horizontal position on a chart refers to.
 *
 * x : pixels from the left edge of the plot area
 * plotWidth : pixels, the plot area's width
 * nDays : dimensionless, days in the run
 * range : [first, last] inclusive, the days laid across the plot, first at
 *     the left edge and last at the right; the whole run when omitted
 *
 * Returns the nearest day index, clamped to the range; null when there
 * are no days or the plot has no width.
 */
export function pickDay(x: number, plotWidth: number, nDays: number, range?: [number, number]): number | null {
  if (nDays <= 0 || plotWidth <= 0) return null;
  const [first, last] = range ?? [0, nDays - 1];
  if (last <= first) return first;
  const day = Math.round(first + (x / plotWidth) * (last - first));
  return Math.min(last, Math.max(first, day));
}
