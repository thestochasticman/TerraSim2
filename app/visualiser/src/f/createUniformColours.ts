/**
 * One colour repeated for every vertex of a mesh.
 *
 * count : dimensionless, number of vertices
 * rgb : the colour, components in 0..1
 *
 * Returns a Float32Array of length 3 count, the layout a colour attribute takes.
 */
export function createUniformColours(count: number, rgb: [number, number, number]): Float32Array {
  const out = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    out[i * 3] = rgb[0];
    out[i * 3 + 1] = rgb[1];
    out[i * 3 + 2] = rgb[2];
  }
  return out;
}
