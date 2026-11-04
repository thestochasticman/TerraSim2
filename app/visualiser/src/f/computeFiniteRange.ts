/**
 * The smallest and largest finite values of an array.
 *
 * values : an array of numbers in any unit
 *
 * Returns {min, max} in the same unit, or null when no value is finite.
 */
export function computeFiniteRange(values: ArrayLike<number>): { min: number; max: number } | null {
  let min = Number.POSITIVE_INFINITY;
  let max = Number.NEGATIVE_INFINITY;
  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (!Number.isFinite(v)) continue;
    if (v < min) min = v;
    if (v > max) max = v;
  }
  return min <= max ? { min, max } : null;
}
