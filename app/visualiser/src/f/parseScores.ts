import type { Scores } from "@/t/Scores";

const SCORE_FIELDS = { observed_mean: "observedMean", modelled_mean: "modelledMean", bias: "bias", rmse: "rmse", ubrmse: "ubrmse", r: "r", nse: "nse", kge: "kge" } as const;

/**
 * Read the service's score fields off an object into a Scores.
 *
 * obj : a JSON object carrying n and the snake_case score fields, each a finite number or null
 * where : names the object in error messages
 *
 * Returns the Scores. Throws an Error naming the first bad field.
 */
export function parseScores(obj: Record<string, unknown>, where: string): Scores {
  const n = obj["n"];
  if (typeof n !== "number" || !Number.isInteger(n) || n < 0) {
    throw new Error(`${where}: n must be a non-negative integer`);
  }
  const out: Scores = { n, observedMean: null, modelledMean: null, bias: null, rmse: null, ubrmse: null, r: null, nse: null, kge: null };
  for (const [key, name] of Object.entries(SCORE_FIELDS)) {
    const value = obj[key];
    if (value === null || value === undefined) continue;
    if (typeof value !== "number" || !Number.isFinite(value)) {
      throw new Error(`${where}: ${key} must be a finite number or null`);
    }
    out[name] = value;
  }
  return out;
}
