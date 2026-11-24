import type { BucketSet } from "@/t/BucketSet";
import type { TerrainGrid } from "@/t/TerrainGrid";

/** The drawn height of the grid's fullest column, as a fraction of the terrain's longer side. */
export const BUCKET_DEPTH = 0.12;
/** A column's footprint edge as a fraction of its block's edge, so neighbours stand apart. */
export const BUCKET_WIDTH = 0.6;

/**
 * The soil columns for one day, one per block of cells.
 *
 * grid : TerrainGrid
 *     Needs capacity, millimetres (mm); reads freeCapacity, millimetres (mm), when withFreeStore.
 * moisture : Float32Array of length rows * cols, millimetres (mm)
 *     The day's water per cell; a non-finite value counts as 0.
 * block : dimensionless
 *     Cells per side of a block; blocks along the far edges may be smaller.
 * withFreeStore : whether the run holds water above field capacity (the subsurface step)
 *
 * A block's capacity, free capacity, moisture and elevation are the means over
 * its cells with a finite capacity; a block with none is left out. Depths are
 * scaled so the block with the largest total capacity stands BUCKET_DEPTH of
 * the terrain's longer side tall. Water fills the plant store first; what is
 * above the capacity fills the free store.
 *
 * Returns a BucketSet, or null when the grid has no capacity, block is not a
 * positive integer, moisture is not one value per cell, or no block has any
 * capacity to draw.
 */
export function buildBucketColumns(grid: TerrainGrid, moisture: Float32Array, block: number, withFreeStore: boolean): BucketSet | null {
  const { rows, cols, cellSize, elevation, capacity } = grid;
  if (!capacity || !Number.isInteger(block) || block < 1 || moisture.length !== rows * cols) return null;
  const freeCapacity = withFreeStore ? grid.freeCapacity : undefined;

  const tops: number[] = [];
  const caps: number[] = [];
  const frees: number[] = [];
  const waters: number[] = [];
  for (let r0 = 0; r0 < rows; r0 += block) {
    const r1 = Math.min(rows, r0 + block);
    for (let c0 = 0; c0 < cols; c0 += block) {
      const c1 = Math.min(cols, c0 + block);
      let n = 0;
      let cap = 0;
      let free = 0;
      let water = 0;
      let height = 0;
      for (let r = r0; r < r1; r++) {
        for (let c = c0; c < c1; c++) {
          const i = r * cols + c;
          if (!Number.isFinite(capacity[i])) continue;
          n++;
          cap += capacity[i];
          const f = freeCapacity?.[i];
          free += f !== undefined && Number.isFinite(f) ? f : 0;
          water += Number.isFinite(moisture[i]) ? moisture[i] : 0;
          height += elevation[i];
        }
      }
      if (n === 0) continue;
      tops.push(((c0 + c1 - 1) / 2) * cellSize, height / n, ((r0 + r1 - 1) / 2) * cellSize);
      caps.push(cap / n);
      frees.push(free / n);
      waters.push(water / n);
    }
  }

  const count = caps.length;
  let maxTotal = 0;
  for (let i = 0; i < count; i++) maxTotal = Math.max(maxTotal, caps[i] + frees[i]);
  if (!(maxTotal > 0)) return null;
  const span = Math.max((cols - 1) * cellSize, (rows - 1) * cellSize, cellSize);
  const scale = (BUCKET_DEPTH * span) / maxTotal;

  const plantDepth = new Float32Array(count);
  const freeDepth = new Float32Array(count);
  const plantFill = new Float32Array(count);
  const freeFill = new Float32Array(count);
  for (let i = 0; i < count; i++) {
    plantDepth[i] = caps[i] * scale;
    freeDepth[i] = frees[i] * scale;
    plantFill[i] = caps[i] > 0 ? Math.min(waters[i], caps[i]) / caps[i] : 0;
    freeFill[i] = frees[i] > 0 ? Math.min(Math.max(waters[i] - caps[i], 0), frees[i]) / frees[i] : 0;
  }
  return { count, block, size: BUCKET_WIDTH * block * cellSize, tops: Float32Array.from(tops), plantDepth, freeDepth, plantFill, freeFill };
}
