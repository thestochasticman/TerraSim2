/**
 * The state of a run as the service reports it.
 *
 * runId : the service's id for this run
 * status : "missing" before the worker has created the store, "running" while it
 *          writes, "complete" when done, "failed" if the worker died
 * daysWritten : dimensionless, leading days safe to read; 0 while missing
 * nDays : dimensionless, total days in the run; 0 while missing
 * rows, cols : dimensionless, grid shape; 0 while missing
 * dates : ISO date strings, one per day; empty while missing
 */
export type RunStatus = {
  runId: string;
  status: "missing" | "running" | "complete" | "failed";
  daysWritten: number;
  nDays: number;
  rows: number;
  cols: number;
  dates: string[];
};
