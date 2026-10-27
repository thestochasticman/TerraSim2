"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useMemo } from "react";
import { TerrainSurface } from "@/c/TerrainSurface";
import { frameTerrainCamera } from "@/f/frameTerrainCamera";
import type { TerrainGrid } from "@/t/TerrainGrid";

export type TerrainSceneProps = {
  grid: TerrainGrid;
};

/**
 * A full 3D scene for one terrain: canvas, camera framed to the grid,
 * lights, the surface, and orbit controls around the grid centre.
 *
 * Needs a browser with WebGL. Load it only on the client.
 */
export function TerrainScene({ grid }: TerrainSceneProps) {
  const frame = useMemo(() => frameTerrainCamera(grid), [grid]);
  const lightDistance = frame.far / 10;

  return (
    <Canvas camera={{ position: frame.position, near: frame.near, far: frame.far, fov: 50 }}>
      <ambientLight intensity={0.5} />
      <directionalLight position={[lightDistance, lightDistance, lightDistance / 2]} intensity={1.2} />
      <TerrainSurface grid={grid} />
      <OrbitControls target={frame.target} />
    </Canvas>
  );
}
