"use client";

import { useLayoutEffect, useRef } from "react";
import { InstancedMesh, Matrix4 } from "three";
import type { BucketSet } from "@/t/BucketSet";

export type BucketColumnsProps = {
  buckets: BucketSet;
};

/** The plant store's water, the darker blue of the process diagram. */
export const PLANT_STORE_COLOUR = "#2a6fc9";
/** The free store's water, the lighter blue. */
export const FREE_STORE_COLOUR = "#8fbbea";
/** The empty column, drawn translucent so the fills read inside it. */
export const SHELL_COLOUR = "#c9ced6";

/**
 * The soil columns under the surface, as three instanced meshes over one unit
 * box: a translucent shell the height of each whole column, the plant store's
 * water filling the column from its bottom, and the free store's water filling
 * the part above the plant store. Must sit inside a Canvas. Each day's set
 * rewrites the instance matrices; a set with another count remounts the meshes,
 * since an instanced mesh cannot grow.
 */
export function BucketColumns({ buckets }: BucketColumnsProps) {
  const shell = useRef<InstancedMesh>(null);
  const plant = useRef<InstancedMesh>(null);
  const free = useRef<InstancedMesh>(null);

  useLayoutEffect(() => {
    const meshes = [shell.current, plant.current, free.current];
    if (meshes.some((m) => m === null)) return;
    const matrix = new Matrix4();
    const place = (mesh: InstancedMesh, i: number, x: number, z: number, bottom: number, height: number) => {
      const h = Math.max(height, 0);
      matrix.makeScale(buckets.size, h, buckets.size);
      matrix.setPosition(x, bottom + h / 2, z);
      mesh.setMatrixAt(i, matrix);
    };
    for (let i = 0; i < buckets.count; i++) {
      const x = buckets.tops[i * 3];
      const top = buckets.tops[i * 3 + 1];
      const z = buckets.tops[i * 3 + 2];
      const total = buckets.plantDepth[i] + buckets.freeDepth[i];
      place(shell.current as InstancedMesh, i, x, z, top - total, total);
      place(plant.current as InstancedMesh, i, x, z, top - total, buckets.plantDepth[i] * buckets.plantFill[i]);
      place(free.current as InstancedMesh, i, x, z, top - buckets.freeDepth[i], buckets.freeDepth[i] * buckets.freeFill[i]);
    }
    for (const mesh of meshes) (mesh as InstancedMesh).instanceMatrix.needsUpdate = true;
  }, [buckets]);

  return (
    <group key={buckets.count}>
      <instancedMesh ref={plant} args={[undefined, undefined, buckets.count]} frustumCulled={false}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={PLANT_STORE_COLOUR} />
      </instancedMesh>
      <instancedMesh ref={free} args={[undefined, undefined, buckets.count]} frustumCulled={false}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={FREE_STORE_COLOUR} />
      </instancedMesh>
      <instancedMesh ref={shell} args={[undefined, undefined, buckets.count]} frustumCulled={false}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={SHELL_COLOUR} transparent opacity={0.18} depthWrite={false} />
      </instancedMesh>
    </group>
  );
}
