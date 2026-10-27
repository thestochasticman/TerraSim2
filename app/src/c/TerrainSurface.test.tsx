import ReactThreeTestRenderer from "@react-three/test-renderer";
import type { Mesh } from "three";
import { describe, expect, it } from "vitest";
import { TerrainSurface } from "./TerrainSurface";
import type { TerrainGrid } from "@/t/TerrainGrid";

function makeGrid(rows: number, cols: number, cellSize: number, elevation: number[]): TerrainGrid {
  return { rows, cols, cellSize, elevation: Float64Array.from(elevation) };
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
});
