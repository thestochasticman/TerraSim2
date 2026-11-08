import type { TerrainGrid } from "@/t/TerrainGrid";
import { readPositiveInteger } from "./readPositiveInteger";

/**
 * Turn parsed terrain JSON into a TerrainGrid, validating every field.
 *
 * Expected input shape, as written by the Python side:
 *
 *     { "rows": 2, "cols": 3, "cell_size": 10.0, "elevation": [[...], [...]], "capacity": [[...], [...]] }
 *
 * `capacity`, `free_capacity`, `upslope_cells` and `vegetation` are optional (null counts as absent); when present each must have
 * the same shape as elevation, and `vegetation` comes with `vegetation_classes`, the names its indices stand for.
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
  if (obj["free_capacity"] !== undefined && obj["free_capacity"] !== null) {
    grid.freeCapacity = readField(obj, "free_capacity", rows, cols);
  }
  if (obj["upslope_cells"] !== undefined) {
    grid.upslopeCells = readField(obj, "upslope_cells", rows, cols);
  }
  if (obj["vegetation"] !== undefined && obj["vegetation"] !== null) {
    const classes = obj["vegetation_classes"];
    if (!Array.isArray(classes) || classes.length === 0 || !classes.every((c) => typeof c === "string")) {
      throw new Error("vegetation_classes must name the vegetation indices");
    }
    grid.vegetation = readField(obj, "vegetation", rows, cols);
    for (const v of grid.vegetation) {
      if (!Number.isInteger(v) || v < -1 || v >= classes.length) throw new Error(`vegetation must index ${classes.length} classes or be -1`);
    }
    grid.vegetationClasses = classes as string[];
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
