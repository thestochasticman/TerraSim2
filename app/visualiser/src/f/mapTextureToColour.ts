import { mapMoistureToColour } from "@/f/mapMoistureToColour";
import type { ColourScheme } from "@/t/ColourScheme";

/**
 * Where on the ramp the coarsest and finest textures sit, per surface. On a
 * light surface the ramp runs light (sand) to dark (clay). On a dark surface
 * the darkest steps vanish, so it runs mid blue (sand) to the lightest step
 * (clay): on either surface the finer the texture, the further its colour
 * stands from the background.
 */
const RANGES: Record<ColourScheme, [number, number]> = { light: [0.15, 1], dark: [0.6, 0] };

/**
 * Colour for a texture by its place in the coarse-to-fine order, as a CSS rgb() string.
 *
 * index : dimensionless, 0 for the coarsest
 * count : dimensionless, how many textures there are
 * scheme : the surface the colour will sit on
 *
 * Uses the same sequential blue ramp as moisture, so fineness reads as a
 * magnitude rather than a category.
 */
export function mapTextureToColour(index: number, count: number, scheme: ColourScheme = "light"): string {
  const [from, to] = RANGES[scheme];
  const position = count > 1 ? index / (count - 1) : 1;
  const [r, g, b] = mapMoistureToColour(from + (to - from) * position).map((c) => Math.round(c * 255));
  return `rgb(${r}, ${g}, ${b})`;
}
