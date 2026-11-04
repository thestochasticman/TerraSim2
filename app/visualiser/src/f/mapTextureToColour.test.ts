import { describe, expect, it } from "vitest";
import { mapTextureToColour } from "./mapTextureToColour";

const lightness = (css: string) => css.match(/\d+/g)!.map(Number).reduce((a, b) => a + b, 0);

describe("mapTextureToColour", () => {
  it("on a light surface returns css rgb strings that darken from sand to clay", () => {
    const sand = mapTextureToColour(0, 12);
    const mid = mapTextureToColour(6, 12);
    const clay = mapTextureToColour(11, 12);
    expect(sand).toMatch(/^rgb\(\d+, \d+, \d+\)$/);
    expect(lightness(sand)).toBeGreaterThan(lightness(mid));
    expect(lightness(mid)).toBeGreaterThan(lightness(clay));
    expect(clay).toBe("rgb(13, 54, 107)");
    expect(lightness(sand)).toBeLessThan(3 * 250);
  });

  it("on a dark surface lightens from sand to clay, ending on the lightest step", () => {
    const sand = mapTextureToColour(0, 12, "dark");
    const clay = mapTextureToColour(11, 12, "dark");
    expect(lightness(sand)).toBeLessThan(lightness(mapTextureToColour(6, 12, "dark")));
    expect(clay).toBe("rgb(205, 226, 251)");
    expect(lightness(sand)).toBeGreaterThan(3 * 60);
  });

  it("a single texture takes the far end of the range", () => {
    expect(mapTextureToColour(0, 1)).toBe("rgb(13, 54, 107)");
    expect(mapTextureToColour(0, 1, "dark")).toBe("rgb(205, 226, 251)");
  });
});
