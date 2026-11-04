import { describe, expect, it } from "vitest";
import { computeFiniteRange } from "./computeFiniteRange";

describe("computeFiniteRange", () => {
  it("skips NaN and infinities", () => {
    expect(computeFiniteRange(Float64Array.from([3, Number.NaN, -1, Number.POSITIVE_INFINITY, 7]))).toEqual({ min: -1, max: 7 });
    expect(computeFiniteRange([5])).toEqual({ min: 5, max: 5 });
  });

  it("is null when nothing is finite", () => {
    expect(computeFiniteRange([])).toBeNull();
    expect(computeFiniteRange([Number.NaN])).toBeNull();
  });
});
