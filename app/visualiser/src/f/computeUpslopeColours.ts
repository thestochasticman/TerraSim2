import { mapMoistureToColour } from "@/f/mapMoistureToColour";

/**
 * Per-vertex colours for a terrain mesh from its upslope cell counts.
 *
 * upslopeCells : Float64Array of length n, dimensionless
 *     How many cells drain through each cell, at least 1.
 *
 * Returns a Float32Array of length 3 n, RGB in 0..1: the sequential ramp
 * over the logarithm of the count, light on ridges where nothing drains
 * through and dark along the channels, so the drainage network shows.
 * Counts below 1 or not finite take the no-data grey.
 */
export function computeUpslopeColours(upslopeCells: Float64Array): Float32Array {
  let max = 1;
  for (let i = 0; i < upslopeCells.length; i++) if (Number.isFinite(upslopeCells[i]) && upslopeCells[i] > max) max = upslopeCells[i];
  const scale = Math.log(max);
  const colours = new Float32Array(upslopeCells.length * 3);
  for (let i = 0; i < upslopeCells.length; i++) {
    const v = upslopeCells[i];
    const fraction = Number.isFinite(v) && v >= 1 ? (scale > 0 ? Math.log(v) / scale : 0) : Number.NaN;
    const [r, g, b] = mapMoistureToColour(fraction);
    colours[i * 3] = r;
    colours[i * 3 + 1] = g;
    colours[i * 3 + 2] = b;
  }
  return colours;
}
