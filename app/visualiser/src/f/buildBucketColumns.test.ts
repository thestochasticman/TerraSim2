import { describe, expect, it } from "vitest";
import { BUCKET_DEPTH, BUCKET_WIDTH, buildBucketColumns } from "./buildBucketColumns";
import type { TerrainGrid } from "@/t/TerrainGrid";

// 2 rows x 4 cols of 10 m; the far right block has one cell without soil.
const grid: TerrainGrid = {
  rows: 2,
  cols: 4,
  cellSize: 10,
  elevation: Float64Array.from([100, 102, 104, 106, 110, 112, 114, 116]),
  capacity: Float64Array.from([40, 40, 80, 80, 40, 40, Number.NaN, 80]),
  freeCapacity: Float64Array.from([20, 20, 40, 40, 20, 20, Number.NaN, 40]),
};
const moisture = Float32Array.from([20, 60, 100, 140, 10, 10, 0, 80]);
const close = (values: Float32Array, expected: number[]) => expected.forEach((v, i) => expect(values[i]).toBeCloseTo(v, 5));

describe("buildBucketColumns", () => {
  it("averages each block's cells with soil, centres the column on the block and hangs it from the mean elevation", () => {
    const set = buildBucketColumns(grid, moisture, 2, true);
    expect(set?.count).toBe(2);
    expect(set?.block).toBe(2);
    expect(set?.size).toBe(BUCKET_WIDTH * 2 * 10);
    // block 0: all four cells; block 1: three cells, the NaN one left out
    close(set?.tops ?? new Float32Array(), [5, 106, 5, 25, (104 + 106 + 116) / 3, 5]);
  });

  it("scales depths so the fullest block stands BUCKET_DEPTH of the longer side tall, and fills the plant store before the free store", () => {
    const set = buildBucketColumns(grid, moisture, 2, true);
    const scale = (BUCKET_DEPTH * 30) / 120; // the longer side is 30 m; block 1 holds 80 + 40 mm
    close(set?.plantDepth ?? new Float32Array(), [40 * scale, 80 * scale]);
    close(set?.freeDepth ?? new Float32Array(), [20 * scale, 40 * scale]);
    // block 0 holds 25 mm of its 40: plant store 0.625 full, free store empty; block 1 holds 106.67 of 80 + 40
    close(set?.plantFill ?? new Float32Array(), [25 / 40, 1]);
    close(set?.freeFill ?? new Float32Array(), [0, (320 / 3 - 80) / 40]);
  });

  it("without a free store the columns are the plant store alone, scaled to the largest capacity, and the fill is capped at full", () => {
    const set = buildBucketColumns(grid, moisture, 2, false);
    const scale = (BUCKET_DEPTH * 30) / 80;
    close(set?.plantDepth ?? new Float32Array(), [40 * scale, 80 * scale]);
    close(set?.freeDepth ?? new Float32Array(), [0, 0]);
    close(set?.plantFill ?? new Float32Array(), [25 / 40, 1]);
    close(set?.freeFill ?? new Float32Array(), [0, 0]);
  });

  it("a block of one cell gives a column per cell with soil, and a non-finite moisture counts as empty", () => {
    const set = buildBucketColumns(grid, Float32Array.from([Number.NaN, 60, 100, 140, 10, 10, 0, 80]), 1, true);
    expect(set?.count).toBe(7);
    expect(set?.size).toBe(BUCKET_WIDTH * 10);
    close(set?.tops.slice(0, 6) ?? new Float32Array(), [0, 100, 0, 10, 102, 0]);
    expect(set?.plantFill[0]).toBe(0);
  });

  it("gives null without capacity, for a bad block, for moisture of another grid, or when nothing has capacity", () => {
    expect(buildBucketColumns({ ...grid, capacity: undefined }, moisture, 1, true)).toBeNull();
    expect(buildBucketColumns(grid, moisture, 0, true)).toBeNull();
    expect(buildBucketColumns(grid, moisture, 1.5, true)).toBeNull();
    expect(buildBucketColumns(grid, new Float32Array(3), 1, true)).toBeNull();
    expect(buildBucketColumns({ ...grid, capacity: new Float64Array(8) }, moisture, 1, false)).toBeNull();
  });
});
