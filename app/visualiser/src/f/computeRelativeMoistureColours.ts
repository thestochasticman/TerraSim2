import { computeFiniteRange } from "@/f/computeFiniteRange";
import { mapMoistureToColour } from "@/f/mapMoistureToColour";

/**
 * Per-vertex colours for a terrain mesh from one day's moisture, stretched over that day's range.
 *
 * moisture : Float32Array of length n, millimetres (mm)
 *
 * Returns a Float32Array of length 3 n, RGB in 0..1: the sequential ramp
 * with the day's driest cell lightest and its wettest darkest, so the
 * spatial pattern shows however small the spread. A day with one value
 * is all dark; non-finite cells take the no-data grey. The absolute
 * level is lost, which is what the fullness colouring is for.
 */
export function computeRelativeMoistureColours(moisture: Float32Array): Float32Array {
  const range = computeFiniteRange(moisture);
  const colours = new Float32Array(moisture.length * 3);
  for (let i = 0; i < moisture.length; i++) {
    let fraction = Number.NaN;
    if (range && Number.isFinite(moisture[i])) {
      fraction = range.max > range.min ? (moisture[i] - range.min) / (range.max - range.min) : 1;
    }
    const [r, g, b] = mapMoistureToColour(fraction);
    colours[i * 3] = r;
    colours[i * 3 + 1] = g;
    colours[i * 3 + 2] = b;
  }
  return colours;
}
