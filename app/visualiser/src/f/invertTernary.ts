import { TRIANGLE_HEIGHT } from "@/f/projectTernary";

/**
 * The composition at a point of the unit triangle: the inverse of projectTernary.
 *
 * x, y : dimensionless, in the triangle's own coordinates, y up
 *
 * Returns {sand, silt, clay} fractions summing to one. A point outside the
 * triangle gives a negative fraction; callers decide what to do with it.
 */
export function invertTernary(x: number, y: number): { sand: number; silt: number; clay: number } {
  const clay = y / TRIANGLE_HEIGHT;
  const silt = x - clay / 2;
  return { sand: 1 - silt - clay, silt, clay };
}
