import { describe, expect, it } from "vitest";
import { TRIANGLE_HEIGHT, projectTernary } from "./projectTernary";

describe("projectTernary", () => {
  it("puts the pure compositions at the three vertices", () => {
    expect(projectTernary(1, 0, 0)).toEqual({ x: 0, y: 0 });
    expect(projectTernary(0, 1, 0)).toEqual({ x: 1, y: 0 });
    expect(projectTernary(0, 0, 1)).toEqual({ x: 0.5, y: TRIANGLE_HEIGHT });
  });

  it("puts equal thirds at the centroid and a sand-silt mix on the base", () => {
    const c = projectTernary(1 / 3, 1 / 3, 1 / 3);
    expect(c.x).toBeCloseTo(0.5);
    expect(c.y).toBeCloseTo(TRIANGLE_HEIGHT / 3);
    expect(projectTernary(0.25, 0.75, 0)).toEqual({ x: 0.75, y: 0 });
  });
});
