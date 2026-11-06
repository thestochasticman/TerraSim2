import ReactThreeTestRenderer from "@react-three/test-renderer";
import type { Mesh, MeshStandardMaterial } from "three";
import { describe, expect, it } from "vitest";
import { EARTH_TONE, TerrainSurface } from "./TerrainSurface";
import type { TerrainGrid } from "@/t/TerrainGrid";

function makeGrid(rows: number, cols: number, cellSize: number, elevation: number[], capacity?: number[]): TerrainGrid {
  const grid: TerrainGrid = { rows, cols, cellSize, elevation: Float64Array.from(elevation) };
  if (capacity) grid.capacity = Float64Array.from(capacity);
  return grid;
}

/** Whether every vertex of the mesh carries the earth tone. */
function isEarthToned(mesh: Mesh): boolean {
  const colour = mesh.geometry.getAttribute("color");
  const [r, g, b] = Float32Array.from(EARTH_TONE);
  for (let i = 0; i < colour.count; i++) if (colour.getX(i) !== r || colour.getY(i) !== g || colour.getZ(i) !== b) return false;
  return colour.count > 0;
}

describe("TerrainSurface", () => {
  it("mounts one mesh whose geometry has a vertex per cell, earth-toned, with vertex colours always on", async () => {
    const grid = makeGrid(3, 4, 1, new Array(12).fill(0));
    const renderer = await ReactThreeTestRenderer.create(<TerrainSurface grid={grid} />);
    const meshes = renderer.scene.findAllByType("Mesh");
    expect(meshes).toHaveLength(1);
    const mesh = meshes[0].instance as Mesh;
    expect(mesh.geometry.getAttribute("position").count).toBe(12);
    expect(mesh.geometry.getIndex()?.count).toBe(2 * 3 * 6);
    expect(mesh.geometry.getAttribute("color").count).toBe(12);
    expect(isEarthToned(mesh)).toBe(true);
    expect((mesh.material as MeshStandardMaterial).vertexColors).toBe(true);
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

  it("colours vertices by moisture over capacity, and returns to the earth tone when moisture goes", async () => {
    const grid = makeGrid(2, 2, 1, [0, 0, 0, 0], [100, 100, 100, 100]);
    const moisture = Float32Array.from([0, 50, 100, 100]);
    const renderer = await ReactThreeTestRenderer.create(<TerrainSurface grid={grid} moisture={moisture} />);
    const mesh = renderer.scene.findByType("Mesh").instance as Mesh;
    const colour = mesh.geometry.getAttribute("color");
    expect(colour.count).toBe(4);
    expect(colour.getX(2)).toBeLessThan(colour.getX(0));
    expect(colour.getX(1)).toBeLessThan(colour.getX(0));
    expect(colour.getX(1)).toBeGreaterThan(colour.getX(2));
    expect(isEarthToned(mesh)).toBe(false);
    expect((mesh.material as MeshStandardMaterial).vertexColors).toBe(true);

    await renderer.update(<TerrainSurface grid={grid} />);
    const after = renderer.scene.findByType("Mesh").instance as Mesh;
    expect(isEarthToned(after)).toBe(true);
    expect((after.material as MeshStandardMaterial).vertexColors).toBe(true);
    await renderer.unmount();
  });

  it("a mesh mounted bare takes the moisture colour when a day arrives later, on the same material", async () => {
    const grid = makeGrid(2, 2, 1, [0, 0, 0, 0], [100, 100, 100, 100]);
    const renderer = await ReactThreeTestRenderer.create(<TerrainSurface grid={grid} />);
    const before = renderer.scene.findByType("Mesh").instance as Mesh;
    const material = before.material as MeshStandardMaterial;
    expect(isEarthToned(before)).toBe(true);
    await renderer.update(<TerrainSurface grid={grid} moisture={Float32Array.from([0, 50, 100, 100])} />);
    const after = renderer.scene.findByType("Mesh").instance as Mesh;
    expect(isEarthToned(after)).toBe(false);
    expect(after.material).toBe(material);
    expect(material.vertexColors).toBe(true);
    await renderer.unmount();
  });

  it("colours by capacity when asked, regardless of moisture, and falls back without a capacity", async () => {
    const grid = makeGrid(2, 2, 1, [0, 0, 0, 0], [10, 20, 40, 80]);
    const moisture = Float32Array.from([80, 80, 80, 80]);
    const renderer = await ReactThreeTestRenderer.create(<TerrainSurface grid={grid} moisture={moisture} colourBy="capacity" />);
    const mesh = renderer.scene.findByType("Mesh").instance as Mesh;
    const colour = mesh.geometry.getAttribute("color");
    expect(colour.getX(0)).toBeGreaterThan(colour.getX(1));
    expect(colour.getX(1)).toBeGreaterThan(colour.getX(3));
    expect((mesh.material as MeshStandardMaterial).vertexColors).toBe(true);

    const bare = makeGrid(2, 2, 1, [0, 0, 0, 0]);
    await renderer.update(<TerrainSurface grid={bare} colourBy="capacity" />);
    const after = renderer.scene.findByType("Mesh").instance as Mesh;
    expect(isEarthToned(after)).toBe(true);
    await renderer.unmount();
  });

  it("fullness divides by the given full capacity when one is passed", async () => {
    const grid = makeGrid(2, 2, 1, [0, 0, 0, 0], [50, 50, 50, 50]);
    const moisture = Float32Array.from([50, 100, 100, 100]);
    const renderer = await ReactThreeTestRenderer.create(<TerrainSurface grid={grid} moisture={moisture} fullCapacity={Float64Array.from([100, 100, 100, 100])} />);
    const colour = (renderer.scene.findByType("Mesh").instance as Mesh).geometry.getAttribute("color");
    expect(colour.getX(0)).toBeGreaterThan(colour.getX(1) + 0.1);
    await renderer.update(<TerrainSurface grid={grid} moisture={moisture} />);
    const clamped = (renderer.scene.findByType("Mesh").instance as Mesh).geometry.getAttribute("color");
    expect(Math.abs(clamped.getX(0) - clamped.getX(1))).toBeLessThan(1e-6);
    await renderer.unmount();
  });

  it("the relative mode stretches a day's small spread over the whole ramp", async () => {
    const grid = makeGrid(2, 2, 1, [0, 0, 0, 0], [100, 100, 100, 100]);
    const moisture = Float32Array.from([50, 50.5, 51, 52]);
    const renderer = await ReactThreeTestRenderer.create(<TerrainSurface grid={grid} moisture={moisture} colourBy="relative" />);
    const colour = (renderer.scene.findByType("Mesh").instance as Mesh).geometry.getAttribute("color");
    expect(colour.getX(0)).toBeGreaterThan(colour.getX(3) + 0.5);
    await renderer.update(<TerrainSurface grid={grid} moisture={moisture} colourBy="moisture" />);
    const absolute = (renderer.scene.findByType("Mesh").instance as Mesh).geometry.getAttribute("color");
    expect(Math.abs(absolute.getX(0) - absolute.getX(3))).toBeLessThan(0.05);
    await renderer.unmount();
  });

  it("colours by upslope cells when asked: a ridge is lighter than the outlet", async () => {
    const grid: TerrainGrid = { ...makeGrid(2, 2, 1, [0, 0, 0, 0], [50, 50, 50, 50]), upslopeCells: Float64Array.from([1, 1, 2, 4]) };
    const renderer = await ReactThreeTestRenderer.create(<TerrainSurface grid={grid} moisture={Float32Array.from([50, 50, 50, 50])} colourBy="upslope" />);
    const mesh = renderer.scene.findByType("Mesh").instance as Mesh;
    const colour = mesh.geometry.getAttribute("color");
    expect(colour.getX(0)).toBeGreaterThan(colour.getX(2));
    expect(colour.getX(2)).toBeGreaterThan(colour.getX(3));
    await renderer.unmount();
  });

  it("ignores moisture whose length does not match the grid instead of throwing", async () => {
    const grid = makeGrid(2, 2, 1, [0, 0, 0, 0], [100, 100, 100, 100]);
    const renderer = await ReactThreeTestRenderer.create(<TerrainSurface grid={grid} moisture={new Float32Array(9)} />);
    const mesh = renderer.scene.findByType("Mesh").instance as Mesh;
    expect(isEarthToned(mesh)).toBe(true);
    expect((mesh.material as MeshStandardMaterial).vertexColors).toBe(true);
    await renderer.unmount();
  });
});
