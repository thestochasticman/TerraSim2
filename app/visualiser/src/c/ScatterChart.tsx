"use client";

import { AxisBottom, AxisLeft } from "@visx/axis";
import { GridColumns, GridRows } from "@visx/grid";
import { Group } from "@visx/group";
import { scaleLinear } from "@visx/scale";
import { useMemo, useState } from "react";
import { SERIES_COLOURS } from "@/c/SeriesChart";
import type { RunPairs } from "@/t/RunPairs";
import styles from "./ScatterChart.module.css";

export type ScatterChartProps = {
  pairs: RunPairs;
  /** The day on screen; its observations are drawn in full and the rest recede. */
  day: number | null;
  /** Station names, indexed by the pairs' station column, for the readout. */
  stations: string[];
  /** ISO dates by day index, for the readout. */
  dates: string[];
};

/** At most this many points are drawn; beyond it every k-th pair is kept, plus all of the day's. */
export const MAX_POINTS = 6000;
const SIZE = 360;
const MARGIN = { left: 46, right: 12, top: 10, bottom: 34 };
const AXIS_TEXT = { fill: "currentColor", fontSize: 10 } as const;

/**
 * Modelled against observed water content, one dot per observation the run
 * has a value for, with the 1:1 line. The day on screen is drawn in full
 * and the other days fade, so a survey's spread and bias read at once.
 * Hovering a dot reads its date, station and both values below the plot.
 */
export function ScatterChart({ pairs, day, stations, dates }: ScatterChartProps) {
  const [hovered, setHovered] = useState<number | null>(null);
  const plot = SIZE - MARGIN.left - MARGIN.right;
  const height = SIZE - MARGIN.top - MARGIN.bottom;

  const drawn = useMemo(() => {
    const paired: number[] = [];
    for (let i = 0; i < pairs.t.length; i++) if (Number.isFinite(pairs.modelled[i])) paired.push(i);
    const stride = Math.max(1, Math.ceil(paired.length / MAX_POINTS));
    return paired.filter((i, k) => k % stride === 0 || pairs.t[i] === day);
  }, [pairs, day]);

  const top = useMemo(() => {
    let max = 0;
    for (const i of drawn) max = Math.max(max, pairs.observed[i], pairs.modelled[i]);
    return Math.max(0.1, Math.ceil(max * 20) / 20);
  }, [drawn, pairs]);
  const x = useMemo(() => scaleLinear<number>({ domain: [0, top], range: [0, plot] }), [top, plot]);
  const y = useMemo(() => scaleLinear<number>({ domain: [0, top], range: [height, 0] }), [top, height]);

  const onMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * SIZE - MARGIN.left;
    const py = ((e.clientY - rect.top) / rect.height) * SIZE - MARGIN.top;
    let best: number | null = null;
    let bestDistance = 8;
    for (const i of drawn) {
      const d = Math.hypot(x(pairs.observed[i]) - px, y(pairs.modelled[i]) - py);
      if (d < bestDistance) {
        bestDistance = d;
        best = i;
      }
    }
    setHovered(best);
  };

  const highlighting = day !== null;
  return (
    <div className={styles.chart}>
      <svg className={styles.svg} viewBox={`0 0 ${SIZE} ${SIZE}`} role="img" aria-label="modelled against observed" onMouseMove={onMouseMove} onMouseLeave={() => setHovered(null)}>
        <Group left={MARGIN.left} top={MARGIN.top}>
          <GridRows scale={y} width={plot} stroke="currentColor" strokeOpacity={0.12} numTicks={5} />
          <GridColumns scale={x} height={height} stroke="currentColor" strokeOpacity={0.12} numTicks={5} />
          <line x1={x(0)} y1={y(0)} x2={x(top)} y2={y(top)} stroke="currentColor" strokeOpacity={0.5} strokeDasharray="4 3" data-testid="identity" />
          {drawn.map((i) => {
            const onDay = pairs.t[i] === day;
            return (
              <circle
                key={i}
                cx={x(pairs.observed[i])}
                cy={y(pairs.modelled[i])}
                r={onDay ? 4 : 2.5}
                fill={SERIES_COLOURS.moisture}
                fillOpacity={onDay ? 0.95 : highlighting ? 0.18 : 0.55}
                stroke={onDay || hovered === i ? "var(--background)" : "none"}
                strokeWidth={onDay ? 1 : 2}
                data-on-day={onDay}
                data-hovered={hovered === i}
              />
            );
          })}
          <AxisLeft scale={y} numTicks={5} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ ...AXIS_TEXT, textAnchor: "end", dx: -4, dy: 3 }} label="modelled, m³/m³" labelProps={{ ...AXIS_TEXT, textAnchor: "middle" }} labelOffset={28} />
          <AxisBottom top={height} scale={x} numTicks={5} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ ...AXIS_TEXT, textAnchor: "middle", dy: 2 }} label="observed, m³/m³" labelProps={{ ...AXIS_TEXT, textAnchor: "middle" }} labelOffset={14} />
        </Group>
      </svg>
      <p className={styles.readout} data-testid="readout">
        {hovered !== null
          ? `${dates[pairs.t[hovered]] ?? ""} · ${stations[pairs.station[hovered]] ?? ""} · observed ${pairs.observed[hovered].toFixed(3)} · modelled ${pairs.modelled[hovered].toFixed(3)}`
          : `${drawn.length} of ${pairs.t.length} observations drawn${day !== null ? ", this day in full" : ""}`}
      </p>
    </div>
  );
}
