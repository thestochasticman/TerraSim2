import { decodeRunPairs } from "@/f/decodeRunPairs";
import type { RunPairs } from "@/t/RunPairs";

/** GET /api/runs/{id}/pairs: every observation with the run's value at it, or null when the site has none (404). */
export async function fetchRunPairs(runId: string): Promise<RunPairs | null> {
  const response = await fetch(`/api/runs/${encodeURIComponent(runId)}/pairs`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`GET /api/runs/${runId}/pairs failed with status ${response.status}`);
  return decodeRunPairs(await response.arrayBuffer());
}
