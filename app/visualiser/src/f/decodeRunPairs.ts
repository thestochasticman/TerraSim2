import type { RunPairs } from "@/t/RunPairs";

const COLUMNS = ["t", "row", "col", "station", "observed", "modelled"] as const;

/**
 * Decode the pairs the service sends: six little-endian float32 columns, one after another.
 *
 * buffer : ArrayBuffer
 *     6 N values: t, row, col, station (dimensionless), observed, modelled (m³/m³).
 *
 * Returns a RunPairs whose columns each have length N.
 * Throws an Error if the byte length is not a multiple of six float32s.
 */
export function decodeRunPairs(buffer: ArrayBuffer): RunPairs {
  const stride = COLUMNS.length * 4;
  if (buffer.byteLength % stride !== 0) {
    throw new Error(`pairs have ${buffer.byteLength} bytes, not a multiple of ${stride}`);
  }
  const n = buffer.byteLength / stride;
  const view = new DataView(buffer);
  const out = {} as Record<(typeof COLUMNS)[number], Float32Array>;
  COLUMNS.forEach((name, k) => {
    const column = new Float32Array(n);
    for (let i = 0; i < n; i++) column[i] = view.getFloat32((k * n + i) * 4, true);
    out[name] = column;
  });
  return out;
}
