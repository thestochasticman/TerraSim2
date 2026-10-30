/**
 * Vertex positions and triangle indices for a terrain surface.
 *
 * positions : Float32Array of length rows * cols * 3, metres (m)
 *     One vertex per cell, in row-major cell order, as (x, y, z) triples.
 *     x runs along columns, z runs along rows, y is elevation. Three.js
 *     convention, y up. The cell at row 0, col 0 sits at x = 0, z = 0.
 * indices : Uint32Array of length (rows - 1) * (cols - 1) * 6, dimensionless
 *     Two triangles per quad of neighbouring cells, wound counter-clockwise
 *     when seen from above (+y), so face normals point up.
 */
export type TerrainMesh = {
  positions: Float32Array;
  indices: Uint32Array;
};
