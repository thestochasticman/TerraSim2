import { describe, expect, it } from "vitest";
import { decodeMoistureDay } from "./decodeMoistureDay";

function encode(values: number[]): ArrayBuffer {
  const buffer = new ArrayBuffer(values.length * 4);
  const view = new DataView(buffer);
  values.forEach((v, i) => view.setFloat32(i * 4, v, true));
  return buffer;
}

describe("decodeMoistureDay", () => {
  it("decodes little-endian float32 row-major values", () => {
    const out = decodeMoistureDay(encode([1.5, 2, 3, 4, 5, 6.25]), 2, 3);
    expect(out).toBeInstanceOf(Float32Array);
    expect(Array.from(out)).toEqual([1.5, 2, 3, 4, 5, 6.25]);
    expect(out[1 * 3 + 2]).toBe(6.25);
  });

  it("is explicitly little-endian regardless of the platform", () => {
    const buffer = new ArrayBuffer(4);
    new DataView(buffer).setFloat32(0, 42, true);
    expect(decodeMoistureDay(buffer, 1, 1)[0]).toBe(42);
  });

  it("rejects a byte length that does not match the shape", () => {
    expect(() => decodeMoistureDay(encode([1, 2, 3]), 2, 2)).toThrow("has 12 bytes, expected 16 for 2 x 2");
  });
});
