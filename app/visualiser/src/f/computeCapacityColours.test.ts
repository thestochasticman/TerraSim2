import { describe, expect, it } from "vitest";
import { computeCapacityColours } from "./computeCapacityColours";
import { NO_DATA_COLOUR, mapMoistureToColour } from "./mapMoistureToColour";

/** The ramp colour as the Float32Array will hold it. */
const f32 = (rgb: [number, number, number]) => Array.from(Float32Array.from(rgb));

describe("computeCapacityColours", () => {
  it("scales by the largest capacity: the largest is darkest, zero is lightest", () => {
    const colours = computeCapacityColours(Float64Array.from([0, 40, 80]));
    expect(colours).toHaveLength(9);
    expect(Array.from(colours.slice(6, 9))).toEqual(f32(mapMoistureToColour(1)));
    expect(Array.from(colours.slice(0, 3))).toEqual(f32(mapMoistureToColour(0)));
    expect(colours[3]).toBeLessThan(colours[0]);
    expect(colours[3]).toBeGreaterThan(colours[6]);
  });

  it("ignores NaN when finding the maximum and paints it grey; all-zero paints everything grey", () => {
    const colours = computeCapacityColours(Float64Array.from([Number.NaN, 50]));
    expect(Array.from(colours.slice(0, 3))).toEqual(f32(NO_DATA_COLOUR));
    expect(Array.from(colours.slice(3, 6))).toEqual(f32(mapMoistureToColour(1)));
    expect(Array.from(computeCapacityColours(Float64Array.from([0, 0])).slice(0, 3))).toEqual(f32(NO_DATA_COLOUR));
  });
});
