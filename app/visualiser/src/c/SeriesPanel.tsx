"use client";

import { AxisBottom, AxisLeft } from "@visx/axis";
import { GridRows } from "@visx/grid";
import { Group } from "@visx/group";
import { scaleLinear } from "@visx/scale";
import { Bar, LinePath } from "@visx/shape";
import { useMemo } from "react";

export type SeriesLine = {
  key: string;
  label: string;
  colour: string;
  values: number[];
};

export type SeriesPanelProps = {
  /** Plot width in SVG units, excluding margins. */
  width: number;
  height: number;
  /** Days visible across the x axis, inclusive; the first sits at the left edge, the last at the right. */
  range: [number, number];
  /** Top of the y axis, millimetres (mm). */
  yMax: number;
  /** Lines to draw, in fixed order; values indexed by day. */
  lines: SeriesLine[];
  /** Optional bars, one per day, drawn behind the lines. */
  bars?: SeriesLine;
  /** Day to mark with a vertical cursor, if any; drawn only when inside the range. */
  markerDay: number | null;
  /** Axis title. */
  yLabel: string;
  /** Whether to draw the x axis (only the bottom panel does). */
  showXAxis: boolean;
  /** Tick labels for the x axis, indexed by day. */
  dates: string[];
};

export const MARGIN = { left: 48, right: 12, top: 8, bottom: 24 };

/**
 * One panel of the series chart: a y axis, grid rows, optional bars, lines,
 * and a vertical marker, showing only the days in `range`. Draws into an
 * SVG group; the parent owns the SVG and the pointer handling. Text and
 * axes use currentColor so they follow the page's theme.
 */
export function SeriesPanel({ width, height, range, yMax, lines, bars, markerDay, yLabel, showXAxis, dates }: SeriesPanelProps) {
  const [first, last] = range;
  const visibleDays = last - first + 1;
  const xScale = useMemo(() => scaleLinear<number>({ domain: [first, Math.max(first + 1, last)], range: [0, width] }), [first, last, width]);
  const yScale = useMemo(() => scaleLinear<number>({ domain: [0, yMax], range: [height, 0], nice: true }), [yMax, height]);
  const barWidth = Math.max(1, width / Math.max(1, visibleDays) - 1);
  const dateAt = (d: number) => dates[Math.round(d)] ?? "";
  const days = Array.from({ length: visibleDays }, (_, i) => first + i);

  return (
    <Group>
      <GridRows scale={yScale} width={width} stroke="currentColor" strokeOpacity={0.12} numTicks={4} />
      {bars &&
        days.map((d) => {
          const v = bars.values[d];
          if (v === undefined) return null;
          return <Bar key={d} x={xScale(d) - barWidth / 2} y={yScale(v)} width={barWidth} height={Math.max(0, height - yScale(v))} fill={bars.colour} fillOpacity={0.55} />;
        })}
      {lines.map((line) => (
        <LinePath<number> key={line.key} data={days.filter((d) => line.values[d] !== undefined)} x={(d) => xScale(d)} y={(d) => yScale(line.values[d])} stroke={line.colour} strokeWidth={2} strokeLinejoin="round" />
      ))}
      {markerDay !== null && markerDay >= first && markerDay <= last && (
        <line x1={xScale(markerDay)} x2={xScale(markerDay)} y1={0} y2={height} stroke="currentColor" strokeOpacity={0.6} strokeWidth={1} data-testid="marker" />
      )}
      <AxisLeft scale={yScale} numTicks={4} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ fill: "currentColor", fontSize: 10, textAnchor: "end", dx: -4, dy: 3 }} label={yLabel} labelProps={{ fill: "currentColor", fontSize: 10, textAnchor: "middle" }} labelOffset={30} />
      {showXAxis && (
        <AxisBottom top={height} scale={xScale} numTicks={Math.min(6, Math.max(1, visibleDays))} tickFormat={(d) => dateAt(Number(d))} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ fill: "currentColor", fontSize: 10, textAnchor: "middle", dy: 2 }} />
      )}
    </Group>
  );
}
