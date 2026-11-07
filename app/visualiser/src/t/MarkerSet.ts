/**
 * Points to draw above the terrain surface, one marker each.
 *
 * count : dimensionless
 * positions : Float32Array of length 3 count, metres (m), x, y (up), z per marker in the mesh's frame
 * colours : Float32Array of length 3 count, RGB in 0..1 per marker
 * radius : metres (m), the size of every marker
 */
export type MarkerSet = {
  count: number;
  positions: Float32Array;
  colours: Float32Array;
  radius: number;
};
