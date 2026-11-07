import { parseRunComparison } from "@/f/parseRunComparison";
import type { RunComparison } from "@/t/RunComparison";

/** GET /api/runs/{id}/comparison: the run scored against its site's observations, or null when the site has none (404). */
export async function fetchRunComparison(runId: string): Promise<RunComparison | null> {
  const response = await fetch(`/api/runs/${encodeURIComponent(runId)}/comparison`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`GET /api/runs/${runId}/comparison failed with status ${response.status}`);
  return parseRunComparison(await response.json());
}
