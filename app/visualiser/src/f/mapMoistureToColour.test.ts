import { describe, expect, it } from "vitest";
import { NO_DATA_COLOUR, mapMoistureToColour } from "./mapMoistureToColour";

describe("mapMoistureToColour", () => {
  it("returns the lightest step at 0 and the darkest at 1", () => {
    const dry = mapMoistureToColour(0);
    const wet = mapMoistureToColour(1);
    expect(dry.map((v) => Math.round(v * 255))).toEqual([0xcd, 0xe2, 0xfb]);
    expect(wet.map((v) => Math.round(v * 255))).toEqual([0x0d, 0x36, 0x6b]);
  });

  it("gets darker monotonically as fullness rises: one hue, light to dark", () => {
    let previous = Infinity;
    for (let f = 0; f <= 1.0001; f += 0.05) {
      const [r, g, b] = mapMoistureToColour(f);
      const lightness = r + g + b;
      expect(lightness).toBeLessThanOrEqual(previous + 1e-9);
      expect(b).toBeGreaterThanOrEqual(r);
      previous = lightness;
    }
  });

  it("clamps out-of-range fractions and greys out NaN", () => {
    expect(mapMoistureToColour(-0.5)).toEqual(mapMoistureToColour(0));
    expect(mapMoistureToColour(3)).toEqual(mapMoistureToColour(1));
    expect(mapMoistureToColour(Number.NaN)).toEqual(NO_DATA_COLOUR);
  });

  it("interpolates between steps", () => {
    const mid = mapMoistureToColour(1 / 24);
    const [r0] = mapMoistureToColour(0);
    const [r1] = mapMoistureToColour(1 / 12);
    expect(mid[0]).toBeCloseTo((r0 + r1) / 2, 6);
  });
});
