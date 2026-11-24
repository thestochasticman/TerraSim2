import { describe, expect, it } from "vitest";
import { computeSvgScale } from "./computeSvgScale";

describe("computeSvgScale", () => {
  it("a box the viewBox's shape is drawn edge to edge", () => {
    expect(computeSvgScale(600, 130, 1200, 260)).toEqual({ scale: 0.5, offsetX: 0, offsetY: 0 });
  });

  it("a box too tall for the viewBox fills the width and centres vertically", () => {
    expect(computeSvgScale(1200, 400, 1200, 260)).toEqual({ scale: 1, offsetX: 0, offsetY: 70 });
  });

  it("a box too wide for the viewBox fills the height and centres horizontally, which is the letterboxing a max-height causes", () => {
    const { scale, offsetX, offsetY } = computeSvgScale(1650, 300, 1200, 260);
    expect(scale).toBeCloseTo(300 / 260, 10);
    expect(offsetX).toBeCloseTo((1650 - 1200 * (300 / 260)) / 2, 10);
    expect(offsetY).toBe(0);
  });

  it("a box or viewBox without area maps one to one", () => {
    expect(computeSvgScale(0, 300, 1200, 260)).toEqual({ scale: 1, offsetX: 0, offsetY: 0 });
    expect(computeSvgScale(600, 300, 1200, 0)).toEqual({ scale: 1, offsetX: 0, offsetY: 0 });
  });
});
