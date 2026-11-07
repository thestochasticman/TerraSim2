import { describe, expect, it } from "vitest";
import { MARKER_LIFT, MARKER_RADIUS, buildObservationMarkers } from "./buildObservationMarkers";
import { mapErrorToColour } from "./mapErrorToColour";
import { mapMoistureToColour, NO_DATA_COLOUR } from "./mapMoistureToColour";
import type { RunPairs } from "@/t/RunPairs";
import type { TerrainGrid } from "@/t/TerrainGrid";

const grid: TerrainGrid = { rows: 2, cols: 3, cellSize: 10, elevation: Float64Array.from([100, 101, 102, 103, 104, 105]) };
const pairs: RunPairs = {
  t: Float32Array.from([4, 4, 9, 4]),
  row: Float32Array.from([0, 1, 1, 0]),
  col: Float32Array.from([2, 0, 1, 0]),
  station: Float32Array.from([0, 1, 2, 3]),
  observed: Float32Array.from([0.2, 0.4, 0.3, 0.3]),
  modelled: Float32Array.from([0.3, 0.3, 0.3, Number.NaN]),
};
const ranges = { observed: { min: 0.2, max: 0.4 }, errorScale: 0.1 };

describe("buildObservationMarkers", () => {
  it("places that day's markers at their cells, lifted above the elevation, sized by the cell", () => {
    const m = buildObservationMarkers(grid, pairs, 4, "observed", ranges);
    expect(m?.count).toBe(3);
    expect(Array.from(m?.positions.slice(0, 3) ?? [])).toEqual([20, 102 + MARKER_LIFT * 10, 0]);
    expect(Array.from(m?.positions.slice(3, 6) ?? [])).toEqual([0, 103 + MARKER_LIFT * 10, 10]);
    expect(m?.radius).toBe(MARKER_RADIUS * 10);
  });

  it("colours by observed content over the whole run's range, or by error on the diverging ramp with grey where the run has nothing", () => {
    const stored = (colour: [number, number, number]) => colour.map(Math.fround);
    const observed = buildObservationMarkers(grid, pairs, 4, "observed", ranges);
    expect(Array.from(observed?.colours.slice(0, 3) ?? [])).toEqual(stored(mapMoistureToColour(0)));
    expect(Array.from(observed?.colours.slice(3, 6) ?? [])).toEqual(stored(mapMoistureToColour(1)));
    const error = buildObservationMarkers(grid, pairs, 4, "error", ranges);
    expect(Array.from(error?.colours.slice(0, 3) ?? [])).toEqual(stored(mapErrorToColour(pairs.modelled[0] - pairs.observed[0], 0.1)));
    expect(Array.from(error?.colours.slice(6, 9) ?? [])).toEqual(stored(NO_DATA_COLOUR));
  });

  it("gives null for the none mode, a day without observations, or a scale not yet known", () => {
    expect(buildObservationMarkers(grid, pairs, 4, "none", ranges)).toBeNull();
    expect(buildObservationMarkers(grid, pairs, 5, "observed", ranges)).toBeNull();
    expect(buildObservationMarkers(grid, pairs, 4, "error", { observed: ranges.observed, errorScale: null })).toBeNull();
    expect(buildObservationMarkers(grid, pairs, 4, "observed", { observed: null, errorScale: 0.1 })).toBeNull();
  });
});
