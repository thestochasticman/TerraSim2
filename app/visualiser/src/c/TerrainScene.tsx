"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useMemo } from "react";
import { BucketColumns } from "@/c/BucketColumns";
import { ObservationMarkers } from "@/c/ObservationMarkers";
import { TerrainSurface } from "@/c/TerrainSurface";
import { frameTerrainCamera } from "@/f/frameTerrainCamera";
import type { BucketSet } from "@/t/BucketSet";
import type { ColourBy } from "@/t/ColourBy";
import type { MarkerSet } from "@/t/MarkerSet";
import type { TerrainGrid } from "@/t/TerrainGrid";

export type TerrainSceneProps = {
  grid: TerrainGrid;
  /** One day's moisture per cell, mm. When given, the surface is coloured by fullness. */
  moisture?: Float32Array;
  /** What the surface colour encodes; passed to TerrainSurface. */
  colourBy?: ColourBy;
  /** What moisture is a fraction of, per cell, mm; passed to TerrainSurface. */
  fullCapacity?: Float64Array;
  /** Observation markers to draw above the surface, if any. */
  markers?: MarkerSet;
  /** Soil columns to hang under the surface, if any; the surface goes translucent over them. */
  buckets?: BucketSet;
};

/** The surface's opacity while bucket columns are shown under it. */
export const SURFACE_OPACITY_OVER_BUCKETS = 0.35;

/**
 * A full 3D scene for one terrain: canvas, camera framed to the grid,
 * lights, the surface, and orbit controls around the grid centre. With
 * bucket columns the surface is drawn translucent so the columns show through.
 *
 * Needs a browser with WebGL. Load it only on the client.
 */
export function TerrainScene({ grid, moisture, colourBy, fullCapacity, markers, buckets }: TerrainSceneProps) {
  const frame = useMemo(() => frameTerrainCamera(grid), [grid]);
  const lightDistance = frame.far / 10;
  const withBuckets = buckets !== undefined && buckets.count > 0;

  return (
    <Canvas camera={{ position: frame.position, near: frame.near, far: frame.far, fov: 50 }}>
      <ambientLight intensity={0.5} />
      <directionalLight position={[lightDistance, lightDistance, lightDistance / 2]} intensity={1.2} />
      <TerrainSurface grid={grid} moisture={moisture} colourBy={colourBy} fullCapacity={fullCapacity} opacity={withBuckets ? SURFACE_OPACITY_OVER_BUCKETS : 1} />
      {markers && markers.count > 0 && <ObservationMarkers markers={markers} />}
      {withBuckets && <BucketColumns buckets={buckets} />}
      <OrbitControls target={frame.target} />
    </Canvas>
  );
}
