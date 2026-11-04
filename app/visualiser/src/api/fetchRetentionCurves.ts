import { parseRetentionCurves } from "@/f/parseRetentionCurves";
import type { RetentionCurves } from "@/t/RetentionCurves";

/** GET /api/soils/retention: the book's retention curves and available water for every texture. */
export async function fetchRetentionCurves(): Promise<RetentionCurves> {
  const response = await fetch("/api/soils/retention");
  if (!response.ok) throw new Error(`GET /api/soils/retention failed with status ${response.status}`);
  return parseRetentionCurves(await response.json());
}
