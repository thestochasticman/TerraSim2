"use client";

import { RetentionChart } from "@/c/RetentionChart";
import { useRetentionCurves } from "@/h/useRetentionCurves";
import styles from "./RetentionViewer.module.css";

/** Fetch the book's retention curves and show them, with a status line until they arrive. */
export function RetentionViewer() {
  const { loading, data, error } = useRetentionCurves();
  return (
    <div className={styles.viewer}>
      <h1 className={styles.title}>Soil water retention by texture</h1>
      <p className={styles.caption}>
        Water content against suction for the twelve USDA textures, from tables 5.3 and 5.4 of <i>Soil Physics with Python</i>. Field capacity is read at 33 J/kg and wilting point at 1500 J/kg; the bars are the water a metre of each soil holds between them, which is
        what a cell&apos;s capacity will come from.
      </p>
      {loading && (
        <p role="status" className={styles.message}>
          Loading curves…
        </p>
      )}
      {error && (
        <p role="alert" className={styles.message}>
          Could not load curves: {error}
        </p>
      )}
      {data && <RetentionChart data={data} />}
    </div>
  );
}
