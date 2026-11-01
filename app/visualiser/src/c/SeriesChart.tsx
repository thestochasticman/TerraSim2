"use client";

import { Group } from "@visx/group";
import { useMemo, useRef, useState } from "react";
import { MARGIN, SeriesPanel, type BarGroup, type SeriesLine } from "@/c/SeriesPanel";
import { clampDayRange } from "@/f/clampDayRange";
import { computeChartExtent } from "@/f/computeChartExtent";
import { pickDay } from "@/f/pickDay";
import type { RunSeries } from "@/t/RunSeries";
import styles from "./SeriesChart.module.css";

/**
 * Fixed hue per series, dark-surface steps of the reference palette. Colour
 * follows the series, never its rank. Moisture shares the surface's blue;
 * rain takes violet so the two never look alike in the legend.
 */
export const SERIES_COLOURS = {
  moisture: "#3987e5",
  rain: "#9085e9",
  pet: "#d95926",
  evaporation: "#199e70",
  runoff: "#c98500",
} as const;

export type SeriesChartProps = {
  series: RunSeries;
  /** Day marked with the cursor, usually the scrubber's day. */
  day: number | null;
  /** Called when the user clicks a day. */
  onSeek?: (day: number) => void;
};

const VIEW_WIDTH = 1200;
const STORE_HEIGHT = 80;
const FLUX_HEIGHT = 120;
const GAP = 14;
/** A press that moves fewer days than this before release is a click, not a zoom. */
const CLICK_TOLERANCE_DAYS = 2;

/**
 * Two stacked panels sharing an x axis. Above, grid-mean stored water, a
 * level in mm, as a line. Below, the daily fluxes in mm per day as bars
 * from a zero line: rain upward, evaporation and runoff stacked downward,
 * with demand outlined behind evaporation as the ceiling it could have
 * reached. A vertical marker shows the scrubber's day; hovering previews
 * a day in the legend; clicking seeks to it.
 *
 * Zoom: drag across either panel to show just that span of days; double
 * click, or the reset button, to show the whole run again. While a run is
 * still writing and no zoom is set, the chart grows with it.
 */
export function SeriesChart({ series, day, onSeek }: SeriesChartProps) {
  const [hoverDay, setHoverDay] = useState<number | null>(null);
  const [zoom, setZoom] = useState<[number, number] | null>(null);
  const [selection, setSelection] = useState<[number, number] | null>(null);
  const pressDay = useRef<number | null>(null);
  const nDays = series.dates.length;
  const plotWidth = VIEW_WIDTH - MARGIN.left - MARGIN.right;
  const totalHeight = MARGIN.top + STORE_HEIGHT + GAP + FLUX_HEIGHT + MARGIN.bottom;
  const extent = useMemo(() => computeChartExtent(series), [series]);

  const full: [number, number] = [0, Math.max(0, nDays - 1)];
  const range: [number, number] = zoom && zoom[1] < nDays ? zoom : full;

  const moisture: SeriesLine = { key: "moisture", label: "stored", colour: SERIES_COLOURS.moisture, values: series.moisture };
  const rain: SeriesLine = { key: "rain", label: "rain", colour: SERIES_COLOURS.rain, values: series.rain };
  const demand: SeriesLine = { key: "pet", label: "demand", colour: SERIES_COLOURS.pet, values: series.pet };
  const losses: SeriesLine[] = [
    ...(series.evaporation ? [{ key: "evaporation", label: "evaporation", colour: SERIES_COLOURS.evaporation, values: series.evaporation }] : []),
    ...(series.runoff ? [{ key: "runoff", label: "runoff", colour: SERIES_COLOURS.runoff, values: series.runoff }] : []),
  ];
  const fluxGroups: BarGroup[] = [
    { direction: "up", stack: [rain] },
    { direction: "down", stack: losses, outline: demand },
  ];

  const shownDay = hoverDay ?? day;
  const legend: { item: SeriesLine; outline?: boolean }[] = [{ item: moisture }, { item: rain }, ...losses.map((item) => ({ item })), { item: demand, outline: true }];

  const dayFromEvent = (e: React.MouseEvent<SVGSVGElement>): number | null => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * VIEW_WIDTH - MARGIN.left;
    return pickDay(x, plotWidth, nDays, range);
  };
  const xOf = (d: number) => MARGIN.left + ((d - range[0]) / Math.max(1, range[1] - range[0])) * plotWidth;

  const onMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    if (e.button !== 0) return;
    pressDay.current = dayFromEvent(e);
  };
  const onMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const d = dayFromEvent(e);
    setHoverDay(d);
    if (pressDay.current !== null && d !== null && Math.abs(d - pressDay.current) >= CLICK_TOLERANCE_DAYS) {
      setSelection([Math.min(pressDay.current, d), Math.max(pressDay.current, d)]);
    }
  };
  const onMouseUp = (e: React.MouseEvent<SVGSVGElement>) => {
    const start = pressDay.current;
    pressDay.current = null;
    setSelection(null);
    const d = dayFromEvent(e);
    if (start === null || d === null) return;
    if (Math.abs(d - start) >= CLICK_TOLERANCE_DAYS) {
      setZoom(clampDayRange(start, d, nDays));
    } else if (onSeek) {
      onSeek(d);
    }
  };
  const onMouseLeave = () => {
    setHoverDay(null);
    pressDay.current = null;
    setSelection(null);
  };
  const reset = () => setZoom(null);

  return (
    <div className={styles.chart}>
      <svg
        className={styles.svg}
        viewBox={`0 0 ${VIEW_WIDTH} ${totalHeight}`}
        role="img"
        aria-label="daily series"
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseLeave}
        onDoubleClick={reset}
      >
        <Group left={MARGIN.left} top={MARGIN.top}>
          <SeriesPanel width={plotWidth} height={STORE_HEIGHT} range={range} yMin={0} yMax={extent.maxMoisture} lines={[moisture]} markerDay={shownDay} yLabel="stored mm" showXAxis={false} dates={series.dates} />
        </Group>
        <Group left={MARGIN.left} top={MARGIN.top + STORE_HEIGHT + GAP}>
          <SeriesPanel width={plotWidth} height={FLUX_HEIGHT} range={range} yMin={-extent.maxOut} yMax={extent.maxIn} lines={[]} barGroups={fluxGroups} markerDay={shownDay} yLabel="in ↑  mm / day  ↓ out" showXAxis dates={series.dates} />
        </Group>
        {selection && (
          <rect data-testid="selection" x={xOf(selection[0])} y={MARGIN.top} width={Math.max(1, xOf(selection[1]) - xOf(selection[0]))} height={STORE_HEIGHT + GAP + FLUX_HEIGHT} fill="currentColor" fillOpacity={0.12} />
        )}
      </svg>
      <ul className={styles.legend} aria-label="legend">
        {legend.map(({ item, outline }) => (
          <li key={item.key}>
            <span className={styles.swatch} style={outline ? { border: `1px solid ${item.colour}` } : { background: item.colour }} />
            {item.label}
            <span className={styles.value}>{shownDay !== null && item.values[shownDay] !== undefined ? item.values[shownDay].toFixed(1) : ""}</span>
          </li>
        ))}
        <li>{shownDay !== null ? series.dates[shownDay] ?? "" : ""}</li>
        {zoom && (
          <li>
            <button type="button" onClick={reset} aria-label="reset zoom">
              {series.dates[range[0]]} to {series.dates[range[1]]}, reset
            </button>
          </li>
        )}
      </ul>
    </div>
  );
}
