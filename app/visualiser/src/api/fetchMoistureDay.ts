import { decodeMoistureDay } from "@/f/decodeMoistureDay";

/**
 * GET /api/runs/{id}/moisture/{t}: one day's moisture field, mm per cell.
 *
 * The service answers 409 for a day not yet written; that surfaces as an Error.
 */
export async function fetchMoistureDay(runId: string, t: number, rows: number, cols: number): Promise<Float32Array> {
  const response = await fetch(`/api/runs/${encodeURIComponent(runId)}/moisture/${t}`);
  if (!response.ok) throw new Error(`GET moisture day ${t} failed with status ${response.status}`);
  return decodeMoistureDay(await response.arrayBuffer(), rows, cols);
}
