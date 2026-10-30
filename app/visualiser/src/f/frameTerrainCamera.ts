import type { TerrainGrid } from "@/t/TerrainGrid";

/**
 * Where to put the camera so the whole terrain is in view.
 *
 * target : [x, y, z], metres (m)
 *     Point the camera looks at and orbits around: the grid centre at
 *     the mid elevation.
 * position : [x, y, z], metres (m)
 *     Initial camera position, above and in front of the target.
 * near, far : metres (m)
 *     Clipping planes sized to the terrain extent.
 */
export type CameraFrame = {
  target: [number, number, number];
  position: [number, number, number];
  near: number;
  far: number;
};

/**
 * Compute a camera frame that shows the whole terrain.
 *
 * The horizontal span is the longer of the grid width and depth. The camera
 * sits one span back along +z and 0.8 spans up from the target, which gives
 * a three-quarter view with the full extent on screen at a 50 degree field
 * of view.
 *
 * grid : TerrainGrid
 *     Elevation and cellSize in metres (m).
 *
 * Returns a CameraFrame in metres (m).
 */
export function frameTerrainCamera(grid: TerrainGrid): CameraFrame {
  const width = (grid.cols - 1) * grid.cellSize;
  const depth = (grid.rows - 1) * grid.cellSize;
  const span = Math.max(width, depth, grid.cellSize);

  let min = Infinity;
  let max = -Infinity;
  for (const z of grid.elevation) {
    if (z < min) min = z;
    if (z > max) max = z;
  }
  const midElevation = (min + max) / 2;

  const target: [number, number, number] = [width / 2, midElevation, depth / 2];
  const position: [number, number, number] = [target[0], target[1] + span * 0.8, target[2] + span];
  const relief = max - min;
  const far = (span + relief) * 10;

  return { target, position, near: span / 1000, far };
}
