import { describe, expect, it } from "vitest";
import { computeUpslopeColours } from "./computeUpslopeColours";
import { NO_DATA_COLOUR, mapMoistureToColour } from "./mapMoistureToColour";

/** The ramp colour as the Float32Array will hold it. */
const f32 = (rgb: [number, number, number]) => Array.from(Float32Array.from(rgb));

describe("computeUpslopeColours", () => {
  it("is light at a count of 1, dark at the largest count, and logarithmic between", () => {
    const colours = computeUpslopeColours(Float64Array.from([1, 10, 100]));
    expect(Array.from(colours.slice(0, 3))).toEqual(f32(mapMoistureToColour(0)));
    expect(Array.from(colours.slice(6, 9))).toEqual(f32(mapMoistureToColour(1)));
    expect(Array.from(colours.slice(3, 6))).toEqual(f32(mapMoistureToColour(0.5)));
  });

  it("paints a bad count grey and an all-ones field light", () => {
    expect(Array.from(computeUpslopeColours(Float64Array.from([0, 5])).slice(0, 3))).toEqual(f32(NO_DATA_COLOUR));
    expect(Array.from(computeUpslopeColours(Float64Array.from([1, 1])).slice(3, 6))).toEqual(f32(mapMoistureToColour(0)));
  });
});
