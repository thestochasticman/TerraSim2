import { parseRunSeries } from "@/f/parseRunSeries";
import type { RunSeries } from "@/t/RunSeries";

/** GET /api/runs/{id}/series: grid-mean daily series for the days written so far. */
export async function fetchRunSeries(runId: string): Promise<RunSeries> {
  const response = await fetch(`/api/runs/${encodeURIComponent(runId)}/series`);
  if (!response.ok) throw new Error(`GET /api/runs/${runId}/series failed with status ${response.status}`);
  return parseRunSeries(await response.json());
}
