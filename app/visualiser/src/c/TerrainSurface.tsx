"use client";

import { useEffect, useMemo } from "react";
import { BufferAttribute, DoubleSide } from "three";
import { computeVertexColours } from "@/f/computeVertexColours";
import { createTerrainGeometry } from "@/f/createTerrainGeometry";
import type { TerrainGrid } from "@/t/TerrainGrid";

export type TerrainSurfaceProps = {
  grid: TerrainGrid;
  /** One day's moisture per cell, mm. When given, the surface is coloured by fullness. */
  moisture?: Float32Array;
};

/**
 * The terrain as a lit mesh. Must be rendered inside a react-three-fiber Canvas.
 *
 * Rebuilds its geometry when grid changes and disposes the old one. When
 * moisture is given, each vertex takes the sequential moisture colour for
 * its cell; otherwise the surface is a single earth tone.
 */
export function TerrainSurface({ grid, moisture }: TerrainSurfaceProps) {
  const geometry = useMemo(() => createTerrainGeometry(grid), [grid]);

  useEffect(() => {
    return () => geometry.dispose();
  }, [geometry]);

  useEffect(() => {
    if (moisture === undefined) {
      geometry.deleteAttribute("color");
      return;
    }
    geometry.setAttribute("color", new BufferAttribute(computeVertexColours(moisture, grid.capacity), 3));
  }, [geometry, grid, moisture]);

  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color={moisture === undefined ? "#8c9a62" : "#ffffff"} vertexColors={moisture !== undefined} side={DoubleSide} />
    </mesh>
  );
}
