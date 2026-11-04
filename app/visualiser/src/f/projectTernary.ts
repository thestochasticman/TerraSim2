/** Height of a unit equilateral triangle, sqrt(3) / 2. */
export const TRIANGLE_HEIGHT = Math.sqrt(3) / 2;

/**
 * Place a composition in a unit equilateral triangle.
 *
 * sand, silt, clay : dimensionless fractions summing to one
 *
 * Returns {x, y} with all sand at (0, 0), all silt at (1, 0) and all clay
 * at the apex (0.5, TRIANGLE_HEIGHT): the USDA triangle's layout, y up.
 */
export function projectTernary(sand: number, silt: number, clay: number): { x: number; y: number } {
  void sand;
  return { x: silt + clay / 2, y: clay * TRIANGLE_HEIGHT };
}
