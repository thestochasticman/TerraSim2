import { describe, expect, it } from "vitest";
import { computeChartExtent } from "./computeChartExtent";

describe("computeChartExtent", () => {
  it("pads the largest moisture, the largest rain, and the larger of demand and evaporation plus runoff", () => {
    const e = computeChartExtent({ dates: ["a", "b"], rain: [0, 12], pet: [4, 5], moisture: [40, 60], infiltration: [0, 12], runoff: [0, 30], evaporation: [2, 2] });
    expect(e.maxMoisture).toBeCloseTo(63);
    expect(e.maxIn).toBeCloseTo(12.6);
    expect(e.maxOut).toBeCloseTo(33.6);
  });

  it("stacks inflow on rain for the upward side", () => {
    const e = computeChartExtent({ dates: ["a", "b"], rain: [10, 2], pet: [1, 1], moisture: [1, 1], inflow: [0, 12] });
    expect(e.maxIn).toBeCloseTo(14.7);
  });

  it("uses demand for the outward side when it exceeds the losses", () => {
    const e = computeChartExtent({ dates: ["a"], rain: [3], pet: [8], moisture: [50], evaporation: [2], runoff: [1] });
    expect(e.maxOut).toBeCloseTo(8.4);
  });

  it("works without the optional flux series", () => {
    const e = computeChartExtent({ dates: ["a"], rain: [3], pet: [8], moisture: [50] });
    expect(e.maxOut).toBeCloseTo(8.4);
    expect(e.maxIn).toBeCloseTo(3.15);
  });

  it("never returns less than 1, so an empty or all-zero series still has an axis", () => {
    const e = computeChartExtent({ dates: [], rain: [], pet: [], moisture: [] });
    expect(e.maxMoisture).toBe(1);
    expect(e.maxIn).toBe(1);
    expect(e.maxOut).toBe(1);
  });
});
