import ReactThreeTestRenderer from "@react-three/test-renderer";
import { type InstancedMesh, Matrix4, type MeshStandardMaterial } from "three";
import { describe, expect, it } from "vitest";
import { BucketColumns, FREE_STORE_COLOUR, PLANT_STORE_COLOUR, SHELL_COLOUR } from "./BucketColumns";
import type { BucketSet } from "@/t/BucketSet";

// Two columns: the first 0.6 m of plant store under 0.3 m of free store, half the plant store wet;
// the second twice as deep, the plant store full and the free store half full.
const buckets: BucketSet = {
  count: 2,
  block: 2,
  size: 16,
  tops: Float32Array.from([5, 106, 5, 25, 108, 5]),
  plantDepth: Float32Array.from([0.6, 1.2]),
  freeDepth: Float32Array.from([0.3, 0.6]),
  plantFill: Float32Array.from([0.5, 1]),
  freeFill: Float32Array.from([0, 0.5]),
};

/** The test renderer files instanced meshes under the plain mesh type; pick them out by their flag and name them by colour. */
function findByColour(scene: { findAllByType: (type: string) => { instance: unknown }[] }): Record<string, InstancedMesh> {
  const out: Record<string, InstancedMesh> = {};
  for (const node of scene.findAllByType("Mesh")) {
    const mesh = node.instance as InstancedMesh;
    if (mesh.isInstancedMesh) out["#" + (mesh.material as MeshStandardMaterial).color.getHexString()] = mesh;
  }
  return out;
}

/** A box's centre height, height and width, read straight off its matrix: decompose() would report a zero-height box as unit scale. */
function placed(mesh: InstancedMesh, i: number): { y: number; height: number; width: number } {
  const matrix = new Matrix4();
  mesh.getMatrixAt(i, matrix);
  const e = matrix.elements;
  return { y: e[13], height: e[5], width: e[0] };
}

describe("BucketColumns", () => {
  it("mounts a shell, a plant fill and a free fill per column, each box placed and scaled from the set", async () => {
    const renderer = await ReactThreeTestRenderer.create(<BucketColumns buckets={buckets} />);
    const meshes = findByColour(renderer.scene);
    expect(Object.keys(meshes).sort()).toEqual([FREE_STORE_COLOUR, PLANT_STORE_COLOUR, SHELL_COLOUR].sort());
    for (const mesh of Object.values(meshes)) expect(mesh.count).toBe(2);
    // the shell of column 1 spans 1.8 m down from 108; its plant fill is the full 1.2 m from the bottom; its free fill the lower half of the top 0.6 m
    const shell = placed(meshes[SHELL_COLOUR], 1);
    expect(shell.width).toBeCloseTo(16, 5);
    expect(shell.height).toBeCloseTo(1.8, 5);
    expect(shell.y).toBeCloseTo(108 - 0.9, 5);
    const plant = placed(meshes[PLANT_STORE_COLOUR], 1);
    expect(plant.height).toBeCloseTo(1.2, 5);
    expect(plant.y).toBeCloseTo(108 - 1.8 + 0.6, 5);
    const free = placed(meshes[FREE_STORE_COLOUR], 1);
    expect(free.height).toBeCloseTo(0.3, 5);
    expect(free.y).toBeCloseTo(108 - 0.6 + 0.15, 5);
    // column 0: half the plant store wet, the free store empty
    expect(placed(meshes[PLANT_STORE_COLOUR], 0).height).toBeCloseTo(0.3, 5);
    expect(placed(meshes[FREE_STORE_COLOUR], 0).height).toBeCloseTo(0, 5);
    expect((meshes[SHELL_COLOUR].material as MeshStandardMaterial).transparent).toBe(true);
    await renderer.unmount();
  });

  it("a set with another count remounts the meshes with that many instances", async () => {
    const renderer = await ReactThreeTestRenderer.create(<BucketColumns buckets={buckets} />);
    const one: BucketSet = { count: 1, block: 1, size: 8, tops: Float32Array.from([0, 50, 0]), plantDepth: Float32Array.from([2]), freeDepth: Float32Array.from([0]), plantFill: Float32Array.from([0.25]), freeFill: Float32Array.from([0]) };
    await renderer.update(<BucketColumns buckets={one} />);
    const meshes = findByColour(renderer.scene);
    expect(Object.keys(meshes)).toHaveLength(3);
    for (const mesh of Object.values(meshes)) expect(mesh.count).toBe(1);
    expect(placed(meshes[PLANT_STORE_COLOUR], 0).height).toBeCloseTo(0.5, 5);
    expect(placed(meshes[PLANT_STORE_COLOUR], 0).y).toBeCloseTo(48.25, 5);
    await renderer.unmount();
  });
});
