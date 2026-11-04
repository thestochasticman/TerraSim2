import { describe, expect, it } from "vitest";
import { parseTextureTriangle } from "./parseTextureTriangle";

const good = () => ({
  textures: ["sand", "clay"],
  step: 50,
  points: { sand: [100, 0], silt: [0, 0], clay: [0, 100], texture: [0, 1], diameter: [317, 0.14], psi_e: [-0.4, -5.1], b: [1, 10.7] },
  typical: [{ texture: "sand", sand: 92, silt: 5, clay: 3, diameter: 211.75 }],
});

describe("parseTextureTriangle", () => {
  it("maps the columns and renames psi_e", () => {
    const out = parseTextureTriangle(good());
    expect(out.textures).toEqual(["sand", "clay"]);
    expect(out.step).toBe(50);
    expect(out.points.psiE).toEqual([-0.4, -5.1]);
    expect(out.points.texture).toEqual([0, 1]);
    expect(out.typical[0]).toEqual({ texture: "sand", sand: 92, silt: 5, clay: 3, diameter: 211.75 });
  });

  it("rejects a column of the wrong length, a bad class index, and a bad typical record", () => {
    const short = good();
    short.points.b = [1];
    expect(() => parseTextureTriangle(short)).toThrow("points.b");
    const bad = good();
    bad.points.texture = [0, 2];
    expect(() => parseTextureTriangle(bad)).toThrow("index into textures");
    const typical = good() as unknown as { typical: Record<string, unknown>[] };
    delete typical.typical[0]["clay"];
    expect(() => parseTextureTriangle(typical)).toThrow("typical[0].clay");
    expect(() => parseTextureTriangle(null)).toThrow("JSON object");
  });
});
