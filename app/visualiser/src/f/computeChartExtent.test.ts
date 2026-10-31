import { describe, expect, it } from "vitest";
import { computeChartExtent } from "./computeChartExtent";

describe("computeChartExtent", () => {
  it("pads the largest moisture and the largest flux across all flux series by 5 percent", () => {
    const e = computeChartExtent({ dates: ["a", "b"], rain: [0, 12], pet: [4, 5], moisture: [40, 60], infiltration: [0, 12], runoff: [0, 30], evaporation: [2, 2] });
    expect(e.maxMoisture).toBeCloseTo(63);
    expect(e.maxFlux).toBeCloseTo(31.5);
  });

  it("works without the optional flux series", () => {
    const e = computeChartExtent({ dates: ["a"], rain: [3], pet: [8], moisture: [50] });
    expect(e.maxFlux).toBeCloseTo(8.4);
  });

  it("never returns less than 1, so an empty or all-zero series still has an axis", () => {
    const e = computeChartExtent({ dates: [], rain: [], pet: [], moisture: [] });
    expect(e.maxMoisture).toBe(1);
    expect(e.maxFlux).toBe(1);
  });
});
