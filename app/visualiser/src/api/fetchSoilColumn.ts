import { parseSoilColumn } from "@/f/parseSoilColumn";
import type { CurveModel } from "@/t/CurveModel";
import type { SoilColumn } from "@/t/SoilColumn";

/**
 * GET /api/soils/column: one layered column's available water.
 *
 * textures : one class per layer, top first
 * rootDepth : m
 * model : whose table gives each layer's curve
 */
export async function fetchSoilColumn(textures: string[], rootDepth: number, model: CurveModel): Promise<SoilColumn> {
  const query = new URLSearchParams({ textures: textures.join(","), root_depth: String(rootDepth), model });
  const response = await fetch(`/api/soils/column?${query.toString()}`);
  if (!response.ok) throw new Error(`GET /api/soils/column failed with status ${response.status}`);
  return parseSoilColumn(await response.json());
}
