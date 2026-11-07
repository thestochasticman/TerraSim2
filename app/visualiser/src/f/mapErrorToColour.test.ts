import { describe, expect, it } from "vitest";
import { mapErrorToColour } from "./mapErrorToColour";
import { NO_DATA_COLOUR } from "./mapMoistureToColour";

describe("mapErrorToColour", () => {
  it("is neutral grey at zero, red when the model is dry, blue when wet, clamped at the scale", () => {
    const zero = mapErrorToColour(0, 0.1);
    expect(zero[0]).toBeCloseTo(0xf0 / 255, 5);
    expect(zero[1]).toBeCloseTo(0xef / 255, 5);
    const dry = mapErrorToColour(-0.1, 0.1);
    expect(dry[0]).toBeCloseTo(0xe3 / 255, 5);
    expect(dry[2]).toBeCloseTo(0x48 / 255, 5);
    expect(mapErrorToColour(-5, 0.1)).toEqual(dry);
    const wet = mapErrorToColour(0.1, 0.1);
    expect(wet[2]).toBeCloseTo(0xd6 / 255, 5);
    expect(mapErrorToColour(5, 0.1)).toEqual(wet);
    expect(dry[0]).toBeGreaterThan(wet[0]);
    expect(wet[2]).toBeGreaterThan(dry[2]);
  });

  it("interpolates linearly: halfway to the pole sits halfway in each channel", () => {
    const zero = mapErrorToColour(0, 1);
    const wet = mapErrorToColour(1, 1);
    const half = mapErrorToColour(0.5, 1);
    for (let k = 0; k < 3; k++) expect(half[k]).toBeCloseTo((zero[k] + wet[k]) / 2, 6);
  });

  it("gives the no-data grey for NaN and refuses a non-positive scale", () => {
    expect(mapErrorToColour(Number.NaN, 0.1)).toEqual(NO_DATA_COLOUR);
    expect(() => mapErrorToColour(0, 0)).toThrow("scale");
  });
});
