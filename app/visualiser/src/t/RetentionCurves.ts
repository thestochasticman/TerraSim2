import type { CurveModel } from "@/t/CurveModel";
import type { TextureCurve } from "@/t/TextureCurve";

/**
 * The book's retention curves for every texture, as GET /api/soils/retention returns them.
 *
 * suction : J/kg, ascending; the absolute value of matric potential
 * fieldCapacity, wiltingPoint : suctions J/kg at which the two reference contents are read
 * models : one list per model, textures coarsest first, in the same order under both models
 */
export type RetentionCurves = {
  suction: number[];
  fieldCapacity: number;
  wiltingPoint: number;
  models: Record<CurveModel, TextureCurve[]>;
};
