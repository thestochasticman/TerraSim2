"use client";

import { useLayoutEffect, useRef } from "react";
import { Color, InstancedMesh, Matrix4 } from "three";
import type { MarkerSet } from "@/t/MarkerSet";

export type ObservationMarkersProps = {
  markers: MarkerSet;
};

/**
 * One sphere per observation, drawn as a single instanced mesh above the
 * terrain. Must sit inside a Canvas. Each instance takes its position and
 * colour from the MarkerSet; a set with a different count remounts the
 * mesh, since an instanced mesh cannot grow.
 */
export function ObservationMarkers({ markers }: ObservationMarkersProps) {
  const ref = useRef<InstancedMesh>(null);

  useLayoutEffect(() => {
    const mesh = ref.current;
    if (!mesh) return;
    const matrix = new Matrix4();
    const colour = new Color();
    for (let i = 0; i < markers.count; i++) {
      matrix.makeTranslation(markers.positions[i * 3], markers.positions[i * 3 + 1], markers.positions[i * 3 + 2]);
      mesh.setMatrixAt(i, matrix);
      mesh.setColorAt(i, colour.setRGB(markers.colours[i * 3], markers.colours[i * 3 + 1], markers.colours[i * 3 + 2]));
    }
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  }, [markers]);

  return (
    <instancedMesh key={markers.count} ref={ref} args={[undefined, undefined, markers.count]} frustumCulled={false}>
      <sphereGeometry args={[markers.radius, 12, 8]} />
      <meshStandardMaterial />
    </instancedMesh>
  );
}
