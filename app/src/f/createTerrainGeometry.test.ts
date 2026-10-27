import { describe, expect, it } from "vitest";
import { createTerrainGeometry } from "./createTerrainGeometry";
import type { TerrainGrid } from "@/t/TerrainGrid";

function makeGrid(rows: number, cols: number, cellSize: number, elevation: number[]): TerrainGrid {
  return { rows, cols, cellSize, elevation: Float64Array.from(elevation) };
}

describe("createTerrainGeometry", () => {
  it("has one position per cell and an index with two triangles per quad", () => {
    const geometry = createTerrainGeometry(makeGrid(3, 4, 2, new Array(12).fill(0)));
    const position = geometry.getAttribute("position");
    expect(position.count).toBe(12);
    expect(position.itemSize).toBe(3);
    expect(geometry.getIndex()?.count).toBe(2 * 3 * 6);
  });

  it("carries the vertex positions from buildTerrainMesh unchanged", () => {
    const geometry = createTerrainGeometry(makeGrid(2, 2, 10, [1, 2, 3, 4]));
    const position = geometry.getAttribute("position");
    expect(Array.from(position.array)).toEqual([0, 1, 0, 10, 2, 0, 0, 3, 10, 10, 4, 10]);
  });

  it("computes normals that point straight up on flat terrain", () => {
    const geometry = createTerrainGeometry(makeGrid(3, 3, 1, new Array(9).fill(7)));
    const normal = geometry.getAttribute("normal");
    expect(normal).toBeDefined();
    expect(normal.count).toBe(9);
    for (let i = 0; i < normal.count; i++) {
      expect(normal.getX(i)).toBeCloseTo(0);
      expect(normal.getY(i)).toBeCloseTo(1);
      expect(normal.getZ(i)).toBeCloseTo(0);
    }
  });

  it("computes normals that tilt against the slope on a ramp", () => {
    const geometry = createTerrainGeometry(makeGrid(2, 3, 1, [0, 1, 2, 0, 1, 2]));
    const normal = geometry.getAttribute("normal");
    for (let i = 0; i < normal.count; i++) {
      expect(normal.getX(i)).toBeLessThan(0);
      expect(normal.getY(i)).toBeGreaterThan(0);
      expect(normal.getZ(i)).toBeCloseTo(0);
    }
  });

  it("rejects grids that cannot be triangulated", () => {
    expect(() => createTerrainGeometry(makeGrid(1, 2, 1, [0, 0]))).toThrow("at least 2 x 2");
  });
});
