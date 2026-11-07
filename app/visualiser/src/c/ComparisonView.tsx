"use client";

import { ComparisonTable, formatScore } from "@/c/ComparisonTable";
import { ScatterChart } from "@/c/ScatterChart";
import type { RunComparison } from "@/t/RunComparison";
import type { RunPairs } from "@/t/RunPairs";
import styles from "./ComparisonView.module.css";

export type ComparisonViewProps = {
  comparison: RunComparison;
  pairs: RunPairs;
  /** The day on screen. */
  day: number | null;
  /** ISO dates by day index. */
  dates: string[];
  /** Called with a day index to show it. */
  onSeek?: (day: number) => void;
};

/**
 * How the run compares with the site's observations: a line saying what
 * was observed and how the run is read, the whole-run scores, then the
 * table by survey beside the modelled-against-observed scatter.
 */
export function ComparisonView({ comparison, pairs, day, dates, onSeek }: ComparisonViewProps) {
  const layers = comparison.layers.map((l) => `${l.top}–${l.bottom} m`).join(", ");
  const o = comparison.overall;
  const headline: [string, string][] = [
    ["bias", formatScore(o.bias, 3)],
    ["rmse", formatScore(o.rmse, 3)],
    ["ubrmse", formatScore(o.ubrmse, 3)],
    ["r", formatScore(o.r, 2)],
    ["NSE", formatScore(o.nse, 2)],
    ["KGE", formatScore(o.kge, 2)],
  ];
  return (
    <section className={styles.view} aria-label="comparison with observations">
      <p className={styles.caption}>
        {comparison.nPaired} of {comparison.nPoints} observations paired, measured over {layers} at {comparison.stations.length} stations; the run is read as a content over its root depth{comparison.rootDepth !== null ? ` of ${comparison.rootDepth} m` : ", which varies by cell"}, m³/m³.
      </p>
      <dl className={styles.headline} data-testid="headline">
        {headline.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <div className={styles.panels}>
        <ComparisonTable comparison={comparison} day={day} onSeek={onSeek} />
        <ScatterChart pairs={pairs} day={day} stations={comparison.stations} dates={dates} />
      </div>
    </section>
  );
}
