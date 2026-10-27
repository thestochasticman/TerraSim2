import { describe, expect, it } from "vitest";
import { readPositiveInteger } from "./readPositiveInteger";

describe("readPositiveInteger", () => {
  it("returns a positive integer field unchanged", () => {
    expect(readPositiveInteger({ n: 1 }, "n")).toBe(1);
    expect(readPositiveInteger({ n: 1000 }, "n")).toBe(1000);
  });

  it("rejects zero, negatives and fractions", () => {
    for (const bad of [0, -1, 0.5, 2.5]) {
      expect(() => readPositiveInteger({ n: bad }, "n")).toThrow("n must be a positive integer");
    }
  });

  it("rejects missing fields and non-numbers", () => {
    expect(() => readPositiveInteger({}, "n")).toThrow("n must be a positive integer");
    for (const bad of ["1", null, true, [1], NaN, Infinity]) {
      expect(() => readPositiveInteger({ n: bad }, "n")).toThrow("n must be a positive integer");
    }
  });

  it("names the key it was asked for in the error", () => {
    expect(() => readPositiveInteger({ rows: -2 }, "rows")).toThrow("rows must be a positive integer");
  });
});
