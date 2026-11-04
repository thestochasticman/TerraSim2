import { describe, expect, it } from "vitest";
import { parseSoilColumn } from "./parseSoilColumn";

const good = () => ({
  textures: ["sand", "clay"],
  layer_bounds: [0, 0.3, 1.0],
  root_depth: 0.6,
  model: "campbell",
  layers: [
    { top: 0, bottom: 0.3, texture: "sand", fraction: 0.035, thickness_in_roots: 0.3, mm: 10.5 },
    { top: 0.3, bottom: 1.0, texture: "clay", fraction: 0.148, thickness_in_roots: 0.3, mm: 44.4 },
  ],
  total: 54.9,
});

describe("parseSoilColumn", () => {
  it("maps snake_case fields to camelCase", () => {
    const out = parseSoilColumn(good());
    expect(out.layerBounds).toEqual([0, 0.3, 1.0]);
    expect(out.rootDepth).toBe(0.6);
    expect(out.model).toBe("campbell");
    expect(out.layers[1]).toEqual({ top: 0.3, bottom: 1.0, texture: "clay", fraction: 0.148, thicknessInRoots: 0.3, mm: 44.4 });
    expect(out.total).toBe(54.9);
  });

  it("rejects a layer count that does not match the bounds, an unknown model, and a missing number", () => {
    expect(() => parseSoilColumn({ ...good(), layer_bounds: [0, 1] })).toThrow("one entry per layer bound interval");
    expect(() => parseSoilColumn({ ...good(), model: "rosetta" })).toThrow("known curve model");
    const bad = good() as unknown as { layers: Record<string, unknown>[] };
    delete bad.layers[0]["mm"];
    expect(() => parseSoilColumn(bad)).toThrow("layers[0].mm");
    expect(() => parseSoilColumn([])).toThrow("JSON object");
  });
});
