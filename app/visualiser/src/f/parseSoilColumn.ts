import { CURVE_MODELS } from "@/t/CurveModel";
import type { CurveModel } from "@/t/CurveModel";
import type { SoilColumn } from "@/t/SoilColumn";

/**
 * Turn the service's column JSON into a SoilColumn, checking the layers match the bounds.
 *
 * data : unknown
 *     The parsed body of GET /api/soils/column.
 *
 * Throws an Error naming the first invalid field.
 */
export function parseSoilColumn(data: unknown): SoilColumn {
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new Error("soil column must be a JSON object");
  }
  const obj = data as Record<string, unknown>;
  const textures = obj["textures"];
  if (!Array.isArray(textures) || !textures.every((t) => typeof t === "string")) throw new Error("textures must be an array of strings");
  const layerBounds = obj["layer_bounds"];
  if (!Array.isArray(layerBounds) || layerBounds.length < 2 || !layerBounds.every((v) => typeof v === "number")) throw new Error("layer_bounds must be an array of at least two numbers");
  const rootDepth = obj["root_depth"];
  if (typeof rootDepth !== "number" || !(rootDepth > 0)) throw new Error("root_depth must be a positive number");
  const model = obj["model"];
  if (typeof model !== "string" || !(CURVE_MODELS as readonly string[]).includes(model)) throw new Error("model must be a known curve model");
  const total = obj["total"];
  if (typeof total !== "number" || !Number.isFinite(total)) throw new Error("total must be a finite number");
  const raw = obj["layers"];
  if (!Array.isArray(raw) || raw.length !== layerBounds.length - 1) throw new Error("layers must have one entry per layer bound interval");
  const layers = raw.map((r: unknown, i) => {
    if (typeof r !== "object" || r === null) throw new Error(`layers[${i}] must be an object`);
    const rec = r as Record<string, unknown>;
    if (typeof rec["texture"] !== "string") throw new Error(`layers[${i}].texture must be a string`);
    const num = (key: string): number => {
      const v = rec[key];
      if (typeof v !== "number" || !Number.isFinite(v)) throw new Error(`layers[${i}].${key} must be a finite number`);
      return v;
    };
    return { top: num("top"), bottom: num("bottom"), texture: rec["texture"], fraction: num("fraction"), thicknessInRoots: num("thickness_in_roots"), mm: num("mm") };
  });
  return { textures: textures as string[], layerBounds: layerBounds as number[], rootDepth, model: model as CurveModel, layers, total };
}
