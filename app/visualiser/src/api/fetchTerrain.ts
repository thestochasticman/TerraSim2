import { parseTerrainGrid } from "@/f/parseTerrainGrid";
import type { TerrainGrid } from "@/t/TerrainGrid";

/** GET /api/runs/{id}/terrain: elevation and capacity of the run's site. */
export async function fetchTerrain(runId: string): Promise<TerrainGrid> {
  const response = await fetch(`/api/runs/${encodeURIComponent(runId)}/terrain`);
  if (!response.ok) throw new Error(`GET /api/runs/${runId}/terrain failed with status ${response.status}`);
  return parseTerrainGrid(await response.json());
}
