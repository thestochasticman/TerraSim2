import { mapMoistureToColour } from "@/f/mapMoistureToColour";

/**
 * Per-vertex colours for a terrain mesh from its cells' capacity.
 *
 * capacity : Float64Array of length n, millimetres (mm)
 *     Each cell's capacity; NaN where unknown.
 *
 * Returns a Float32Array of length 3 n, RGB in 0..1: the sequential ramp
 * from light at zero to dark at the largest finite capacity, so the map
 * reads as "how much this soil can hold". Unknown cells take the no-data grey.
 */
export function computeCapacityColours(capacity: Float64Array): Float32Array {
  let max = 0;
  for (let i = 0; i < capacity.length; i++) if (Number.isFinite(capacity[i]) && capacity[i] > max) max = capacity[i];
  const colours = new Float32Array(capacity.length * 3);
  for (let i = 0; i < capacity.length; i++) {
    const fraction = max > 0 && Number.isFinite(capacity[i]) ? capacity[i] / max : Number.NaN;
    const [r, g, b] = mapMoistureToColour(fraction);
    colours[i * 3] = r;
    colours[i * 3 + 1] = g;
    colours[i * 3 + 2] = b;
  }
  return colours;
}
