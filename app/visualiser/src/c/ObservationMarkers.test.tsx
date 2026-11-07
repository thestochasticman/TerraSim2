import ReactThreeTestRenderer from "@react-three/test-renderer";
import { Color, type InstancedMesh, Matrix4, type SphereGeometry, Vector3 } from "three";
import { describe, expect, it } from "vitest";
import { ObservationMarkers } from "./ObservationMarkers";
import type { MarkerSet } from "@/t/MarkerSet";

const markers: MarkerSet = {
  count: 2,
  positions: Float32Array.from([10, 105, 20, 30, 107, 0]),
  colours: Float32Array.from([1, 0, 0, 0, 0, 1]),
  radius: 4.5,
};

/** The test renderer files an instanced mesh under the plain mesh type; pick it out by its flag. */
function findInstanced(scene: { findAllByType: (type: string) => { instance: unknown }[] }): InstancedMesh[] {
  return scene.findAllByType("Mesh").map((node) => node.instance as InstancedMesh).filter((mesh) => mesh.isInstancedMesh);
}

describe("ObservationMarkers", () => {
  it("mounts one instanced mesh with an instance per marker, placed and coloured as given", async () => {
    const renderer = await ReactThreeTestRenderer.create(<ObservationMarkers markers={markers} />);
    const meshes = findInstanced(renderer.scene);
    expect(meshes).toHaveLength(1);
    const mesh = meshes[0];
    expect(mesh.count).toBe(2);
    const matrix = new Matrix4();
    mesh.getMatrixAt(1, matrix);
    expect(new Vector3().setFromMatrixPosition(matrix).toArray()).toEqual([30, 107, 0]);
    const colour = new Color();
    mesh.getColorAt(0, colour);
    expect(colour.r).toBeCloseTo(1, 5);
    expect(colour.b).toBeCloseTo(0, 5);
    expect((mesh.geometry as SphereGeometry).parameters.radius).toBe(4.5);
    await renderer.unmount();
  });

  it("a set with another count remounts the mesh with that many instances", async () => {
    const renderer = await ReactThreeTestRenderer.create(<ObservationMarkers markers={markers} />);
    const one: MarkerSet = { count: 1, positions: Float32Array.from([0, 1, 2]), colours: Float32Array.from([0, 1, 0]), radius: 2 };
    await renderer.update(<ObservationMarkers markers={one} />);
    const meshes = findInstanced(renderer.scene);
    expect(meshes).toHaveLength(1);
    const mesh = meshes[0];
    expect(mesh.count).toBe(1);
    const matrix = new Matrix4();
    mesh.getMatrixAt(0, matrix);
    expect(new Vector3().setFromMatrixPosition(matrix).toArray()).toEqual([0, 1, 2]);
    await renderer.unmount();
  });
});
