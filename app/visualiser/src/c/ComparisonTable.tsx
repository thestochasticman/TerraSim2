"use client";

import type { RunComparison } from "@/t/RunComparison";
import type { Scores } from "@/t/Scores";
import styles from "./ComparisonTable.module.css";

export type ComparisonTableProps = {
  comparison: RunComparison;
  /** The day on screen; its survey's row is highlighted. */
  day: number | null;
  /** Called with a survey's day index when its row is clicked. */
  onSeek?: (day: number) => void;
};

/** A score for the table: fixed decimals, or a dash for null. */
export function formatScore(value: number | null, decimals: number): string {
  return value === null ? "–" : value.toFixed(decimals);
}

const COLUMNS: { key: keyof Scores; label: string; decimals: number }[] = [
  { key: "n", label: "n", decimals: 0 },
  { key: "observedMean", label: "observed", decimals: 3 },
  { key: "modelledMean", label: "modelled", decimals: 3 },
  { key: "bias", label: "bias", decimals: 3 },
  { key: "rmse", label: "rmse", decimals: 3 },
  { key: "r", label: "r", decimals: 2 },
];

/**
 * The run's scores against the observations, one row per survey date with
 * the whole run above them, contents in m³/m³. The row of the day on
 * screen is highlighted; clicking a row seeks the scrubber to that survey.
 */
export function ComparisonTable({ comparison, day, onSeek }: ComparisonTableProps) {
  const cells = (scores: Scores) => COLUMNS.map((c) => <td key={c.key}>{formatScore(scores[c.key], c.decimals)}</td>);
  return (
    <div className={styles.scroll}>
      <table className={styles.table} aria-label="scores by survey">
        <thead>
          <tr>
            <th>survey</th>
            {COLUMNS.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr className={styles.overall} data-testid="overall">
            <td>all days</td>
            {cells(comparison.overall)}
          </tr>
          {comparison.byDate.map((row) => (
            <tr key={row.date} data-highlighted={row.t !== null && row.t === day} data-t={row.t ?? ""} className={onSeek && row.t !== null ? styles.seekable : undefined} onClick={() => onSeek && row.t !== null && onSeek(row.t)}>
              <td>{row.date}</td>
              {cells(row)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
