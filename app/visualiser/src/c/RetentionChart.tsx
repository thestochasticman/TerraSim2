"use client";

import { AxisBottom, AxisLeft } from "@visx/axis";
import { GridRows } from "@visx/grid";
import { Group } from "@visx/group";
import { scaleBand, scaleLinear, scaleLog } from "@visx/scale";
import { LinePath } from "@visx/shape";
import { useMemo, useState } from "react";
import { mapTextureToColour } from "@/f/mapTextureToColour";
import { useColourScheme } from "@/h/useColourScheme";
import { CURVE_MODELS } from "@/t/CurveModel";
import type { CurveModel } from "@/t/CurveModel";
import type { RetentionCurves } from "@/t/RetentionCurves";
import styles from "./RetentionChart.module.css";

export const MODEL_LABELS: Record<CurveModel, string> = { campbell: "Campbell", van_genuchten: "van Genuchten" };

/** Fixed hue per model: the two bars of each texture. Blue and violet from the reference palette. */
export const MODEL_COLOURS: Record<CurveModel, string> = { campbell: "#3987e5", van_genuchten: "#9085e9" };

const VIEW_WIDTH = 1200;
const MARGIN = { left: 60, right: 16, top: 26, bottom: 30 };
const CURVE_HEIGHT = 300;
const GAP = 48;
const BAR_HEIGHT = 170;
const AXIS_TEXT = { fill: "currentColor", fontSize: 10 } as const;

/** Tick label for a suction in J/kg: 0.1, 1, 10, 100, 1k, 10k, 100k, 1M. */
function formatSuction(v: number): string {
  if (v >= 1e6) return `${v / 1e6}M`;
  if (v >= 1e3) return `${v / 1e3}k`;
  return String(v);
}

/**
 * The book's retention curves, one line per texture, over a log axis of
 * suction, with field capacity and wilting point marked. Below, the water
 * a metre of each texture holds between those two, as a bar per model.
 * Lines take the moisture ramp, stepped for the page's colour scheme so
 * fineness reads as a magnitude on either surface. A radio picks the model the lines and the
 * table show; hovering a line, a bar or a table row highlights that
 * texture everywhere.
 */
