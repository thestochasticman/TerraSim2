"use client";

import { TextureTriangle } from "@/c/TextureTriangle";
import { useTextureTriangle } from "@/h/useTextureTriangle";
import styles from "./TextureTriangleViewer.module.css";

/** Fetch the classified texture triangle and show it, with a status line until it arrives. */
export function TextureTriangleViewer() {
  const { loading, data, error } = useTextureTriangle();
  return (
    <div className={styles.viewer}>
      <h1 className={styles.title}>Texture triangle</h1>
      <p className={styles.caption}>
        Every composition on a one-percent grid, classified by the USDA rules. Colour is the same fineness ramp as the retention curves. The reading gives the geometric mean particle diameter of equation 2.36 and the Campbell air entry and b that equations 5.36 and 5.37 estimate from it, the
        continuous route from measured fractions to a curve.
      </p>
      {loading && (
        <p role="status" className={styles.message}>
          Loading triangle…
        </p>
      )}
      {error && (
        <p role="alert" className={styles.message}>
          Could not load triangle: {error}
        </p>
      )}
      {data && <TextureTriangle data={data} />}
    </div>
  );
}
