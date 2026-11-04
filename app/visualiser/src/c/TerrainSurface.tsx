"use client";

import { useEffect, useMemo } from "react";
import { BufferAttribute, DoubleSide } from "three";
import { computeCapacityColours } from "@/f/computeCapacityColours";
import { computeVertexColours } from "@/f/computeVertexColours";
import { createTerrainGeometry } from "@/f/createTerrainGeometry";
import { createUniformColours } from "@/f/createUniformColours";
import type { ColourBy } from "@/t/ColourBy";
import type { TerrainGrid } from "@/t/TerrainGrid";

export type TerrainSurfaceProps = {
  grid: TerrainGrid;
  /** One day's moisture per cell, mm. When given, the surface is coloured by fullness. */
  moisture?: Float32Array;
  /** "capacity" colours by the grid's capacity instead, when the grid has one. Default "moisture". */
  colourBy?: ColourBy;
};

/** The surface's colour when there is nothing to colour by: an earth tone, RGB in 0..1. */
export const EARTH_TONE: [number, number, number] = [0x8c / 255, 0x9a / 255, 0x62 / 255];

/**
 * The terrain as a lit mesh. Must be rendered inside a react-three-fiber Canvas.
 *
 * Rebuilds its geometry when grid changes and disposes the old one. The
 * mesh always carries a colour per vertex, so the material never switches
 * modes: when moisture is given, each vertex takes the sequential moisture
 * colour for its cell; with colourBy "capacity" and a grid that has
 * capacity, the capacity colour instead; otherwise the earth tone.
 * Switching the material's vertex colours on after it has drawn would need
 * a shader recompile that nothing triggers, and the surface would show its
 * white base colour; a constant mode avoids that.
 */
export function TerrainSurface({ grid, moisture, colourBy = "moisture" }: TerrainSurfaceProps) {
  const geometry = useMemo(() => {
    const g = createTerrainGeometry(grid);
    g.setAttribute("color", new BufferAttribute(createUniformColours(grid.rows * grid.cols, EARTH_TONE), 3));
    return g;
  }, [grid]);

  useEffect(() => {
    return () => geometry.dispose();
  }, [geometry]);

  // Moisture from another grid (a stale day after a site switch) is ignored rather than drawn or thrown on.
  const byCapacity = colourBy === "capacity" && grid.capacity !== undefined;
  const byMoisture = !byCapacity && moisture !== undefined && moisture.length === grid.rows * grid.cols;

  useEffect(() => {
    const colours = byCapacity && grid.capacity ? computeCapacityColours(grid.capacity) : byMoisture && moisture ? computeVertexColours(moisture, grid.capacity) : createUniformColours(grid.rows * grid.cols, EARTH_TONE);
    const attribute = geometry.getAttribute("color") as BufferAttribute;
    (attribute.array as Float32Array).set(colours);
    attribute.needsUpdate = true;
  }, [geometry, grid, moisture, byCapacity, byMoisture]);

  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color="#ffffff" vertexColors side={DoubleSide} />
    </mesh>
  );
}
