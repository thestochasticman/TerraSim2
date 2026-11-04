"use client";

import { useEffect, useMemo } from "react";
import { BufferAttribute, DoubleSide } from "three";
import { computeCapacityColours } from "@/f/computeCapacityColours";
import { computeVertexColours } from "@/f/computeVertexColours";
import { createTerrainGeometry } from "@/f/createTerrainGeometry";
import type { ColourBy } from "@/t/ColourBy";
import type { TerrainGrid } from "@/t/TerrainGrid";

export type TerrainSurfaceProps = {
  grid: TerrainGrid;
  /** One day's moisture per cell, mm. When given, the surface is coloured by fullness. */
  moisture?: Float32Array;
  /** "capacity" colours by the grid's capacity instead, when the grid has one. Default "moisture". */
  colourBy?: ColourBy;
};

/**
 * The terrain as a lit mesh. Must be rendered inside a react-three-fiber Canvas.
 *
 * Rebuilds its geometry when grid changes and disposes the old one. When
 * moisture is given, each vertex takes the sequential moisture colour for
 * its cell; with colourBy "capacity" and a grid that has capacity, the
 * capacity colour instead; otherwise the surface is a single earth tone.
 */
export function TerrainSurface({ grid, moisture, colourBy = "moisture" }: TerrainSurfaceProps) {
  const geometry = useMemo(() => createTerrainGeometry(grid), [grid]);

  useEffect(() => {
    return () => geometry.dispose();
  }, [geometry]);

  // Moisture from another grid (a stale day after a site switch) is ignored rather than drawn or thrown on.
  const byCapacity = colourBy === "capacity" && grid.capacity !== undefined;
  const byMoisture = !byCapacity && moisture !== undefined && moisture.length === grid.rows * grid.cols;
  const coloured = byCapacity || byMoisture;

  useEffect(() => {
    if (byCapacity && grid.capacity) {
      geometry.setAttribute("color", new BufferAttribute(computeCapacityColours(grid.capacity), 3));
    } else if (byMoisture && moisture) {
      geometry.setAttribute("color", new BufferAttribute(computeVertexColours(moisture, grid.capacity), 3));
    } else {
      geometry.deleteAttribute("color");
    }
  }, [geometry, grid, moisture, byCapacity, byMoisture]);

  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color={coloured ? "#ffffff" : "#8c9a62"} vertexColors={coloured} side={DoubleSide} />
    </mesh>
  );
}
