import type { TextureTriangle } from "@/t/TextureTriangle";

/**
 * Turn the service's texture-triangle JSON into a TextureTriangle, checking the columns line up.
 *
 * data : unknown
 *     The parsed body of GET /api/soils/texture.
 *
 * Throws an Error naming the first invalid field.
 */
export function parseTextureTriangle(data: unknown): TextureTriangle {
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new Error("texture triangle must be a JSON object");
  }
  const obj = data as Record<string, unknown>;
  const textures = obj["textures"];
  if (!Array.isArray(textures) || textures.length === 0 || !textures.every((t) => typeof t === "string")) {
    throw new Error("textures must be a non-empty array of strings");
  }
  const step = obj["step"];
  if (typeof step !== "number" || !(step > 0)) throw new Error("step must be a positive number");
  const raw = obj["points"];
  if (typeof raw !== "object" || raw === null) throw new Error("points must be an object of columns");
  const cols = raw as Record<string, unknown>;
  const n = Array.isArray(cols["sand"]) ? cols["sand"].length : 0;
  if (n === 0) throw new Error("points.sand must be a non-empty array");
  const column = (key: string): number[] => {
    const v = cols[key];
    if (!Array.isArray(v) || v.length !== n || !v.every((x) => typeof x === "number" && Number.isFinite(x))) {
      throw new Error(`points.${key} must have one finite number per point (${n})`);
    }
    return v as number[];
  };
  const texture = column("texture");
  if (!texture.every((i) => Number.isInteger(i) && i >= 0 && i < textures.length)) {
    throw new Error("points.texture must index into textures");
  }
  const typicalRaw = obj["typical"];
  if (!Array.isArray(typicalRaw)) throw new Error("typical must be an array");
  const typical = typicalRaw.map((r: unknown, i) => {
    if (typeof r !== "object" || r === null) throw new Error(`typical[${i}] must be an object`);
    const rec = r as Record<string, unknown>;
    if (typeof rec["texture"] !== "string") throw new Error(`typical[${i}].texture must be a string`);
    const num = (key: string): number => {
      const v = rec[key];
      if (typeof v !== "number" || !Number.isFinite(v)) throw new Error(`typical[${i}].${key} must be a finite number`);
      return v;
    };
    return { texture: rec["texture"], sand: num("sand"), silt: num("silt"), clay: num("clay"), diameter: num("diameter") };
  });
  return {
    textures: textures as string[],
    step,
    points: { sand: column("sand"), silt: column("silt"), clay: column("clay"), texture, diameter: column("diameter"), psiE: column("psi_e"), b: column("b") },
    typical,
  };
}
