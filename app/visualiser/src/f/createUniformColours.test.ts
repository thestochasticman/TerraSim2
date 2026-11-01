import { describe, expect, it } from "vitest";
import { createUniformColours } from "./createUniformColours";

describe("createUniformColours", () => {
  it("repeats the colour three floats per vertex", () => {
    const out = createUniformColours(3, [0.5, 0.25, 1]);
    expect(out).toHaveLength(9);
    expect(Array.from(out)).toEqual([0.5, 0.25, 1, 0.5, 0.25, 1, 0.5, 0.25, 1]);
  });

  it("is empty for no vertices", () => {
    expect(createUniformColours(0, [1, 1, 1])).toHaveLength(0);
  });
});
