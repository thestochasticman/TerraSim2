import { describe, expect, it } from "vitest";
import { computeComparisonRanges } from "./computeComparisonRanges";
import type { RunPairs } from "@/t/RunPairs";

function pairsOf(observed: number[], modelled: number[]): RunPairs {
  const n = observed.length;
  return { t: new Float32Array(n), row: new Float32Array(n), col: new Float32Array(n), station: new Float32Array(n), observed: Float32Array.from(observed), modelled: Float32Array.from(modelled) };
}

describe("computeComparisonRanges", () => {
  it("spans the observed contents and takes the largest error the run has a value for", () => {
    const r = computeComparisonRanges(pairsOf([0.2, 0.5, 0.3], [0.25, Number.NaN, 0.1]));
    expect(r.observed?.min).toBeCloseTo(0.2, 6);
    expect(r.observed?.max).toBeCloseTo(0.5, 6);
    expect(r.errorScale).toBeCloseTo(0.2, 6);
  });

  it("has no error scale before the run has written anything, and none when every error is zero", () => {
    expect(computeComparisonRanges(pairsOf([0.2, 0.3], [Number.NaN, Number.NaN])).errorScale).toBeNull();
    expect(computeComparisonRanges(pairsOf([0.2, 0.3], [0.2, 0.3])).errorScale).toBeNull();
    expect(computeComparisonRanges(pairsOf([], [])).observed).toBeNull();
  });
});
