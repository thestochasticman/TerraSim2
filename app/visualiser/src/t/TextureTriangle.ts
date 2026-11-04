/**
 * The USDA texture triangle sampled on a grid, as GET /api/soils/texture returns it.
 *
 * textures : the twelve classes, coarsest first; point classes index into it
 * step : grid spacing, percent
 * points : one entry per composition, as columns; sand, silt and clay in
 *     percent, texture an index into textures, diameter the geometric mean
 *     particle diameter in micrometres, psiE the estimated air entry in
 *     J/kg and b the estimated Campbell exponent
 * typical : table 2.4's typical composition of each class, percent, with its diameter
 */
export type TextureTriangle = {
  textures: string[];
  step: number;
  points: {
    sand: number[];
    silt: number[];
    clay: number[];
    texture: number[];
    diameter: number[];
    psiE: number[];
    b: number[];
  };
  typical: { texture: string; sand: number; silt: number; clay: number; diameter: number }[];
};
