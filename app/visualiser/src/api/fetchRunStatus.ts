import { parseRunStatus } from "@/f/parseRunStatus";
import type { RunStatus } from "@/t/RunStatus";

/** GET /api/runs/{id}: the run's current state. */
export async function fetchRunStatus(runId: string): Promise<RunStatus> {
  const response = await fetch(`/api/runs/${encodeURIComponent(runId)}`);
  if (!response.ok) throw new Error(`GET /api/runs/${runId} failed with status ${response.status}`);
  return parseRunStatus(await response.json());
}
