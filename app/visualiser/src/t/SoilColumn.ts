import type { CurveModel } from "@/t/CurveModel";

/**
 * One layered soil column's available water, as GET /api/soils/column returns it.
 *
 * textures : the twelve classes in ramp order, for colouring
 * layerBounds : m, ascending from 0; layer i spans layerBounds[i] to layerBounds[i + 1]
 * rootDepth : m
 * model : whose table gave each layer's curve
 * layers : top and bottom in m, the texture, the available fraction in m³/m³,
 *     the thickness within the roots in m, and the mm of water that gives
 * total : mm, the sum over layers
 */
export type SoilColumn = {
  textures: string[];
  layerBounds: number[];
  rootDepth: number;
  model: CurveModel;
  layers: { top: number; bottom: number; texture: string; fraction: number; thicknessInRoots: number; mm: number }[];
  total: number;
};
