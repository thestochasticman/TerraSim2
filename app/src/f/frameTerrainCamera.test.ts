import { describe, expect, it } from "vitest";
import { frameTerrainCamera } from "./frameTerrainCamera";
import type { TerrainGrid } from "@/t/TerrainGrid";

function makeGrid(rows: number, cols: number, cellSize: number, elevation: number[]): TerrainGrid {
  return { rows, cols, cellSize, elevation: Float64Array.from(elevation) };
}

describe("frameTerrainCamera", () => {
  it("targets the grid centre at the mid elevation", () => {
    const frame = frameTerrainCamera(makeGrid(3, 5, 10, [100, 100, 100, 100, 100, 100, 100, 300, 100, 100, 100, 100, 100, 100, 100]));
    expect(frame.target).toEqual([20, 200, 10]);
  });

  it("places the camera one span back and 0.8 spans up from the target", () => {
    const frame = frameTerrainCamera(makeGrid(3, 5, 10, new Array(15).fill(0)));
    expect(frame.target).toEqual([20, 0, 10]);
    expect(frame.position).toEqual([20, 32, 50]);
  });

  it("uses the longer side as the span", () => {
    const wide = frameTerrainCamera(makeGrid(2, 11, 1, new Array(22).fill(0)));
    const deep = frameTerrainCamera(makeGrid(11, 2, 1, new Array(22).fill(0)));
    expect(wide.position[2] - wide.target[2]).toBe(10);
    expect(deep.position[2] - deep.target[2]).toBe(10);
  });

  it("sizes the clipping planes to the extent and keeps near well below it", () => {
    const frame = frameTerrainCamera(makeGrid(2, 2, 100, [0, 0, 0, 50]));
    expect(frame.near).toBeGreaterThan(0);
    expect(frame.near).toBeLessThan(1);
    expect(frame.far).toBe(1500);
  });
});
