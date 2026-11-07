import { useEffect, useState } from "react";
import { fetchRunComparison } from "@/api/fetchRunComparison";
import { fetchRunPairs } from "@/api/fetchRunPairs";
import type { RunComparison } from "@/t/RunComparison";
import type { RunPairs } from "@/t/RunPairs";

type State = { runId: string | null; comparison: RunComparison | null; pairs: RunPairs | null; error: string | null };

/**
 * A run's comparison with its site's observations, refetched as days are written.
 *
 * runId : the run to follow, or null for none
 * daysWritten : dimensionless; a change triggers a refetch, so the scores
 *     and pairs grow with the run and are final once it completes
 *
 * Returns the latest comparison and pairs, both null before the first
 * response and for a site without observations, and an error message if
 * the last fetch failed. A response for a run that is no longer current is
 * dropped.
 */
export function useRunComparison(runId: string | null, daysWritten: number): { comparison: RunComparison | null; pairs: RunPairs | null; error: string | null } {
  const [state, setState] = useState<State>({ runId: null, comparison: null, pairs: null, error: null });

  useEffect(() => {
    if (runId === null || daysWritten === 0) return;
    let cancelled = false;
    Promise.all([fetchRunComparison(runId), fetchRunPairs(runId)])
      .then(([comparison, pairs]) => { if (!cancelled) setState({ runId, comparison, pairs, error: null }); })
      .catch((err: unknown) => {
        if (!cancelled) setState((prev) => ({ runId, comparison: prev.runId === runId ? prev.comparison : null, pairs: prev.runId === runId ? prev.pairs : null, error: err instanceof Error ? err.message : String(err) }));
      });
    return () => { cancelled = true; };
  }, [runId, daysWritten]);

  const current = state.runId === runId ? state : { comparison: null, pairs: null, error: null };
  return { comparison: current.comparison, pairs: current.pairs, error: current.error };
}
