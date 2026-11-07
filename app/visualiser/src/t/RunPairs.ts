/**
 * Every observation at a site with the run's value at it, as parallel columns of one length.
 *
 * t : the run's day index per observation, dimensionless; NaN when the date is outside the run or not yet written
 * row, col : the observation's cell, dimensionless
 * station : index into the comparison's station names, dimensionless
 * observed : the measured volumetric water content, m³/m³
 * modelled : the run's content at that cell on that day, m³/m³; NaN when unavailable
 */
export type RunPairs = {
  t: Float32Array;
  row: Float32Array;
  col: Float32Array;
  station: Float32Array;
  observed: Float32Array;
  modelled: Float32Array;
};
