import { describe, expect, it } from "vitest";
import { parseRetentionCurves } from "./parseRetentionCurves";

const record = (texture: string, theta: number[], fc: number, pwp: number) => ({ texture, theta, theta_fc: fc, theta_pwp: pwp, available_water: 1000 * (fc - pwp) });
const good = () => ({
  suction: [1, 10, 100],
  field_capacity: 33,
  wilting_point: 1500,
  models: {
    campbell: [record("sand", [0.37, 0.1, 0.05], 0.04, 0.004), record("clay", [0.5, 0.45, 0.4], 0.376, 0.228)],
    van_genuchten: [record("sand", [0.38, 0.12, 0.06], 0.06, 0.02), record("clay", [0.5, 0.46, 0.41], 0.39, 0.25)],
  },
});

describe("parseRetentionCurves", () => {
  it("maps snake_case records to camelCase and keeps texture order", () => {
    const out = parseRetentionCurves(good());
    expect(out.suction).toEqual([1, 10, 100]);
    expect(out.fieldCapacity).toBe(33);
    expect(out.wiltingPoint).toBe(1500);
    expect(out.models.campbell.map((c) => c.texture)).toEqual(["sand", "clay"]);
    expect(out.models.van_genuchten[1]).toEqual({ texture: "clay", theta: [0.5, 0.46, 0.41], thetaFc: 0.39, thetaPwp: 0.25, availableWater: 140 });
  });

  it("rejects bad suctions", () => {
    expect(() => parseRetentionCurves({ ...good(), suction: [1] })).toThrow("at least two");
    expect(() => parseRetentionCurves({ ...good(), suction: [10, 1, 100] })).toThrow("ascending");
    expect(() => parseRetentionCurves({ ...good(), suction: [0, 1, 2] })).toThrow("positive");
  });

  it("rejects a record whose theta does not match the suctions, or a missing number", () => {
    const bad = good();
    bad.models.campbell[0].theta = [0.37, 0.1];
    expect(() => parseRetentionCurves(bad)).toThrow("models.campbell[0].theta");
    const missing = good() as unknown as { models: { van_genuchten: Record<string, unknown>[] } };
    delete missing.models.van_genuchten[1]["available_water"];
    expect(() => parseRetentionCurves(missing)).toThrow("models.van_genuchten[1].available_water");
  });

  it("rejects models that disagree on textures, and non-objects", () => {
    const bad = good();
    bad.models.van_genuchten.reverse();
    expect(() => parseRetentionCurves(bad)).toThrow("same textures in the same order");
    expect(() => parseRetentionCurves(null)).toThrow("JSON object");
    expect(() => parseRetentionCurves({ ...good(), models: { campbell: [] } })).toThrow("models.campbell must be a non-empty array");
  });
});
