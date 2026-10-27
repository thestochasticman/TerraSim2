import { useEffect, useState } from "react";
import { parseTerrainGrid } from "@/f/parseTerrainGrid";
import type { TerrainGrid } from "@/t/TerrainGrid";

/**
 * What the hook reports while a terrain file is fetched and parsed.
 *
 * loading : true until the fetch settles, success or failure.
 * grid : the parsed TerrainGrid on success, otherwise null.
 * error : a message on failure, otherwise null.
 */
export type TerrainGridState = {
  loading: boolean;
  grid: TerrainGrid | null;
  error: string | null;
};

/**
 * Fetch a terrain JSON file and parse it into a TerrainGrid.
 *
 * Refetches whenever url changes. A response that arrives after the url
 * has changed, or after unmount, is discarded.
 *
 * url : string
 *     Where to fetch the terrain JSON from, relative or absolute.
 */
export function useTerrainGrid(url: string): TerrainGridState {
  const [result, setResult] = useState<{ url: string; grid: TerrainGrid | null; error: string | null } | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetch(url)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`fetch of ${url} failed with status ${response.status}`);
        }
        return parseTerrainGrid(await response.json());
      })
      .then((grid) => {
        if (!cancelled) setResult({ url, grid, error: null });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setResult({ url, grid: null, error: err instanceof Error ? err.message : String(err) });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [url]);

  if (result === null || result.url !== url) {
    return { loading: true, grid: null, error: null };
  }
  return { loading: false, grid: result.grid, error: result.error };
}
