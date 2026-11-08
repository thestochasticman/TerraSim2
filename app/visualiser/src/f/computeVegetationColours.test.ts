import { describe, expect, it } from "vitest";
import { VEGETATION_COLOURS, computeVegetationColours } from "./computeVegetationColours";
import { NO_DATA_COLOUR } from "./mapMoistureToColour";

describe("computeVegetationColours", () => {
  it("gives grass yellow, trees green, and the unknown grey, three floats per cell", () => {
    const out = computeVegetationColours(Float64Array.from([0, 1, -1, 7]));
    expect(out).toHaveLength(12);
    expect(Array.from(out.slice(0, 3)).map((v) => Math.round(v * 255))).toEqual([0xed, 0xa1, 0x00]);
    expect(Array.from(out.slice(3, 6)).map((v) => Math.round(v * 255))).toEqual([0x00, 0x83, 0x00]);
    expect(Array.from(out.slice(6, 9))).toEqual(NO_DATA_COLOUR.map(Math.fround));
    expect(Array.from(out.slice(9, 12))).toEqual(NO_DATA_COLOUR.map(Math.fround));
    expect(VEGETATION_COLOURS).toHaveLength(2);
  });
});
