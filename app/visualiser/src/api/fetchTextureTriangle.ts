import { parseTextureTriangle } from "@/f/parseTextureTriangle";
import type { TextureTriangle } from "@/t/TextureTriangle";

/** GET /api/soils/texture: the USDA texture triangle on a grid, classified, with the book's size estimates. */
export async function fetchTextureTriangle(): Promise<TextureTriangle> {
  const response = await fetch("/api/soils/texture");
  if (!response.ok) throw new Error(`GET /api/soils/texture failed with status ${response.status}`);
  return parseTextureTriangle(await response.json());
}
