import { describe, expect, it } from "vitest";
import { decodeRunPairs } from "./decodeRunPairs";

function encode(values: number[]): ArrayBuffer {
  const buffer = new ArrayBuffer(values.length * 4);
  const view = new DataView(buffer);
  values.forEach((v, i) => view.setFloat32(i * 4, v, true));
  return buffer;
}

describe("decodeRunPairs", () => {
  it("splits the bytes into six columns of one length, in order", () => {
    const pairs = decodeRunPairs(encode([0, 3, 1, 2, 5, 6, 0, 1, 0.25, 0.5, 0.2, Number.NaN]));
    expect(Array.from(pairs.t)).toEqual([0, 3]);
    expect(Array.from(pairs.row)).toEqual([1, 2]);
    expect(Array.from(pairs.col)).toEqual([5, 6]);
    expect(Array.from(pairs.station)).toEqual([0, 1]);
    expect(Array.from(pairs.observed)).toEqual([0.25, 0.5]);
    expect(pairs.modelled[0]).toBeCloseTo(0.2, 6);
    expect(Number.isNaN(pairs.modelled[1])).toBe(true);
  });

  it("decodes an empty body as empty columns and refuses a length that is not six columns", () => {
    expect(decodeRunPairs(new ArrayBuffer(0)).t.length).toBe(0);
    expect(() => decodeRunPairs(encode([1, 2, 3, 4, 5, 6, 7]))).toThrow("28 bytes");
  });
});
