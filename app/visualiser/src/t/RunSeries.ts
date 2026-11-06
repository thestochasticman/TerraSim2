/**
 * Grid-mean daily series for the days a run has written. All values in millimetres (mm).
 *
 * dates : ISO date strings, one per written day
 * rain, pet, moisture : one value per date
 * infiltration, runoff, evaporation : one value per date, absent when the run did not record fluxes
 * inflow : one value per date, water that arrived from upslope; routed and subsurface runs
 * drainage, leak : one value per date, free water that left downslope through the soil, or straight down; subsurface runs
 */
export type RunSeries = {
  dates: string[];
  rain: number[];
  pet: number[];
  moisture: number[];
  infiltration?: number[];
  runoff?: number[];
  evaporation?: number[];
  inflow?: number[];
  drainage?: number[];
  leak?: number[];
};
