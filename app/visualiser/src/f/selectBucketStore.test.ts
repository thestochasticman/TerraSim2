import { describe, expect, it } from "vitest";
import { selectBucketStore } from "./selectBucketStore";
import type { BucketSet } from "@/t/BucketSet";

const buckets: BucketSet = {
  count: 2,
  block: 1,
  size: 6,
  tops: Float32Array.from([0, 10, 0, 10, 12, 0]),
  plantDepth: Float32Array.from([0.6, 1.2]),
  freeDepth: Float32Array.from([0.3, 0.6]),
  plantFill: Float32Array.from([0.5, 1]),
  freeFill: Float32Array.from([0, 0.5]),
};

describe("selectBucketStore", () => {
  it("both gives the set back unchanged", () => {
    expect(selectBucketStore(buckets, "both")).toBe(buckets);
  });

  it("plant keeps the plant store's depth and fill and drops the free store's depth, leaving the input alone", () => {
    const plant = selectBucketStore(buckets, "plant");
    expect(Array.from(plant.plantDepth)).toEqual([Float32Array.from([0.6])[0], Float32Array.from([1.2])[0]]);
    expect(Array.from(plant.freeDepth)).toEqual([0, 0]);
    expect(plant.plantFill).toBe(buckets.plantFill);
    expect(plant.tops).toBe(buckets.tops);
    expect(Array.from(buckets.freeDepth)).toEqual([Float32Array.from([0.3])[0], Float32Array.from([0.6])[0]]);
  });

  it("free keeps the free store's depth and fill and drops the plant store's depth", () => {
    const free = selectBucketStore(buckets, "free");
    expect(Array.from(free.plantDepth)).toEqual([0, 0]);
    expect(free.freeDepth).toBe(buckets.freeDepth);
    expect(free.freeFill).toBe(buckets.freeFill);
    expect(free.count).toBe(2);
  });
});
