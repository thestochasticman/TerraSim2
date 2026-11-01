"use client";

import { useState } from "react";
import { MODEL_LABELS } from "@/c/RetentionChart";
import { SoilColumnChart } from "@/c/SoilColumnChart";
import { useSoilColumn } from "@/h/useSoilColumn";
import { CURVE_MODELS } from "@/t/CurveModel";
import type { CurveModel } from "@/t/CurveModel";
import styles from "./SoilColumnViewer.module.css";

/** The twelve classes in the service's order, for the layer pickers. */
export const TEXTURES = ["sand", "loamy sand", "sandy loam", "silt loam", "loam", "silt", "sandy clay loam", "silty clay loam", "clay loam", "sandy clay", "silty clay", "clay"];

/** The six layers of the service's column, top first, as "0–5 cm" labels. */
const LAYER_LABELS = ["0–5 cm", "5–15 cm", "15–30 cm", "30–60 cm", "60–100 cm", "100–200 cm"];

/** A sand-over-clay profile to start from: the case where depth matters most. */
const INITIAL_TEXTURES = ["sand", "sand", "sandy loam", "clay loam", "clay", "clay"];

/**
 * Pick a texture for each of the six layers, a root depth and a model, and
 * see the column's available water build up layer by layer.
 */
export function SoilColumnViewer() {
  const [textures, setTextures] = useState<string[]>(INITIAL_TEXTURES);
  const [rootDepth, setRootDepth] = useState(0.6);
  const [model, setModel] = useState<CurveModel>("campbell");
  const { data, error } = useSoilColumn(textures, rootDepth, model);

  const setLayer = (i: number, texture: string) => setTextures((prev) => prev.map((t, k) => (k === i ? texture : t)));

  return (
    <div className={styles.viewer}>
      <h1 className={styles.title}>Soil column</h1>
      <p className={styles.caption}>
        A cell&apos;s capacity is the water its soil holds between wilting point and field capacity down to the roots, layer by layer. Pick a texture for each of the six depth intervals the Soil and Landscape Grid of Australia reports, slide the root depth, and read the total.
      </p>
      <div className={styles.controls}>
        <div className={styles.layers}>
          {LAYER_LABELS.map((label, i) => (
            <label key={label}>
              <span>{label}</span>
              <select value={textures[i]} onChange={(e) => setLayer(i, e.target.value)} aria-label={`texture ${label}`}>
                {TEXTURES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
        <label className={styles.depth}>
          <span>root depth, {rootDepth.toFixed(2)} m</span>
          <input type="range" min={0.05} max={2} step={0.05} value={rootDepth} onChange={(e) => setRootDepth(Number(e.target.value))} aria-label="root depth" />
        </label>
        <fieldset className={styles.models}>
          <legend>model</legend>
          {CURVE_MODELS.map((m) => (
            <label key={m}>
              <input type="radio" name="column-model" value={m} checked={model === m} onChange={() => setModel(m)} />
              {MODEL_LABELS[m]}
            </label>
          ))}
        </fieldset>
      </div>
      {error && (
        <p role="alert" className={styles.message}>
          Could not load column: {error}
        </p>
      )}
      {data === null && !error && (
        <p role="status" className={styles.message}>
          Loading column…
        </p>
      )}
      {data && <SoilColumnChart column={data} />}
    </div>
  );
}
