import { describe, expect, it } from "vitest";
import { pickDay } from "./pickDay";

describe("pickDay", () => {
  it("maps the left edge to day 0, the right edge to the last day, and rounds between", () => {
    expect(pickDay(0, 100, 11)).toBe(0);
    expect(pickDay(100, 100, 11)).toBe(10);
    expect(pickDay(50, 100, 11)).toBe(5);
    expect(pickDay(54, 100, 11)).toBe(5);
    expect(pickDay(56, 100, 11)).toBe(6);
  });

  it("clamps positions outside the plot", () => {
    expect(pickDay(-20, 100, 11)).toBe(0);
    expect(pickDay(140, 100, 11)).toBe(10);
  });

  it("handles one day, no days and no width", () => {
    expect(pickDay(30, 100, 1)).toBe(0);
    expect(pickDay(30, 100, 0)).toBeNull();
    expect(pickDay(30, 0, 5)).toBeNull();
  });
});
