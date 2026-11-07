import { computeFiniteRange } from "@/f/computeFiniteRange";
import type { RunPairs } from "@/t/RunPairs";

/**
 * The scales the observation markers are coloured on, fixed over the whole run
 * so a marker's colour means the same on every day.
 *
 * pairs : RunPairs
 *
 * Returns observed, the {min, max} of the observed contents in m³/m³, or null
 * when there are none; and errorScale, the largest |modelled − observed| in
 * m³/m³ among the pairs the run has a value for, or null when it has none yet.
 */
export function computeComparisonRanges(pairs: RunPairs): { observed: { min: number; max: number } | null; errorScale: number | null } {
  let largest = 0;
  let any = false;
  for (let i = 0; i < pairs.observed.length; i++) {
    const error = pairs.modelled[i] - pairs.observed[i];
    if (!Number.isFinite(error)) continue;
    any = true;
    if (Math.abs(error) > largest) largest = Math.abs(error);
  }
  return { observed: computeFiniteRange(pairs.observed), errorScale: any && largest > 0 ? largest : null };
}
