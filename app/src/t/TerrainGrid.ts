/**
 * A regular raster of terrain cells, as the app holds it in memory.
 *
 * rows, cols : dimensionless
 *     Grid dimensions.
 * cellSize : metres (m)
 *     Edge length of one square cell.
 * elevation : Float64Array of length rows * cols, metres (m)
 *     Ground elevation above datum per cell, row-major: index = row * cols + col.
 */
export type TerrainGrid = {
  rows: number;
  cols: number;
  cellSize: number;
  elevation: Float64Array;
};
