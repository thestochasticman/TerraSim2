import type { TerrainGrid } from "@/t/TerrainGrid";
import { readPositiveInteger } from "./readPositiveInteger";

/**
 * Turn parsed terrain JSON into a TerrainGrid, validating every field.
 *
 * Expected input shape, as written by the Python side:
 *
 *     { "rows": 2, "cols": 3, "cell_size": 10.0, "elevation": [[...], [...]], "capacity": [[...], [...]] }
 *
 * `capacity` is optional; when present it must have the same shape as elevation.
 *
 * data : unknown
 *     The result of JSON.parse on a terrain file or the service's terrain response.
 *
 * Returns a TerrainGrid with the arrays flattened row-major.
 * Throws an Error naming the first field that is missing or invalid.
 */
export function parseTerrainGrid(data: unknown): TerrainGrid {
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new Error("terrain data must be a JSON object");
  }
  const obj = data as Record<string, unknown>;

  const rows = readPositiveInteger(obj, "rows");
  const cols = readPositiveInteger(obj, "cols");

  const cellSize = obj["cell_size"];
  if (typeof cellSize !== "number" || !Number.isFinite(cellSize) || cellSize <= 0) {
    throw new Error("cell_size must be a positive finite number");
  }

  const elevation = readField(obj, "elevation", rows, cols);
  const grid: TerrainGrid = { rows, cols, cellSize, elevation };
  if (obj["capacity"] !== undefined) {
    grid.capacity = readField(obj, "capacity", rows, cols);
  }
  return grid;
}

function readField(obj: Record<string, unknown>, name: string, rows: number, cols: number): Float64Array {
  const rowsIn = obj[name];
  if (!Array.isArray(rowsIn) || rowsIn.length !== rows) {
    throw new Error(`${name} must be an array of ${rows} rows`);
  }
  const out = new Float64Array(rows * cols);
  for (let r = 0; r < rows; r++) {
    const row = rowsIn[r];
    if (!Array.isArray(row) || row.length !== cols) {
      throw new Error(`${name} row ${r} must be an array of ${cols} values`);
    }
    for (let c = 0; c < cols; c++) {
      const value = row[c];
      if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new Error(`${name}[${r}][${c}] must be a finite number`);
      }
      out[r * cols + c] = value;
    }
  }
  return out;
}
