import { computeFiniteRange } from "@/f/computeFiniteRange";
import { mapMoistureToColour } from "@/f/mapMoistureToColour";

/**
 * Per-vertex colours for a terrain mesh from its cells' capacity.
 *
 * capacity : Float64Array of length n, millimetres (mm)
 *     Each cell's capacity; NaN where unknown.
 *
 * Returns a Float32Array of length 3 n, RGB in 0..1: the sequential ramp
 * stretched over the finite range, light at the smallest capacity and dark
 * at the largest, so differences between soils show even when all are
 * similar. A field with one value is all dark. Unknown cells take the
 * no-data grey.
 */
export function computeCapacityColours(capacity: Float64Array): Float32Array {
  const range = computeFiniteRange(capacity);
  const colours = new Float32Array(capacity.length * 3);
  for (let i = 0; i < capacity.length; i++) {
    let fraction = Number.NaN;
    if (range && Number.isFinite(capacity[i])) {
      fraction = range.max > range.min ? (capacity[i] - range.min) / (range.max - range.min) : 1;
    }
    const [r, g, b] = mapMoistureToColour(fraction);
    colours[i * 3] = r;
    colours[i * 3 + 1] = g;
    colours[i * 3 + 2] = b;
  }
  return colours;
}
