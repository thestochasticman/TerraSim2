import { describe, expect, it } from "vitest";
import { computeRelativeMoistureColours } from "./computeRelativeMoistureColours";
import { NO_DATA_COLOUR, mapMoistureToColour } from "./mapMoistureToColour";

/** The ramp colour as the Float32Array will hold it. */
const f32 = (rgb: [number, number, number]) => Array.from(Float32Array.from(rgb));

describe("computeRelativeMoistureColours", () => {
  it("stretches the day's range: driest lightest, wettest darkest, however small the spread", () => {
    const colours = computeRelativeMoistureColours(Float32Array.from([20.0, 20.5, 21.0]));
    expect(Array.from(colours.slice(0, 3))).toEqual(f32(mapMoistureToColour(0)));
    expect(Array.from(colours.slice(6, 9))).toEqual(f32(mapMoistureToColour(1)));
    expect(Array.from(colours.slice(3, 6))).toEqual(f32(mapMoistureToColour(0.5)));
  });

  it("paints NaN grey and a uniform day dark", () => {
    const colours = computeRelativeMoistureColours(Float32Array.from([Number.NaN, 5, 9]));
    expect(Array.from(colours.slice(0, 3))).toEqual(f32(NO_DATA_COLOUR));
    expect(Array.from(computeRelativeMoistureColours(Float32Array.from([7, 7])).slice(0, 3))).toEqual(f32(mapMoistureToColour(1)));
  });
});
