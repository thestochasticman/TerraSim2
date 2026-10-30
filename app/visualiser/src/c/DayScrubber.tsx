"use client";

import styles from "./DayScrubber.module.css";

export type DayScrubberProps = {
  /** Days that can be shown so far, dimensionless. */
  daysAvailable: number;
  /** Total days in the run, dimensionless. */
  nDays: number;
  /** The day on screen. */
  day: number;
  /** ISO date of that day, or empty. */
  date: string;
  /** Whether the user may scrub and play. False while the run is still writing. */
  enabled: boolean;
  playing: boolean;
  onSeek: (day: number) => void;
  onTogglePlay: () => void;
};

/**
 * Play, pause, a day slider and the date. While disabled it reads as a
 * progress bar: the thumb sits on the newest day and nothing responds.
 */
export function DayScrubber({ daysAvailable, nDays, day, date, enabled, playing, onSeek, onTogglePlay }: DayScrubberProps) {
  const max = Math.max(0, daysAvailable - 1);
  return (
    <div className={styles.scrubber}>
      <button type="button" onClick={onTogglePlay} disabled={!enabled} aria-label={playing ? "pause" : "play"}>
        {playing ? "❚❚" : "▶"}
      </button>
      <input
        className={styles.slider}
        type="range"
        min={0}
        max={max}
        value={Math.min(day, max)}
        disabled={!enabled}
        aria-label="day"
        onChange={(e) => onSeek(Number(e.target.value))}
      />
      <span className={styles.date}>{date}</span>
      <span className={styles.count}>
        day {day + 1} of {nDays}
      </span>
    </div>
  );
}
