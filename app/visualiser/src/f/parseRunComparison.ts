import { parseScores } from "@/f/parseScores";
import type { RunComparison } from "@/t/RunComparison";

/**
 * Turn the service's comparison JSON into a RunComparison, validating every field.
 *
 * data : unknown
 *     The parsed body of GET /api/runs/{id}/comparison.
 *
 * Throws an Error naming the first invalid field.
 */
export function parseRunComparison(data: unknown): RunComparison {
  const obj = asObject(data, "run comparison");
  const daysWritten = readCount(obj, "days_written");
  const nPoints = readCount(obj, "n_points");
  const nPaired = readCount(obj, "n_paired");
  const rootDepth = obj["root_depth"] === null || obj["root_depth"] === undefined ? null : obj["root_depth"];
  if (rootDepth !== null && (typeof rootDepth !== "number" || !(rootDepth > 0))) throw new Error("root_depth must be a positive number or null");

  const layers = asArray(obj["layers"], "layers").map((item, i) => {
    const layer = asObject(item, `layers[${i}]`);
    const top = layer["top"];
    const bottom = layer["bottom"];
    if (typeof top !== "number" || typeof bottom !== "number" || !(top >= 0) || !(bottom > top)) throw new Error(`layers[${i}] must have 0 <= top < bottom`);
    return { top, bottom, n: readCount(layer, "n", `layers[${i}]`) };
  });
  const stations = asArray(obj["stations"], "stations");
  if (!stations.every((s) => typeof s === "string")) throw new Error("stations must be an array of strings");

  const byDate = asArray(obj["by_date"], "by_date").map((item, i) => {
    const row = asObject(item, `by_date[${i}]`);
    const date = row["date"];
    const t = row["t"];
    if (typeof date !== "string") throw new Error(`by_date[${i}]: date must be a string`);
    if (t !== null && (typeof t !== "number" || !Number.isInteger(t) || t < 0)) throw new Error(`by_date[${i}]: t must be a day index or null`);
    return { date, t: t as number | null, ...parseScores(row, `by_date[${i}]`) };
  });
  const byStation = asArray(obj["by_station"], "by_station").map((item, i) => {
    const row = asObject(item, `by_station[${i}]`);
    const station = row["station"];
    if (typeof station !== "number" || !Number.isInteger(station) || station < 0 || station >= stations.length) throw new Error(`by_station[${i}]: station must index the station names`);
    return { station, ...parseScores(row, `by_station[${i}]`) };
  });

  return { daysWritten, nPoints, nPaired, rootDepth, layers, stations: stations as string[], overall: parseScores(asObject(obj["overall"], "overall"), "overall"), byDate, byStation };
}

function asObject(value: unknown, name: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${name} must be a JSON object`);
  return value as Record<string, unknown>;
}

function asArray(value: unknown, name: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${name} must be an array`);
  return value;
}

function readCount(obj: Record<string, unknown>, key: string, where = ""): number {
  const value = obj[key];
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) throw new Error(`${where ? `${where}: ` : ""}${key} must be a non-negative integer`);
  return value;
}
