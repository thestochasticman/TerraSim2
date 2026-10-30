import { BufferAttribute, BufferGeometry } from "three";
import { buildTerrainMesh } from "@/f/buildTerrainMesh";
import type { TerrainGrid } from "@/t/TerrainGrid";

/**
 * Create a Three.js BufferGeometry for a terrain surface.
 *
 * Wraps buildTerrainMesh: positions become the "position" attribute,
 * indices become the index, and per-vertex normals are computed from
 * the triangles so lighting shades the slopes.
 *
 * grid : TerrainGrid
 *     Elevation and cellSize in metres (m).
 *
 * Returns a BufferGeometry in metres (m). The caller owns it and should
 * call dispose() when it is no longer rendered.
 */
export function createTerrainGeometry(grid: TerrainGrid): BufferGeometry {
  const { positions, indices } = buildTerrainMesh(grid);
  const geometry = new BufferGeometry();
  geometry.setAttribute("position", new BufferAttribute(positions, 3));
  geometry.setIndex(new BufferAttribute(indices, 1));
  geometry.computeVertexNormals();
  return geometry;
}
