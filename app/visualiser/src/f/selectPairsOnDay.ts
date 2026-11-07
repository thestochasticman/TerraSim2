import type { RunPairs } from "@/t/RunPairs";

/**
 * The indices of the pairs observed on one of the run's days.
 *
 * pairs : RunPairs
 * t : dimensionless, a day index of the run
 *
 * Returns the indices in column order; empty when nothing was observed that day.
 */
export function selectPairsOnDay(pairs: RunPairs, t: number): number[] {
  const out: number[] = [];
  for (let i = 0; i < pairs.t.length; i++) if (pairs.t[i] === t) out.push(i);
  return out;
}
