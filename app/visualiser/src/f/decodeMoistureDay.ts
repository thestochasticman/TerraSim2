/**
 * Decode one day's moisture field from the bytes the service sends.
 *
 * buffer : ArrayBuffer
 *     rows * cols little-endian float32 values, row-major, millimetres (mm).
 * rows, cols : dimensionless
 *     The grid shape the bytes must match.
 *
 * Returns a Float32Array of length rows * cols, index = row * cols + col, mm.
 * Throws an Error if the byte length is wrong.
 */
export function decodeMoistureDay(buffer: ArrayBuffer, rows: number, cols: number): Float32Array {
  const expected = rows * cols * 4;
  if (buffer.byteLength !== expected) {
    throw new Error(`moisture day has ${buffer.byteLength} bytes, expected ${expected} for ${rows} x ${cols}`);
  }
  const view = new DataView(buffer);
  const out = new Float32Array(rows * cols);
  for (let i = 0; i < out.length; i++) {
    out[i] = view.getFloat32(i * 4, true);
  }
  return out;
}
