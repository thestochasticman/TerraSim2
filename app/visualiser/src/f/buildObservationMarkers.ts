import { mapErrorToColour } from "@/f/mapErrorToColour";
import { mapMoistureToColour } from "@/f/mapMoistureToColour";
import { selectPairsOnDay } from "@/f/selectPairsOnDay";
import type { MarkerMode } from "@/t/MarkerMode";
import type { MarkerSet } from "@/t/MarkerSet";
import type { RunPairs } from "@/t/RunPairs";
import type { TerrainGrid } from "@/t/TerrainGrid";

/** How far above the surface a marker's centre sits, in cell sizes, so it is not buried in the mesh. */
export const MARKER_LIFT = 0.6;
/** A marker's radius in cell sizes. */
export const MARKER_RADIUS = 0.45;

/**
 * The markers for one day's observations, placed on the terrain and coloured by mode.
 *
 * grid : TerrainGrid
 *     Gives each marker's x, z from its cell and y from the cell's elevation, metres (m).
 * pairs : RunPairs
 * t : dimensionless, the day shown
 * mode : MarkerMode
 *     "observed" colours each marker by its observed content on the sequential ramp over
 *     `ranges.observed`; "error" by modelled minus observed on the diverging ramp over
 *     ±`ranges.errorScale`, grey where the run has no value yet.
 * ranges : the scales from computeComparisonRanges
 *
 * Returns a MarkerSet, or null when the mode is "none", nothing was observed that
 * day, or the scale the mode needs is not known.
 */
export function buildObservationMarkers(grid: TerrainGrid, pairs: RunPairs, t: number, mode: MarkerMode, ranges: { observed: { min: number; max: number } | null; errorScale: number | null }): MarkerSet | null {
  if (mode === "none") return null;
  const indices = selectPairsOnDay(pairs, t);
  if (indices.length === 0) return null;
  if (mode === "observed" && ranges.observed === null) return null;
  if (mode === "error" && ranges.errorScale === null) return null;

  const positions = new Float32Array(indices.length * 3);
  const colours = new Float32Array(indices.length * 3);
  indices.forEach((i, k) => {
    const row = pairs.row[i];
    const col = pairs.col[i];
    positions[k * 3] = col * grid.cellSize;
    positions[k * 3 + 1] = grid.elevation[row * grid.cols + col] + MARKER_LIFT * grid.cellSize;
    positions[k * 3 + 2] = row * grid.cellSize;
    let colour: [number, number, number];
    if (mode === "observed") {
      const { min, max } = ranges.observed as { min: number; max: number };
      colour = mapMoistureToColour(max > min ? (pairs.observed[i] - min) / (max - min) : 1);
    } else {
      colour = mapErrorToColour(pairs.modelled[i] - pairs.observed[i], ranges.errorScale as number);
    }
    colours[k * 3] = colour[0];
    colours[k * 3 + 1] = colour[1];
    colours[k * 3 + 2] = colour[2];
  });
  return { count: indices.length, positions, colours, radius: MARKER_RADIUS * grid.cellSize };
}
