import type { RunStatus } from "@/t/RunStatus";

const STATUSES = new Set(["missing", "running", "complete", "failed"]);

/**
 * Turn the service's status JSON into a RunStatus, validating the fields.
 *
 * The service omits the counts and dates while the run is "missing";
 * those come back as zeros and an empty list.
 *
 * data : unknown
 *     The parsed body of GET /api/runs/{id}.
 *
 * Throws an Error naming the first invalid field.
 */
export function parseRunStatus(data: unknown): RunStatus {
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new Error("run status must be a JSON object");
  }
  const obj = data as Record<string, unknown>;
  const runId = obj["run_id"];
  if (typeof runId !== "string" || runId.length === 0) {
    throw new Error("run_id must be a non-empty string");
  }
  const status = obj["status"];
  if (typeof status !== "string" || !STATUSES.has(status)) {
    throw new Error(`status must be one of ${[...STATUSES].join(", ")}`);
  }
  const dates = obj["dates"] ?? [];
  if (!Array.isArray(dates) || !dates.every((d) => typeof d === "string")) {
    throw new Error("dates must be an array of strings");
  }
  return {
    runId,
    status: status as RunStatus["status"],
    daysWritten: readCount(obj, "days_written"),
    nDays: readCount(obj, "n_days"),
    rows: readCount(obj, "rows"),
    cols: readCount(obj, "cols"),
    dates: dates as string[],
  };
}

function readCount(obj: Record<string, unknown>, key: string): number {
  const value = obj[key] ?? 0;
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) {
    throw new Error(`${key} must be a non-negative integer`);
  }
  return value;
}
