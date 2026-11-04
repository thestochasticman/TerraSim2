/**
 * What the visualiser sends to start a run. Mirrors app/api's RunRequest.
 *
 * stub : a site with prepared inputs, for example "tarrawarra"
 * step : which process runs: "bucket" for closed per-cell buckets, "routed" for buckets whose overflow runs downhill
 * stressExponent : dimensionless, positive
 * initialFullness : dimensionless, moisture at day zero as a fraction of capacity, 0 to 1
 * rootDepth : metres (m), how deep the roots reach; each cell's capacity is its soil's available water to this depth
 * writeEveryDays : dimensionless, days the run buffers before writing; 1 shows progress daily
 * recordFluxes : whether the run stores fluxes
 */
export type RunRequest = {
  stub: string;
  step: "bucket" | "routed";
  stressExponent: number;
  initialFullness: number;
  rootDepth: number;
  writeEveryDays: number;
  recordFluxes: boolean;
};
