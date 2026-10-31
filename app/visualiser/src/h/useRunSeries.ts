import { useEffect, useState } from "react";
import { fetchRunSeries } from "@/api/fetchRunSeries";
import type { RunSeries } from "@/t/RunSeries";

/**
 * The grid-mean daily series of a run, refetched as days are written.
 *
 * runId : the run to follow, or null for none
 * daysWritten : dimensionless; a change triggers a refetch, so the series
 *     grows with the run and is final once the run completes
 *
 * Returns the latest series, or null before the first response, and an
 * error message if the last fetch failed. A response for a run that is no
 * longer current is dropped.
 */
export function useRunSeries(runId: string | null, daysWritten: number): { series: RunSeries | null; error: string | null } {
  const [state, setState] = useState<{ runId: string | null; series: RunSeries | null; error: string | null }>({ runId: null, series: null, error: null });

  useEffect(() => {
    if (runId === null || daysWritten === 0) return;
    let cancelled = false;
    fetchRunSeries(runId)
      .then((series) => { if (!cancelled) setState({ runId, series, error: null }); })
      .catch((err: unknown) => { if (!cancelled) setState((prev) => ({ runId, series: prev.runId === runId ? prev.series : null, error: err instanceof Error ? err.message : String(err) })); });
    return () => { cancelled = true; };
  }, [runId, daysWritten]);

  const current = state.runId === runId ? state : { series: null, error: null };
  return { series: current.series, error: current.error };
}
