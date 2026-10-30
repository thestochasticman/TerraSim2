/**
 * Sequential blue ramp, light (dry) to dark (wet). Steps 100 to 700 of the
 * reference palette, as RGB in 0..1.
 */
const RAMP: [number, number, number][] = [
  "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
  "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
].map((hex) => [parseInt(hex.slice(1, 3), 16) / 255, parseInt(hex.slice(3, 5), 16) / 255, parseInt(hex.slice(5, 7), 16) / 255]);

/** Colour for a cell with no usable value: a neutral mid grey. */
export const NO_DATA_COLOUR: [number, number, number] = [0.6, 0.6, 0.6];

/**
 * Map a fullness fraction to a colour on the sequential ramp.
 *
 * fraction : dimensionless
 *     Moisture over capacity. Clamped to [0, 1]; NaN gives NO_DATA_COLOUR.
 *
 * Returns [r, g, b] in 0..1, interpolated linearly between ramp steps.
 */
export function mapMoistureToColour(fraction: number): [number, number, number] {
  if (!Number.isFinite(fraction)) return NO_DATA_COLOUR;
  const f = Math.min(1, Math.max(0, fraction));
  const position = f * (RAMP.length - 1);
  const i = Math.min(RAMP.length - 2, Math.floor(position));
  const w = position - i;
  const [r0, g0, b0] = RAMP[i];
  const [r1, g1, b1] = RAMP[i + 1];
  return [r0 + (r1 - r0) * w, g0 + (g1 - g0) * w, b0 + (b1 - b0) * w];
}
