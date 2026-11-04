import { useEffect, useState } from "react";
import { fetchSoilColumn } from "@/api/fetchSoilColumn";
import type { CurveModel } from "@/t/CurveModel";
import type { SoilColumn } from "@/t/SoilColumn";

export type SoilColumnState = {
  data: SoilColumn | null;
  error: string | null;
};

/**
 * The available water of a column, refetched whenever its textures, root
 * depth or model change. The last column stays on show until the next
 * arrives; a response for inputs that are no longer current is dropped.
 */
export function useSoilColumn(textures: string[], rootDepth: number, model: CurveModel): SoilColumnState {
  const [state, setState] = useState<SoilColumnState>({ data: null, error: null });
  const key = textures.join(",");

  useEffect(() => {
    let cancelled = false;
    fetchSoilColumn(key.split(","), rootDepth, model)
      .then((data) => { if (!cancelled) setState({ data, error: null }); })
      .catch((err: unknown) => { if (!cancelled) setState((prev) => ({ data: prev.data, error: err instanceof Error ? err.message : String(err) })); });
    return () => { cancelled = true; };
  }, [key, rootDepth, model]);

  return state;
}
