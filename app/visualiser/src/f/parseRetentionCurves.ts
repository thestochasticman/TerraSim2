import { CURVE_MODELS } from "@/t/CurveModel";
import type { CurveModel } from "@/t/CurveModel";
import type { RetentionCurves } from "@/t/RetentionCurves";
import type { TextureCurve } from "@/t/TextureCurve";

/**
 * Turn the service's retention JSON into a RetentionCurves, checking shapes and order.
 *
 * data : unknown
 *     The parsed body of GET /api/soils/retention.
 *
 * Throws an Error naming the first invalid field. Both models must list the
 * same textures in the same order, each with one content per suction.
 */
export function parseRetentionCurves(data: unknown): RetentionCurves {
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new Error("retention curves must be a JSON object");
  }
  const obj = data as Record<string, unknown>;
  const suction = obj["suction"];
  if (!Array.isArray(suction) || suction.length < 2 || !suction.every((v) => typeof v === "number" && v > 0)) {
    throw new Error("suction must be an array of at least two positive numbers");
  }
  if (!suction.every((v, i) => i === 0 || v > suction[i - 1])) {
    throw new Error("suction must be ascending");
  }
  const fieldCapacity = readPositive(obj, "field_capacity");
  const wiltingPoint = readPositive(obj, "wilting_point");
  const modelsRaw = obj["models"];
  if (typeof modelsRaw !== "object" || modelsRaw === null) {
    throw new Error("models must be an object");
  }
  const models = {} as Record<CurveModel, TextureCurve[]>;
  for (const model of CURVE_MODELS) {
    models[model] = readModel((modelsRaw as Record<string, unknown>)[model], model, suction.length);
  }
  const names = models.campbell.map((c) => c.texture);
  if (names.join("|") !== models.van_genuchten.map((c) => c.texture).join("|")) {
    throw new Error("models must list the same textures in the same order");
  }
  return { suction: suction as number[], fieldCapacity, wiltingPoint, models };
}

function readPositive(obj: Record<string, unknown>, key: string): number {
  const v = obj[key];
  if (typeof v !== "number" || !(v > 0)) throw new Error(`${key} must be a positive number`);
  return v;
}

function readModel(raw: unknown, model: string, n: number): TextureCurve[] {
  if (!Array.isArray(raw) || raw.length === 0) throw new Error(`models.${model} must be a non-empty array`);
  return raw.map((record: unknown, i) => {
    if (typeof record !== "object" || record === null) throw new Error(`models.${model}[${i}] must be an object`);
    const r = record as Record<string, unknown>;
    const texture = r["texture"];
    if (typeof texture !== "string" || texture === "") throw new Error(`models.${model}[${i}].texture must be a string`);
    const theta = r["theta"];
    if (!Array.isArray(theta) || theta.length !== n || !theta.every((v) => typeof v === "number" && Number.isFinite(v))) {
      throw new Error(`models.${model}[${i}].theta must have one finite number per suction (${n})`);
    }
    const read = (key: string): number => {
      const v = r[key];
      if (typeof v !== "number" || !Number.isFinite(v)) throw new Error(`models.${model}[${i}].${key} must be a finite number`);
      return v;
    };
    return { texture, theta: theta as number[], thetaFc: read("theta_fc"), thetaPwp: read("theta_pwp"), availableWater: read("available_water") };
  });
}
