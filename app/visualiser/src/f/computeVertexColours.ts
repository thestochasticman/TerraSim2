import { mapMoistureToColour } from "@/f/mapMoistureToColour";

/**
 * Per-vertex colours for a terrain mesh from one day's moisture.
 *
 * Each cell is one vertex, so the colour array has three floats per cell in
 * the same row-major order as the moisture.
 *
 * moisture : Float32Array of length n, millimetres (mm)
 * capacity : Float64Array of length n, millimetres (mm), or undefined
 *     When absent, fullness is moisture over the day's maximum moisture, so
 *     the ramp still spans the field.
 *
 * Returns a Float32Array of length 3 n, RGB in 0..1.
 * Throws an Error if the lengths differ.
 */
export function computeVertexColours(moisture: Float32Array, capacity?: Float64Array): Float32Array {
  if (capacity !== undefined && capacity.length !== moisture.length) {
    throw new Error(`capacity has ${capacity.length} cells but moisture has ${moisture.length}`);
  }
  let maxMoisture = 0;
  if (capacity === undefined) {
    for (let i = 0; i < moisture.length; i++) if (moisture[i] > maxMoisture) maxMoisture = moisture[i];
  }
  const colours = new Float32Array(moisture.length * 3);
  for (let i = 0; i < moisture.length; i++) {
    const denominator = capacity === undefined ? maxMoisture : capacity[i];
    const fraction = denominator > 0 ? moisture[i] / denominator : Number.NaN;
    const [r, g, b] = mapMoistureToColour(fraction);
    colours[i * 3] = r;
    colours[i * 3 + 1] = g;
    colours[i * 3 + 2] = b;
  }
  return colours;
}
