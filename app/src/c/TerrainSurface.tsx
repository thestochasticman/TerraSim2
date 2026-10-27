"use client";

import { useEffect, useMemo } from "react";
import { DoubleSide } from "three";
import { createTerrainGeometry } from "@/f/createTerrainGeometry";
import type { TerrainGrid } from "@/t/TerrainGrid";

export type TerrainSurfaceProps = {
  grid: TerrainGrid;
};

/**
 * The terrain as a lit mesh. Must be rendered inside a react-three-fiber Canvas.
 *
 * Rebuilds its geometry when grid changes and disposes the old one.
 */
export function TerrainSurface({ grid }: TerrainSurfaceProps) {
  const geometry = useMemo(() => createTerrainGeometry(grid), [grid]);

  useEffect(() => {
    return () => geometry.dispose();
  }, [geometry]);

  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color="#8c9a62" side={DoubleSide} />
    </mesh>
  );
}
