import type { TerrainGrid } from "@/t/TerrainGrid";
import { readPositiveInteger } from "./readPositiveInteger";

/**
 * Turn parsed terrain JSON into a TerrainGrid, validating every field.
 *
 * Expected input shape, as written by the Python side:
 *
 *     { "rows": 2, "cols": 3, "cell_size": 10.0, "elevation": [[...], [...]] }
 *
 * data : unknown
 *     The result of JSON.parse on a terrain file.
 *
 * Returns a TerrainGrid with elevation flattened row-major.
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

  const elevationRows = obj["elevation"];
  if (!Array.isArray(elevationRows) || elevationRows.length !== rows) {
    throw new Error(`elevation must be an array of ${rows} rows`);
  }

  const elevation = new Float64Array(rows * cols);
  for (let r = 0; r < rows; r++) {
    const row = elevationRows[r];
    if (!Array.isArray(row) || row.length !== cols) {
      throw new Error(`elevation row ${r} must be an array of ${cols} values`);
    }
    for (let c = 0; c < cols; c++) {
      const value = row[c];
      if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new Error(`elevation[${r}][${c}] must be a finite number`);
      }
      elevation[r * cols + c] = value;
    }
  }

  return { rows, cols, cellSize, elevation };
}
