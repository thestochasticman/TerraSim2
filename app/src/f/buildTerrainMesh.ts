import type { TerrainGrid } from "@/t/TerrainGrid";
import type { TerrainMesh } from "@/t/TerrainMesh";

/**
 * Build a triangulated surface from a TerrainGrid.
 *
 * Each cell becomes one vertex at (col * cellSize, elevation, row * cellSize).
 * Each 2 x 2 block of cells becomes two triangles. The grid must be at least
 * 2 x 2, since a single row or column has no area to triangulate.
 *
 * grid : TerrainGrid
 *     Elevation in metres (m), cellSize in metres (m).
 *
 * Returns a TerrainMesh in metres (m).
 * Throws an Error if rows or cols is less than 2.
 */
export function buildTerrainMesh(grid: TerrainGrid): TerrainMesh {
  const { rows, cols, cellSize, elevation } = grid;
  if (rows < 2 || cols < 2) {
    throw new Error(`grid must be at least 2 x 2 to build a mesh, got ${rows} x ${cols}`);
  }

  const positions = new Float32Array(rows * cols * 3);
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      positions[i * 3] = c * cellSize;
      positions[i * 3 + 1] = elevation[i];
      positions[i * 3 + 2] = r * cellSize;
    }
  }

  const indices = new Uint32Array((rows - 1) * (cols - 1) * 6);
  let k = 0;
  for (let r = 0; r < rows - 1; r++) {
    for (let c = 0; c < cols - 1; c++) {
      const a = r * cols + c;
      const b = a + 1;
      const d = a + cols;
      const e = d + 1;
      indices[k++] = a;
      indices[k++] = d;
      indices[k++] = b;
      indices[k++] = b;
      indices[k++] = d;
      indices[k++] = e;
    }
  }

  return { positions, indices };
}
