import ReactThreeTestRenderer from "@react-three/test-renderer";
import type { Mesh, MeshStandardMaterial } from "three";
import { describe, expect, it } from "vitest";
import { TerrainSurface } from "./TerrainSurface";
import type { TerrainGrid } from "@/t/TerrainGrid";

function makeGrid(rows: number, cols: number, cellSize: number, elevation: number[], capacity?: number[]): TerrainGrid {
  const grid: TerrainGrid = { rows, cols, cellSize, elevation: Float64Array.from(elevation) };
  if (capacity) grid.capacity = Float64Array.from(capacity);
  return grid;
}

describe("TerrainSurface", () => {
  it("mounts one mesh whose geometry has a vertex per cell", async () => {
    const grid = makeGrid(3, 4, 1, new Array(12).fill(0));
    const renderer = await ReactThreeTestRenderer.create(<TerrainSurface grid={grid} />);
    const meshes = renderer.scene.findAllByType("Mesh");
    expect(meshes).toHaveLength(1);
    const mesh = meshes[0].instance as Mesh;
    expect(mesh.geometry.getAttribute("position").count).toBe(12);
    expect(mesh.geometry.getIndex()?.count).toBe(2 * 3 * 6);
    expect(mesh.geometry.getAttribute("color")).toBeUndefined();
    expect((mesh.material as MeshStandardMaterial).vertexColors).toBe(false);
    await renderer.unmount();
  });

  it("rebuilds the geometry when the grid changes", async () => {
    const small = makeGrid(2, 2, 1, [0, 0, 0, 0]);
    const large = makeGrid(4, 4, 1, new Array(16).fill(0));
    const renderer = await ReactThreeTestRenderer.create(<TerrainSurface grid={small} />);
    const first = renderer.scene.findByType("Mesh").instance as Mesh;
    expect(first.geometry.getAttribute("position").count).toBe(4);

    await renderer.update(<TerrainSurface grid={large} />);
    const second = renderer.scene.findByType("Mesh").instance as Mesh;
    expect(second.geometry.getAttribute("position").count).toBe(16);
    await renderer.unmount();
  });

  it("colours vertices by moisture over capacity and turns vertex colours on", async () => {
    const grid = makeGrid(2, 2, 1, [0, 0, 0, 0], [100, 100, 100, 100]);
    const moisture = Float32Array.from([0, 50, 100, 100]);
    const renderer = await ReactThreeTestRenderer.create(<TerrainSurface grid={grid} moisture={moisture} />);
    const mesh = renderer.scene.findByType("Mesh").instance as Mesh;
    const colour = mesh.geometry.getAttribute("color");
    expect(colour.count).toBe(4);
    expect(colour.getX(2)).toBeLessThan(colour.getX(0));
    expect(colour.getX(1)).toBeLessThan(colour.getX(0));
    expect(colour.getX(1)).toBeGreaterThan(colour.getX(2));
    expect((mesh.material as MeshStandardMaterial).vertexColors).toBe(true);

    await renderer.update(<TerrainSurface grid={grid} />);
    const after = renderer.scene.findByType("Mesh").instance as Mesh;
    expect(after.geometry.getAttribute("color")).toBeUndefined();
    await renderer.unmount();
  });
});
