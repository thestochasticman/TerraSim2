/**
 * What the visualiser sends to start a run. Mirrors app/api's RunRequest.
 *
 * stub : a site with prepared inputs, for example "tarrawarra"
 * stressExponent : dimensionless, positive
 * initialFullness : dimensionless, moisture at day zero as a fraction of capacity, 0 to 1
 * writeEveryDays : dimensionless, days the run buffers before writing; 1 shows progress daily
 * recordFluxes : whether the run stores fluxes
 */
export type RunRequest = {
  stub: string;
  stressExponent: number;
  initialFullness: number;
  writeEveryDays: number;
  recordFluxes: boolean;
};
