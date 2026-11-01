import { describe, expect, it } from "vitest";
import { computeCapacityColours } from "./computeCapacityColours";
import { NO_DATA_COLOUR, mapMoistureToColour } from "./mapMoistureToColour";

/** The ramp colour as the Float32Array will hold it. */
const f32 = (rgb: [number, number, number]) => Array.from(Float32Array.from(rgb));

describe("computeCapacityColours", () => {
  it("stretches the ramp over the finite range: the smallest is lightest, the largest darkest", () => {
    const colours = computeCapacityColours(Float64Array.from([30, 40, 50]));
    expect(colours).toHaveLength(9);
    expect(Array.from(colours.slice(0, 3))).toEqual(f32(mapMoistureToColour(0)));
    expect(Array.from(colours.slice(6, 9))).toEqual(f32(mapMoistureToColour(1)));
    expect(Array.from(colours.slice(3, 6))).toEqual(f32(mapMoistureToColour(0.5)));
  });

  it("ignores NaN when finding the range and paints it grey; a single value paints everything dark", () => {
    const colours = computeCapacityColours(Float64Array.from([Number.NaN, 20, 50]));
    expect(Array.from(colours.slice(0, 3))).toEqual(f32(NO_DATA_COLOUR));
    expect(Array.from(colours.slice(3, 6))).toEqual(f32(mapMoistureToColour(0)));
    expect(Array.from(computeCapacityColours(Float64Array.from([40, 40])).slice(0, 3))).toEqual(f32(mapMoistureToColour(1)));
    expect(Array.from(computeCapacityColours(Float64Array.from([Number.NaN])).slice(0, 3))).toEqual(f32(NO_DATA_COLOUR));
  });
});
