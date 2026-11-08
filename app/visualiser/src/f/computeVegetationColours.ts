import { NO_DATA_COLOUR } from "@/f/mapMoistureToColour";

/**
 * One colour per vegetation class, by class index, from the reference palette's categorical
 * slots: yellow for grass (what comes and goes), green for trees (what stays). CSS hex for
 * legends; the RGB form is derived below.
 */
export const VEGETATION_COLOURS: string[] = ["#eda100", "#008300"];

function hex(h: string): [number, number, number] {
  return [parseInt(h.slice(1, 3), 16) / 255, parseInt(h.slice(3, 5), 16) / 255, parseInt(h.slice(5, 7), 16) / 255];
}

const RGB = VEGETATION_COLOURS.map(hex);

/**
 * Per-vertex colours for a terrain mesh from its cells' vegetation class.
 *
 * vegetation : Float64Array of length n, dimensionless
 *     The class index per cell; -1 or any index without a colour takes the no-data grey.
 *
 * Returns a Float32Array of length 3 n, RGB in 0..1.
 */
export function computeVegetationColours(vegetation: Float64Array): Float32Array {
  const colours = new Float32Array(vegetation.length * 3);
  for (let i = 0; i < vegetation.length; i++) {
    const [r, g, b] = RGB[vegetation[i]] ?? NO_DATA_COLOUR;
    colours[i * 3] = r;
    colours[i * 3 + 1] = g;
    colours[i * 3 + 2] = b;
  }
  return colours;
}
