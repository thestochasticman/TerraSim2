/**
 * Grid-mean daily series for the days a run has written. All values in millimetres (mm).
 *
 * dates : ISO date strings, one per written day
 * rain, pet, moisture : one value per date
 * infiltration, runoff, evaporation : one value per date, absent when the run did not record fluxes
 */
export type RunSeries = {
  dates: string[];
  rain: number[];
  pet: number[];
  moisture: number[];
  infiltration?: number[];
  runoff?: number[];
  evaporation?: number[];
};
