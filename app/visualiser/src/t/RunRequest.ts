/**
 * What the visualiser sends to start a run. Mirrors app/api's RunRequest.
 *
 * stub : a site with prepared inputs, for example "tarrawarra"
 * step : which process runs: "bucket" for closed per-cell buckets, "routed" for buckets whose overflow runs downhill,
 *     "subsurface" for buckets with a free store that drains downslope through the soil
 * percolationFraction : dimensionless, 0 to 1; the share of conductivity acting straight down out of the root zone, 0 for an impermeable base (subsurface only)
 * rainHours : hours the day's rain is taken to fall, setting the infiltration limit (subsurface only)
 * lateralMultiplier : dimensionless, positive; how many times the matrix conductivity water moves along the slope, 1 for the matrix value (subsurface only)
 * aspectStrength : dimensionless, non-negative; how much a cell's evaporative demand follows the sun its slope receives, 0 for none (subsurface only)
 * coverStrength : dimensionless, non-negative; how much a cell's demand follows its persistent cover relative to the site's mean where the site has a vegetation map, 0 for none (every step)
 * stressExponent : dimensionless, positive
 * initialFullness : dimensionless, moisture at day zero as a fraction of capacity, 0 to 1
 * rootDepth : metres (m), how deep the roots reach; each cell's capacity is its soil's available water to this depth
 * treeRootDepth : metres (m) or null; when the site has a vegetation map, tree cells reach this deep and rootDepth applies to the rest
 * writeEveryDays : dimensionless, days the run buffers before writing; 1 shows progress daily
 * recordFluxes : whether the run stores fluxes
 */
export type RunRequest = {
  stub: string;
  step: "bucket" | "routed" | "subsurface";
  percolationFraction: number;
  rainHours: number;
  lateralMultiplier: number;
  aspectStrength: number;
  coverStrength: number;
  stressExponent: number;
  initialFullness: number;
  rootDepth: number;
  treeRootDepth: number | null;
  writeEveryDays: number;
  recordFluxes: boolean;
};
