import { describe, expect, it } from "vitest";
import { selectPairsOnDay } from "./selectPairsOnDay";
import type { RunPairs } from "@/t/RunPairs";

const pairs: RunPairs = {
  t: Float32Array.from([0, 3, 3, Number.NaN, 7]),
  row: new Float32Array(5),
  col: new Float32Array(5),
  station: new Float32Array(5),
  observed: new Float32Array(5),
  modelled: new Float32Array(5),
};

describe("selectPairsOnDay", () => {
  it("returns the indices of that day's pairs in order, and nothing for a day without any", () => {
    expect(selectPairsOnDay(pairs, 3)).toEqual([1, 2]);
    expect(selectPairsOnDay(pairs, 0)).toEqual([0]);
    expect(selectPairsOnDay(pairs, 5)).toEqual([]);
  });

  it("never matches an unpaired observation", () => {
    expect(selectPairsOnDay(pairs, Number.NaN)).toEqual([]);
  });
});
