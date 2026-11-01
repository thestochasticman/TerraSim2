/**
 * Turn a requested span of days into a valid visible range.
 *
 * start, end : dimensionless
 *     Requested first and last day, in either order.
 * nDays : dimensionless
 *     Days in the run; the range is kept inside [0, nDays - 1].
 * minSpan : dimensionless
 *     Fewest days a range may show. A narrower request is widened around
 *     its centre, then shifted to stay inside the run.
 *
 * Returns [first, last], inclusive, or null when the run has fewer than
 * two days, in which case there is nothing to zoom.
 */
export function clampDayRange(start: number, end: number, nDays: number, minSpan: number = 7): [number, number] | null {
  if (nDays < 2) return null;
  const last = nDays - 1;
  let a = Math.round(Math.min(start, end));
  let b = Math.round(Math.max(start, end));
  const span = Math.min(minSpan, nDays);
  if (b - a + 1 < span) {
    const centre = (a + b) / 2;
    a = Math.round(centre - (span - 1) / 2);
    b = a + span - 1;
  }
  if (a < 0) {
    b -= a;
    a = 0;
  }
  if (b > last) {
    a -= b - last;
    b = last;
  }
  return [Math.max(0, a), Math.min(last, b)];
}
