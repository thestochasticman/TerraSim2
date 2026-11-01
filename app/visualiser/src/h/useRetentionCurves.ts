import { useEffect, useState } from "react";
import { fetchRetentionCurves } from "@/api/fetchRetentionCurves";
import type { RetentionCurves } from "@/t/RetentionCurves";

export type RetentionCurvesState = {
  loading: boolean;
  data: RetentionCurves | null;
  error: string | null;
};

/** Fetch the book's retention curves once, on mount. */
export function useRetentionCurves(): RetentionCurvesState {
  const [state, setState] = useState<RetentionCurvesState>({ loading: true, data: null, error: null });

  useEffect(() => {
    let cancelled = false;
    fetchRetentionCurves()
      .then((data) => { if (!cancelled) setState({ loading: false, data, error: null }); })
      .catch((err: unknown) => { if (!cancelled) setState({ loading: false, data: null, error: err instanceof Error ? err.message : String(err) }); });
    return () => { cancelled = true; };
  }, []);

  return state;
}
