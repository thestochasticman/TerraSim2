import type { BucketSet } from "@/t/BucketSet";
import type { BucketStore } from "@/t/BucketStore";

/**
 * The columns with only the chosen store drawn.
 *
 * buckets : BucketSet
 * store : BucketStore
 *     "both" returns the set as it is; "plant" drops the free store, so each
 *     column is its plant store hanging from the surface; "free" drops the
 *     plant store, so each column is its free store hanging from the surface.
 *
 * Depths keep the set's scale, so a store is the same height whichever view
 * it is seen in; fills are untouched. Returns a new BucketSet, sharing the
 * arrays it does not change.
 */
export function selectBucketStore(buckets: BucketSet, store: BucketStore): BucketSet {
  if (store === "both") return buckets;
  const zero = new Float32Array(buckets.count);
  return store === "plant" ? { ...buckets, freeDepth: zero } : { ...buckets, plantDepth: zero };
}
