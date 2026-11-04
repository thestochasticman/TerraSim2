import { describe, expect, it } from "vitest";
import { invertTernary } from "./invertTernary";
import { projectTernary } from "./projectTernary";

describe("invertTernary", () => {
  it("undoes projectTernary", () => {
    for (const [sand, silt, clay] of [[1, 0, 0], [0, 1, 0], [0, 0, 1], [0.2, 0.3, 0.5], [0.6, 0.1, 0.3]]) {
      const p = projectTernary(sand, silt, clay);
      const back = invertTernary(p.x, p.y);
      expect(back.sand).toBeCloseTo(sand);
      expect(back.silt).toBeCloseTo(silt);
      expect(back.clay).toBeCloseTo(clay);
    }
  });

  it("gives a negative fraction outside the triangle", () => {
    expect(invertTernary(-0.1, 0).silt).toBeLessThan(0);
    expect(invertTernary(0.5, -0.1).clay).toBeLessThan(0);
    expect(invertTernary(1.2, 0).sand).toBeLessThan(0);
  });
});
