"use client";

import { AxisBottom, AxisLeft } from "@visx/axis";
import { Group } from "@visx/group";
import { scaleLinear } from "@visx/scale";
import { useMemo } from "react";
import { mapTextureToColour } from "@/f/mapTextureToColour";
import { useColourScheme } from "@/h/useColourScheme";
import type { SoilColumn } from "@/t/SoilColumn";
import styles from "./SoilColumnChart.module.css";

const VIEW_WIDTH = 560;
const VIEW_HEIGHT = 420;
const MARGIN = { left: 56, right: 24, top: 10, bottom: 34 };
const AXIS_TEXT = { fill: "currentColor", fontSize: 10 } as const;

/** "0–5 cm" style label for a layer. */
function formatLayer(top: number, bottom: number): string {
  return `${Math.round(top * 100)}–${Math.round(bottom * 100)} cm`;
}

/**
 * A soil column as a profile: depth down the page, each layer a bar whose
 * width is its available fraction, coloured by texture on the fineness
 * ramp. The part of each bar the roots reach is solid; the rest is faded.
 * A dashed line marks the root depth. Beside it, the total in mm as the
 * headline and a table of the layers.
 */
export function SoilColumnChart({ column }: { column: SoilColumn }) {
  const scheme = useColourScheme();
  const plotWidth = VIEW_WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = VIEW_HEIGHT - MARGIN.top - MARGIN.bottom;
  const bottom = column.layerBounds[column.layerBounds.length - 1];
  const maxFraction = useMemo(() => Math.max(0.05, ...column.layers.map((l) => l.fraction)) * 1.1, [column.layers]);
  const yScale = useMemo(() => scaleLinear<number>({ domain: [0, bottom], range: [0, plotHeight] }), [bottom, plotHeight]);
  const xScale = useMemo(() => scaleLinear<number>({ domain: [0, maxFraction], range: [0, plotWidth], nice: true }), [maxFraction, plotWidth]);
  const colourOf = (texture: string) => mapTextureToColour(Math.max(0, column.textures.indexOf(texture)), column.textures.length, scheme);
  const rootY = yScale(Math.min(column.rootDepth, bottom));

  return (
    <div className={styles.chart}>
      <svg className={styles.svg} viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`} role="img" aria-label="soil column">
        <Group left={MARGIN.left} top={MARGIN.top}>
          {column.layers.map((layer) => {
            const y0 = yScale(layer.top);
            const y1 = yScale(layer.bottom);
            const split = yScale(Math.min(layer.bottom, Math.max(layer.top, layer.top + layer.thicknessInRoots)));
            const width = Math.max(0, xScale(layer.fraction));
            const colour = colourOf(layer.texture);
            return (
              <g key={layer.top}>
                {split > y0 && <rect x={0} y={y0} width={width} height={split - y0 - 1} fill={colour} fillOpacity={0.9} data-layer={layer.texture} data-part="roots" />}
                {y1 > split && <rect x={0} y={split} width={width} height={y1 - split - 1} fill={colour} fillOpacity={0.3} data-layer={layer.texture} data-part="below" />}
                <text x={width + 6} y={(y0 + y1) / 2 + 4} {...AXIS_TEXT} fillOpacity={0.85}>
                  {layer.texture}, {layer.mm.toFixed(0)} mm
                </text>
              </g>
            );
          })}
          <line x1={0} x2={plotWidth} y1={rootY} y2={rootY} stroke="currentColor" strokeDasharray="5 3" strokeOpacity={0.8} data-testid="root-depth" />
          <text x={plotWidth} y={rootY - 5} {...AXIS_TEXT} textAnchor="end">
            roots to {column.rootDepth.toFixed(2)} m
          </text>
          <AxisLeft scale={yScale} tickValues={column.layerBounds} tickFormat={(v) => `${Number(v).toFixed(2)}`} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ ...AXIS_TEXT, textAnchor: "end", dx: -4, dy: 3 }} label="depth, m" labelProps={{ ...AXIS_TEXT, textAnchor: "middle" }} labelOffset={34} />
          <AxisBottom top={plotHeight} scale={xScale} numTicks={5} stroke="currentColor" tickStroke="currentColor" tickLabelProps={{ ...AXIS_TEXT, textAnchor: "middle", dy: 2 }} label="available water, m³ per m³ of soil" labelProps={{ ...AXIS_TEXT, textAnchor: "middle" }} labelOffset={12} />
        </Group>
      </svg>
      <div className={styles.side}>
        <div className={styles.total} aria-label="total">
          {column.total.toFixed(0)} <span className={styles.unit}>mm within the roots</span>
        </div>
        <p className={styles.note}>What this column&apos;s cell would hold between wilting point and field capacity: its capacity in the bucket model.</p>
        <table className={styles.table} aria-label="layers">
          <thead>
            <tr>
              <th>layer</th>
              <th>texture</th>
              <th>fraction</th>
              <th>in roots</th>
              <th>mm</th>
            </tr>
          </thead>
          <tbody>
            {column.layers.map((layer) => (
              <tr key={layer.top}>
                <td>{formatLayer(layer.top, layer.bottom)}</td>
                <td>
                  <span className={styles.swatch} style={{ background: colourOf(layer.texture) }} />
                  {layer.texture}
                </td>
                <td>{layer.fraction.toFixed(3)}</td>
                <td>{(layer.thicknessInRoots * 100).toFixed(0)} cm</td>
                <td>{layer.mm.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
