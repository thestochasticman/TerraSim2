/**
 * Soil columns to draw under the terrain surface, one per block of cells.
 *
 * Each column hangs from the surface at its block's mean elevation. Its drawn
 * height is proportional to the block's total capacity, the plant store at the
 * bottom and the free store above it, and each store is filled from its bottom
 * by that day's water.
 *
 * count : dimensionless
 * block : dimensionless, cells per side of a block
 * size : metres (m), the footprint edge of every column
 * tops : Float32Array of length 3 count, metres (m), x, y (up), z of each column's top centre in the mesh's frame
 * plantDepth : Float32Array of length count, metres (m), the drawn height of each column's plant store
 * freeDepth : Float32Array of length count, metres (m), the drawn height of each column's free store; 0 when the run has none
 * plantFill : Float32Array of length count, dimensionless in 0..1, how full each plant store is
 * freeFill : Float32Array of length count, dimensionless in 0..1, how full each free store is
 */
export type BucketSet = {
  count: number;
  block: number;
  size: number;
  tops: Float32Array;
  plantDepth: Float32Array;
  freeDepth: Float32Array;
  plantFill: Float32Array;
  freeFill: Float32Array;
};
