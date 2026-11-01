"use client";

import { AxisBottom, AxisLeft } from "@visx/axis";
import { GridRows } from "@visx/grid";
import { Group } from "@visx/group";
import { scaleLinear } from "@visx/scale";
import { LinePath } from "@visx/shape";
import { useMemo } from "react";

export type SeriesLine = {
  key: string;
  label: string;
  colour: string;
  values: number[];
};

/**
 * Bars drawn from the zero line in one direction. The stack's series are
 * drawn one on top of the other, first nearest zero. The outline, if any,
 * is an unfilled bar from zero to its own value, behind the stack: used
 * for a ceiling such as demand behind evaporation.
 */
export type BarGroup = {
  direction: "up" | "down";
  stack: SeriesLine[];
  outline?: SeriesLine;
};

export type SeriesPanelProps = {
  /** Plot width in SVG units, excluding margins. */
  width: number;
  height: number;
  /** Days visible across the x axis, inclusive; the first sits at the left edge, the last at the right. */
  range: [number, number];
  /** Bottom and top of the y axis, millimetres (mm). yMin is 0 or negative. */
  yMin: number;
  yMax: number;
  /** Lines to draw, in fixed order; values indexed by day. */
  lines: SeriesLine[];
  /** Bars from the zero line, drawn behind the lines. */
  barGroups?: BarGroup[];
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
 * One panel of the series chart: a y axis, grid rows, bars up or down from
 * zero, lines, and a vertical marker, showing only the days in `range`.
 * Draws into an SVG group; the parent owns the SVG and the pointer
 * handling. Text and axes use currentColor so they follow the page's theme.
 */
export function SeriesPanel({ width, height, range, yMin, yMax, lines, barGroups = [], markerDay, yLabel, showXAxis, dates }: SeriesPanelProps) {
  const [first, last] = range;
  const visibleDays = last - first + 1;
  const xScale = useMemo(() => scaleLinear<number>({ domain: [first, Math.max(first + 1, last)], range: [0, width] }), [first, last, width]);
  const yScale = useMemo(() => scaleLinear<number>({ domain: [Math.min(0, yMin), yMax], range: [height, 0], nice: true }), [yMin, yMax, height]);
  const barWidth = Math.max(1, width / Math.max(1, visibleDays) - 1);
  const dateAt = (d: number) => dates[Math.round(d)] ?? "";
  const days = Array.from({ length: visibleDays }, (_, i) => first + i);
  const zeroY = yScale(0);

  /** A bar covering [from, to] in data units at day d, as rect geometry. */
  const barRect = (d: number, from: number, to: number) => {
    const y0 = yScale(from);
    const y1 = yScale(to);
    return { x: xScale(d) - barWidth / 2, y: Math.min(y0, y1), width: barWidth, height: Math.abs(y1 - y0) };
  };

  return (
    <Group>
      <GridRows scale={yScale} width={width} stroke="currentColor" strokeOpacity={0.12} numTicks={4} />
      {barGroups.map((group, g) => {
        const sign = group.direction === "up" ? 1 : -1;
        return (
          <Group key={g}>
            {group.outline &&
              days.map((d) => {
                const v = group.outline?.values[d];
                if (v === undefined || v <= 0) return null;
                const r = barRect(d, 0, sign * v);
                return <rect key={`o${d}`} {...r} fill="none" stroke={group.outline?.colour} strokeWidth={1} strokeOpacity={0.9} data-outline={group.outline?.key} />;
              })}
            {days.map((d) => {
              let base = 0;
              return group.stack.map((series) => {
                const v = series.values[d];
                if (v === undefined) return null;
                const r = barRect(d, sign * base, sign * (base + v));
                base += v;
                return <rect key={`${series.key}${d}`} {...r} fill={series.colour} fillOpacity={0.8} data-series={series.key} />;
              });
            })}
          </Group>
        );
      })}
      {yMin < 0 && <line x1={0} x2={width} y1={zeroY} y2={zeroY} stroke="currentColor" strokeOpacity={0.5} strokeWidth={1} data-testid="zero" />}
      {lines.map((line) => (
        <LinePath<number> key={line.key} data={days.filter((d) => line.values[d] !== undefined)} x={(d) => xScale(d)} y={(d) => yScale(line.values[d])} stroke={line.colour} strokeWidth={2} strokeLinejoin="round" />
      ))}
      {markerDay !== null && markerDay >= first && markerDay <= last && (
        <line x1={xScale(markerDay)} x2={xScale(markerDay)} y1={0} y2={height} stroke="currentColor" strokeOpacity={0.6} strokeWidth={1} data-testid="marker" />
      )}
      <AxisLeft scale={yScale} numTicks={4} tickFormat={(v) => String(Math.abs(Number(v)))} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ fill: "currentColor", fontSize: 10, textAnchor: "end", dx: -4, dy: 3 }} label={yLabel} labelProps={{ fill: "currentColor", fontSize: 10, textAnchor: "middle" }} labelOffset={30} />
      {showXAxis && (
        <AxisBottom top={height} scale={xScale} numTicks={Math.min(6, Math.max(1, visibleDays))} tickFormat={(d) => dateAt(Number(d))} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ fill: "currentColor", fontSize: 10, textAnchor: "middle", dy: 2 }} />
      )}
    </Group>
  );
}
