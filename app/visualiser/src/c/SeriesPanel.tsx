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
  /** Days across the x axis; day i sits at i / (nDays - 1) of the width. */
  nDays: number;
  /** Top of the y axis, millimetres (mm). */
  yMax: number;
  /** Lines to draw, in fixed order. */
  lines: SeriesLine[];
  /** Optional bars, one per day, drawn behind the lines. */
  bars?: SeriesLine;
  /** Day to mark with a vertical cursor, if any. */
  markerDay: number | null;
  /** Axis title. */
  yLabel: string;
  /** Whether to draw the x axis (only the bottom panel does). */
  showXAxis: boolean;
  /** Tick labels for the x axis, one per day; sampled sparsely. */
  dates: string[];
};

export const MARGIN = { left: 48, right: 12, top: 8, bottom: 24 };

/**
 * One panel of the series chart: a y axis, grid rows, optional bars, lines,
 * and a vertical marker. Draws into an SVG group; the parent owns the SVG
 * and the pointer handling. Text and axes use currentColor so they follow
 * the page's theme.
 */
export function SeriesPanel({ width, height, nDays, yMax, lines, bars, markerDay, yLabel, showXAxis, dates }: SeriesPanelProps) {
  const xScale = useMemo(() => scaleLinear<number>({ domain: [0, Math.max(1, nDays - 1)], range: [0, width] }), [nDays, width]);
  const yScale = useMemo(() => scaleLinear<number>({ domain: [0, yMax], range: [height, 0], nice: true }), [yMax, height]);
  const barWidth = Math.max(1, width / Math.max(1, nDays) - 1);
  const dateAt = (d: number) => dates[Math.round(d)] ?? "";

  return (
    <Group>
      <GridRows scale={yScale} width={width} stroke="currentColor" strokeOpacity={0.12} numTicks={4} />
      {bars &&
        bars.values.map((v, i) => (
          <Bar key={i} x={xScale(i) - barWidth / 2} y={yScale(v)} width={barWidth} height={Math.max(0, height - yScale(v))} fill={bars.colour} fillOpacity={0.55} />
        ))}
      {lines.map((line) => (
        <LinePath<number> key={line.key} data={line.values} x={(_, i) => xScale(i)} y={(v) => yScale(v)} stroke={line.colour} strokeWidth={2} strokeLinejoin="round" />
      ))}
      {markerDay !== null && nDays > 0 && (
        <line x1={xScale(markerDay)} x2={xScale(markerDay)} y1={0} y2={height} stroke="currentColor" strokeOpacity={0.6} strokeWidth={1} data-testid="marker" />
      )}
      <AxisLeft scale={yScale} numTicks={4} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ fill: "currentColor", fontSize: 10, textAnchor: "end", dx: -4, dy: 3 }} label={yLabel} labelProps={{ fill: "currentColor", fontSize: 10, textAnchor: "middle" }} labelOffset={30} />
      {showXAxis && (
        <AxisBottom top={height} scale={xScale} numTicks={Math.min(6, Math.max(1, nDays))} tickFormat={(d) => dateAt(Number(d))} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ fill: "currentColor", fontSize: 10, textAnchor: "middle", dy: 2 }} />
      )}
    </Group>
  );
}