export function RetentionChart({ data }: { data: RetentionCurves }) {
  const [model, setModel] = useState<CurveModel>("campbell");
  const [highlighted, setHighlighted] = useState<string | null>(null);
  const scheme = useColourScheme();
  const plotWidth = VIEW_WIDTH - MARGIN.left - MARGIN.right;
  const totalHeight = MARGIN.top + CURVE_HEIGHT + GAP + BAR_HEIGHT + MARGIN.bottom;
  const curves = data.models[model];
  const n = curves.length;
  const textures = useMemo(() => curves.map((c) => c.texture), [curves]);
  const suctionMin = data.suction[0];
  const suctionMax = data.suction[data.suction.length - 1];

  const xLog = useMemo(() => scaleLog<number>({ domain: [suctionMin, suctionMax], range: [0, plotWidth] }), [suctionMin, suctionMax, plotWidth]);
  const maxTheta = useMemo(() => Math.max(0, ...CURVE_MODELS.flatMap((m) => data.models[m].map((c) => c.theta[0] ?? 0))), [data]);
  const yTheta = useMemo(() => scaleLinear<number>({ domain: [0, Math.max(0.1, maxTheta * 1.05)], range: [CURVE_HEIGHT, 0], nice: true }), [maxTheta]);
  const xBand = useMemo(() => scaleBand<string>({ domain: textures, range: [0, plotWidth], padding: 0.25 }), [textures, plotWidth]);
  const maxMm = useMemo(() => Math.max(0, ...CURVE_MODELS.flatMap((m) => data.models[m].map((c) => c.availableWater))), [data]);
  const yMm = useMemo(() => scaleLinear<number>({ domain: [0, Math.max(1, maxMm * 1.05)], range: [BAR_HEIGHT, 0], nice: true }), [maxMm]);
  const decades = useMemo(() => {
    const out: number[] = [];
    for (let e = Math.ceil(Math.log10(suctionMin)); e <= Math.floor(Math.log10(suctionMax) + 1e-9); e++) out.push(10 ** e);
    return out;
  }, [suctionMin, suctionMax]);

  const references = [
    { suction: data.fieldCapacity, label: `field capacity, ${formatSuction(data.fieldCapacity)} J/kg` },
    { suction: data.wiltingPoint, label: `wilting point, ${formatSuction(data.wiltingPoint)} J/kg` },
  ];
  const hover = (texture: string) => ({ onMouseEnter: () => setHighlighted(texture), onMouseLeave: () => setHighlighted(null) });
  const band = xBand.bandwidth();
  const barWidth = Math.max(1, band / 2 - 1);

  return (
    <div className={styles.chart}>
      <svg className={styles.svg} viewBox={`0 0 ${VIEW_WIDTH} ${totalHeight}`} role="img" aria-label="retention curves">
        <Group left={MARGIN.left} top={MARGIN.top} data-model={model} data-testid="curves">
          <GridRows scale={yTheta} width={plotWidth} stroke="currentColor" strokeOpacity={0.12} numTicks={5} />
          {references.map((ref) => (
            <g key={ref.label}>
              <line x1={xLog(ref.suction)} x2={xLog(ref.suction)} y1={0} y2={CURVE_HEIGHT} stroke="currentColor" strokeOpacity={0.5} strokeDasharray="4 3" data-testid="reference" />
              <text x={xLog(ref.suction) + 4} y={-8} {...AXIS_TEXT} fillOpacity={0.8}>
                {ref.label}
              </text>
            </g>
          ))}
          {curves.map((c, i) => {
            const colour = mapTextureToColour(i, n, scheme);
            const isHighlighted = highlighted === c.texture;
            const dimmed = highlighted !== null && !isHighlighted;
            const points = data.suction.map((s, k) => [s, c.theta[k]] as [number, number]);
            return (
              <g key={c.texture}>
                <LinePath<[number, number]> data={points} x={(p) => xLog(p[0])} y={(p) => yTheta(p[1])} stroke={colour} strokeWidth={isHighlighted ? 3 : 1.5} strokeOpacity={dimmed ? 0.25 : 1} strokeLinejoin="round" fill="none" data-texture={c.texture} data-highlighted={isHighlighted} />
                <LinePath<[number, number]> data={points} x={(p) => xLog(p[0])} y={(p) => yTheta(p[1])} stroke="transparent" strokeWidth={12} fill="none" data-hit={c.texture} {...hover(c.texture)} />
              </g>
            );
          })}
          <AxisLeft scale={yTheta} numTicks={5} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ ...AXIS_TEXT, textAnchor: "end", dx: -4, dy: 3 }} label="water content, m³/m³" labelProps={{ ...AXIS_TEXT, textAnchor: "middle" }} labelOffset={36} />
          <AxisBottom top={CURVE_HEIGHT} scale={xLog} tickValues={decades} tickFormat={(v) => formatSuction(Number(v))} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ ...AXIS_TEXT, textAnchor: "middle", dy: 2 }} label="suction, J/kg" labelProps={{ ...AXIS_TEXT, textAnchor: "middle" }} labelOffset={12} />
        </Group>
        <Group left={MARGIN.left} top={MARGIN.top + CURVE_HEIGHT + GAP} data-testid="bars">
          <GridRows scale={yMm} width={plotWidth} stroke="currentColor" strokeOpacity={0.12} numTicks={4} />
          {curves.map((c, ti) => {
            const x0 = xBand(c.texture) ?? 0;
            return (
              <g key={c.texture}>
                {highlighted === c.texture && <rect x={x0 - band * 0.125} y={0} width={band * 1.25} height={BAR_HEIGHT} fill="currentColor" fillOpacity={0.08} data-testid="backdrop" />}
                {CURVE_MODELS.map((m, mi) => {
                  const v = data.models[m][ti]?.availableWater ?? 0;
                  const y = yMm(v);
                  return <rect key={m} x={x0 + mi * (barWidth + 2)} y={y} width={barWidth} height={Math.max(0, BAR_HEIGHT - y)} fill={MODEL_COLOURS[m]} fillOpacity={m === model ? 0.9 : 0.4} data-model={m} data-texture={c.texture} {...hover(c.texture)} />;
                })}
              </g>
            );
          })}
          <AxisLeft scale={yMm} numTicks={4} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ ...AXIS_TEXT, textAnchor: "end", dx: -4, dy: 3 }} label="available water, mm per m" labelProps={{ ...AXIS_TEXT, textAnchor: "middle" }} labelOffset={36} />
          <AxisBottom top={BAR_HEIGHT} scale={xBand} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ ...AXIS_TEXT, textAnchor: "middle", dy: 2 }} />
        </Group>
      </svg>
      <div className={styles.side}>
        <fieldset className={styles.models}>
          <legend>model</legend>
          {CURVE_MODELS.map((m) => (
            <label key={m}>
              <input type="radio" name="model" value={m} checked={model === m} onChange={() => setModel(m)} />
              <span className={styles.swatch} style={{ background: MODEL_COLOURS[m] }} />
              {MODEL_LABELS[m]}
            </label>
          ))}
        </fieldset>
        <table className={styles.table} aria-label="textures">
          <thead>
            <tr>
              <th>texture</th>
              <th>θ at FC</th>
              <th>θ at WP</th>
              <th>mm per m</th>
            </tr>
          </thead>
          <tbody>
            {curves.map((c, i) => (
              <tr key={c.texture} data-highlighted={highlighted === c.texture} {...hover(c.texture)}>
                <td>
                  <span className={styles.swatch} style={{ background: mapTextureToColour(i, n, scheme) }} />
                  {c.texture}
                </td>
                <td>{c.thetaFc.toFixed(3)}</td>
                <td>{c.thetaPwp.toFixed(3)}</td>
                <td>{c.availableWater.toFixed(0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
