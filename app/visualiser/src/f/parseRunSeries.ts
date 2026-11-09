import type { RunSeries } from "@/t/RunSeries";

const REQUIRED = ["rain", "pet", "moisture"] as const;
/** Optional series: the key the service sends (the store's flux name) and the field it fills. */
const OPTIONAL: [string, "infiltration" | "runoff" | "evaporation" | "inflow" | "surfaceFlow" | "subsurfaceLateralFlow" | "percolation"][] = [
  ["infiltration", "infiltration"],
  ["runoff", "runoff"],
  ["evaporation", "evaporation"],
  ["inflow", "inflow"],
  ["surface_flow", "surfaceFlow"],
  ["subsurface_lateral_flow", "subsurfaceLateralFlow"],
  ["percolation", "percolation"],
];

/**
 * Turn the service's series JSON into a RunSeries, checking every list has one value per date.
 *
 * data : unknown
 *     The parsed body of GET /api/runs/{id}/series.
 *
 * Throws an Error naming the first invalid field.
 */
export function parseRunSeries(data: unknown): RunSeries {
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new Error("run series must be a JSON object");
  }
  const obj = data as Record<string, unknown>;
  const dates = obj["dates"];
  if (!Array.isArray(dates) || !dates.every((d) => typeof d === "string")) {
    throw new Error("dates must be an array of strings");
  }
  const n = dates.length;
  const out: RunSeries = { dates: dates as string[], rain: [], pet: [], moisture: [] };
  for (const key of REQUIRED) {
    out[key] = readNumbers(obj, key, n);
  }
  for (const [key, field] of OPTIONAL) {
    if (obj[key] !== undefined) out[field] = readNumbers(obj, key, n);
  }
  return out;
}

function readNumbers(obj: Record<string, unknown>, key: string, n: number): number[] {
  const values = obj[key];
  if (!Array.isArray(values) || values.length !== n) {
    throw new Error(`${key} must have one value per date (${n})`);
  }
  if (!values.every((v) => typeof v === "number" && Number.isFinite(v))) {
    throw new Error(`${key} must contain only finite numbers`);
  }
  return values as number[];
}
