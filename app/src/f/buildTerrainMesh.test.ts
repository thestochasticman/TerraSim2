import { describe, expect, it } from "vitest";
import { buildTerrainMesh } from "./buildTerrainMesh";
import type { TerrainGrid } from "@/t/TerrainGrid";

function makeGrid(rows: number, cols: number, cellSize: number, elevation: number[]): TerrainGrid {
  return { rows, cols, cellSize, elevation: Float64Array.from(elevation) };
}

/** y component of the face normal of triangle (i, j, k), positive when wound CCW seen from +y. */
function normalY(positions: Float32Array, i: number, j: number, k: number): number {
  const ax = positions[i * 3], az = positions[i * 3 + 2];
  const bx = positions[j * 3], bz = positions[j * 3 + 2];
  const cx = positions[k * 3], cz = positions[k * 3 + 2];
  const ux = bx - ax, uz = bz - az;
  const vx = cx - ax, vz = cz - az;
  return uz * vx - ux * vz;
}

describe("buildTerrainMesh", () => {
  it("places one vertex per cell at (col * cellSize, elevation, row * cellSize)", () => {
    const mesh = buildTerrainMesh(makeGrid(2, 2, 10, [1, 2, 3, 4]));
    expect(mesh.positions).toBeInstanceOf(Float32Array);
    expect(Array.from(mesh.positions)).toEqual([
      0, 1, 0,
      10, 2, 0,
      0, 3, 10,
      10, 4, 10,
    ]);
  });

  it("triangulates a 2 x 2 grid into two triangles with the expected winding", () => {
    const mesh = buildTerrainMesh(makeGrid(2, 2, 10, [1, 2, 3, 4]));
    expect(mesh.indices).toBeInstanceOf(Uint32Array);
    expect(Array.from(mesh.indices)).toEqual([0, 2, 1, 1, 2, 3]);
  });

  it("produces the right array sizes for a rectangular grid", () => {
    const rows = 3, cols = 5;
    const mesh = buildTerrainMesh(makeGrid(rows, cols, 1, new Array(rows * cols).fill(0)));
    expect(mesh.positions.length).toBe(rows * cols * 3);
    expect(mesh.indices.length).toBe((rows - 1) * (cols - 1) * 6);
  });

  it("references only valid vertices and uses every vertex", () => {
    const rows = 4, cols = 3;
    const mesh = buildTerrainMesh(makeGrid(rows, cols, 2, new Array(rows * cols).fill(5)));
    const used = new Set<number>();
    for (const idx of mesh.indices) {
      expect(idx).toBeGreaterThanOrEqual(0);
      expect(idx).toBeLessThan(rows * cols);
      used.add(idx);
    }
    expect(used.size).toBe(rows * cols);
  });

  it("winds every triangle counter-clockwise seen from above, whatever the heights", () => {
    const heights = [0, 9, 1, 4, 7, 2, 8, 3, 6, 5, 0, 1];
    const mesh = buildTerrainMesh(makeGrid(3, 4, 1, heights));
    for (let t = 0; t < mesh.indices.length; t += 3) {
      expect(normalY(mesh.positions, mesh.indices[t], mesh.indices[t + 1], mesh.indices[t + 2])).toBeGreaterThan(0);
    }
  });

  it("rejects grids with fewer than two rows or columns", () => {
    expect(() => buildTerrainMesh(makeGrid(1, 3, 1, [0, 0, 0]))).toThrow("at least 2 x 2");
    expect(() => buildTerrainMesh(makeGrid(3, 1, 1, [0, 0, 0]))).toThrow("at least 2 x 2");
  });
});
