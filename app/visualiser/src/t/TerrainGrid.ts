/**
 * A regular raster of terrain cells, as the app holds it in memory.
 *
 * rows, cols : dimensionless
 *     Grid dimensions.
 * cellSize : metres (m)
 *     Edge length of one square cell.
 * elevation : Float64Array of length rows * cols, metres (m)
 *     Ground elevation above datum per cell, row-major: index = row * cols + col.
 * capacity : Float64Array of length rows * cols, millimetres (mm), optional
 *     Bucket capacity per cell, same layout. Present when the terrain came from
 *     prepared model inputs; absent for a bare terrain file.
 * freeCapacity : Float64Array of length rows * cols, millimetres (mm), optional
 *     Pore space above field capacity per cell at the run's root depth; present when the inputs carry a soil curve.
 * upslopeCells : Float64Array of length rows * cols, dimensionless, optional
 *     How many cells drain through each cell, itself included; absent for a bare terrain file.
 * vegetation : Float64Array of length rows * cols, dimensionless, optional
 *     The vegetation class index per cell, -1 where unknown; present when the site has a vegetation map.
 * vegetationClasses : the names the indices stand for, present with vegetation.
 */
export type TerrainGrid = {
  rows: number;
  cols: number;
  cellSize: number;
  elevation: Float64Array;
  capacity?: Float64Array;
  freeCapacity?: Float64Array;
  upslopeCells?: Float64Array;
  vegetation?: Float64Array;
  vegetationClasses?: string[];
};
