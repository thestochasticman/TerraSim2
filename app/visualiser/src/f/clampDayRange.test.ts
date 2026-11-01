import { describe, expect, it } from "vitest";
import { clampDayRange } from "./clampDayRange";

describe("clampDayRange", () => {
  it("orders the ends and keeps a wide enough span as given", () => {
    expect(clampDayRange(40, 10, 100)).toEqual([10, 40]);
    expect(clampDayRange(10.4, 40.6, 100)).toEqual([10, 41]);
  });

  it("widens a narrow span around its centre to the minimum", () => {
    expect(clampDayRange(20, 20, 100)).toEqual([17, 23]);
    expect(clampDayRange(20, 22, 100, 5)).toEqual([19, 23]);
  });

  it("shifts a span that would leave the run instead of shrinking it", () => {
    expect(clampDayRange(0, 2, 100)).toEqual([0, 6]);
    expect(clampDayRange(98, 99, 100)).toEqual([93, 99]);
    expect(clampDayRange(-5, 3, 100)).toEqual([0, 8]);
  });

  it("never exceeds the run, even when the minimum span is longer than it", () => {
    expect(clampDayRange(0, 1, 4)).toEqual([0, 3]);
    expect(clampDayRange(0, 0, 2)).toEqual([0, 1]);
  });

  it("returns null when there is nothing to zoom", () => {
    expect(clampDayRange(0, 0, 1)).toBeNull();
    expect(clampDayRange(0, 0, 0)).toBeNull();
  });
});
