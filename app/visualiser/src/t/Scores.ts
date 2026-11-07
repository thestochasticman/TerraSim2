/**
 * How a set of modelled values matches observed ones, as the service scores them.
 *
 * n : dimensionless, pairs scored
 * observedMean, modelledMean, bias, rmse, ubrmse : m³/m³; bias is modelled minus observed; null when there are no pairs
 * r, nse, kge : dimensionless; null when the pairs have no spread to score
 */
export type Scores = {
  n: number;
  observedMean: number | null;
  modelledMean: number | null;
  bias: number | null;
  rmse: number | null;
  ubrmse: number | null;
  r: number | null;
  nse: number | null;
  kge: number | null;
};
