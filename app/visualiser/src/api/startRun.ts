import type { RunRequest } from "@/t/RunRequest";

/**
 * POST /api/runs: start a run, or get back the id of the cached one.
 *
 * Returns the run id and whether the service reports it "running" or already "complete".
 */
export async function startRun(request: RunRequest): Promise<{ runId: string; status: "running" | "complete" }> {
  const response = await fetch("/api/runs", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      stub: request.stub,
      stress_exponent: request.stressExponent,
      initial_fullness: request.initialFullness,
      write_every_days: request.writeEveryDays,
      record_fluxes: request.recordFluxes,
    }),
  });
  if (!response.ok) throw new Error(`POST /api/runs failed with status ${response.status}`);
  const data = (await response.json()) as { run_id?: unknown; status?: unknown };
  if (typeof data.run_id !== "string" || (data.status !== "running" && data.status !== "complete")) {
    throw new Error("unexpected response from POST /api/runs");
  }
  return { runId: data.run_id, status: data.status };
}
