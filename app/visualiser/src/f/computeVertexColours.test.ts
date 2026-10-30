import { describe, expect, it } from "vitest";
import { computeVertexColours } from "./computeVertexColours";
import { NO_DATA_COLOUR, mapMoistureToColour } from "./mapMoistureToColour";

/** The colour as it is stored: float32. */
const f32 = (rgb: [number, number, number]) => Array.from(Float32Array.from(rgb));
const cell = (colours: Float32Array, i: number) => Array.from(colours.slice(i * 3, i * 3 + 3));

describe("computeVertexColours", () => {
  it("colours each cell by moisture over its own capacity, three floats per cell", () => {
    const colours = computeVertexColours(Float32Array.from([0, 50, 100]), Float64Array.from([100, 100, 100]));
    expect(colours.length).toBe(9);
    expect(cell(colours, 0)).toEqual(f32(mapMoistureToColour(0)));
    expect(cell(colours, 1)).toEqual(f32(mapMoistureToColour(0.5)));
    expect(cell(colours, 2)).toEqual(f32(mapMoistureToColour(1)));
  });

  it("uses per-cell capacity, so equal moisture in a smaller store reads fuller", () => {
    const colours = computeVertexColours(Float32Array.from([40, 40]), Float64Array.from([80, 160]));
    expect(cell(colours, 0)).toEqual(f32(mapMoistureToColour(0.5)));
    expect(cell(colours, 1)).toEqual(f32(mapMoistureToColour(0.25)));
  });

  it("falls back to the day's maximum when there is no capacity", () => {
    const colours = computeVertexColours(Float32Array.from([10, 20, 40]));
    expect(cell(colours, 2)).toEqual(f32(mapMoistureToColour(1)));
    expect(cell(colours, 0)).toEqual(f32(mapMoistureToColour(0.25)));
  });

  it("greys a zero-capacity cell and rejects a length mismatch", () => {
    expect(cell(computeVertexColours(Float32Array.from([5]), Float64Array.from([0])), 0)).toEqual(f32(NO_DATA_COLOUR));
    expect(() => computeVertexColours(Float32Array.from([1, 2]), Float64Array.from([1]))).toThrow("capacity has 1 cells but moisture has 2");
  });
});
