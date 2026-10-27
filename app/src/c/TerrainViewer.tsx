"use client";

import dynamic from "next/dynamic";
import { useTerrainGrid } from "@/h/useTerrainGrid";
import styles from "./TerrainViewer.module.css";

const TerrainScene = dynamic(() => import("@/c/TerrainScene").then((m) => m.TerrainScene), {
  ssr: false,
  loading: () => <p className={styles.message}>Loading viewer…</p>,
});

export type TerrainViewerProps = {
  url: string;
};

/**
 * Fetch a terrain file and show it in a 3D scene.
 *
 * Shows a status line while the file loads, an error line if it cannot be
 * loaded or parsed, and the scene once the grid is ready. The scene itself
 * is loaded only in the browser, since it needs WebGL.
 */
export function TerrainViewer({ url }: TerrainViewerProps) {
  const { loading, grid, error } = useTerrainGrid(url);

  if (loading) {
    return (
      <p role="status" className={styles.message}>
        Loading terrain…
      </p>
    );
  }
  if (error) {
    return (
      <p role="alert" className={styles.message}>
        Could not load terrain: {error}
      </p>
    );
  }
  if (!grid) return null;

  return (
    <div className={styles.viewer}>
      <TerrainScene grid={grid} />
    </div>
  );
}
