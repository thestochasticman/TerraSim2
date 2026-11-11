"use client";

import { useLayoutEffect, useRef } from "react";
import { InstancedMesh, Matrix4 } from "three";
import type { BucketSet } from "@/t/BucketSet";

export type BucketColumnsProps = {
  buckets: BucketSet;
};

/** The plant store's water, the darker blue of the process diagram. */
export const PLANT_STORE_COLOUR = "#1f5fbf";
/** The free store's water, the lighter blue. */
export const FREE_STORE_COLOUR = "#6fb1f0";
/** The empty part of a column, dry soil in the sand of the process diagram, drawn translucent so the fills read inside it. */
export const SHELL_COLOUR = "#e3d5b4";
/** The shell's footprint relative to the fills', slightly inside them so the water's faces are not veiled by the translucent shell. */
export const SHELL_INSET = 0.96;
/** The shell's height relative to the column's, so a full fill's top face sits clear of the shell's and the two do not flicker. */
export const SHELL_HEIGHT_INSET = 0.99;

/**
 * The soil columns under the surface, as three instanced meshes over one unit
 * box: a translucent shell the height of each whole column, set slightly
 * inside the fills so their faces stay clear of it, the plant store's water
 * filling the column from its bottom, and the free store's water filling the
 * part above the plant store. Must sit inside a Canvas. Each day's set
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
    const place = (mesh: InstancedMesh, i: number, x: number, z: number, bottom: number, height: number, width = buckets.size) => {
      const h = Math.max(height, 0);
      matrix.makeScale(width, h, width);
      matrix.setPosition(x, bottom + h / 2, z);
      mesh.setMatrixAt(i, matrix);
    };
    for (let i = 0; i < buckets.count; i++) {
      const x = buckets.tops[i * 3];
      const top = buckets.tops[i * 3 + 1];
      const z = buckets.tops[i * 3 + 2];
      const total = buckets.plantDepth[i] + buckets.freeDepth[i];
      place(shell.current as InstancedMesh, i, x, z, top - total + (total * (1 - SHELL_HEIGHT_INSET)) / 2, total * SHELL_HEIGHT_INSET, buckets.size * SHELL_INSET);
      place(plant.current as InstancedMesh, i, x, z, top - total, buckets.plantDepth[i] * buckets.plantFill[i]);
      place(free.current as InstancedMesh, i, x, z, top - buckets.freeDepth[i], buckets.freeDepth[i] * buckets.freeFill[i]);
    }
    for (const mesh of meshes) (mesh as InstancedMesh).instanceMatrix.needsUpdate = true;
  }, [buckets]);

  return (
    <group key={buckets.count}>
      <instancedMesh ref={plant} args={[undefined, undefined, buckets.count]} frustumCulled={false}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={PLANT_STORE_COLOUR} emissive={PLANT_STORE_COLOUR} emissiveIntensity={0.35} />
      </instancedMesh>
      <instancedMesh ref={free} args={[undefined, undefined, buckets.count]} frustumCulled={false}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={FREE_STORE_COLOUR} emissive={FREE_STORE_COLOUR} emissiveIntensity={0.35} />
      </instancedMesh>
      <instancedMesh ref={shell} args={[undefined, undefined, buckets.count]} frustumCulled={false}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={SHELL_COLOUR} transparent opacity={0.45} depthWrite={false} />
      </instancedMesh>
    </group>
  );
}
