"use client";

import { useMemo, useState } from "react";
import { invertTernary } from "@/f/invertTernary";
import { mapTextureToColour } from "@/f/mapTextureToColour";
import { TRIANGLE_HEIGHT, projectTernary } from "@/f/projectTernary";
import { useColourScheme } from "@/h/useColourScheme";
import type { TextureTriangle as TextureTriangleData } from "@/t/TextureTriangle";
import styles from "./TextureTriangle.module.css";

/** Where the triangle sits in the SVG's viewBox, in SVG units. */
export const LAYOUT = { width: 1000, height: 900, left: 100, base: 780, side: 800 } as const;
const TICKS = [0, 20, 40, 60, 80, 100];
const TEXT = { fill: "currentColor", fontSize: 17 } as const;
const TITLE_SIZE = 20;
const REGION_SIZE = 19;

/** Pixel position of a composition given in percent. */
function place(sand: number, silt: number, clay: number): { x: number; y: number } {
  const p = projectTernary(sand / 100, silt / 100, clay / 100);
  return { x: LAYOUT.left + p.x * LAYOUT.side, y: LAYOUT.base - p.y * LAYOUT.side };
}

/**
 * The USDA texture triangle as the classifier draws it: one dot per grid
 * composition, coloured by class on the fineness ramp, each class named
 * at its centroid, and table 2.4's typical compositions ringed. Sand runs
 * along the base, clay up the left edge, silt down the right. Moving the
 * pointer over the triangle reads off the nearest grid composition: its
 * class and the book's particle-size estimates of air entry and b.
 * Hovering a class in the list highlights its region.
 */
export function TextureTriangle({ data }: { data: TextureTriangleData }) {
  const scheme = useColourScheme();
  const [hovered, setHovered] = useState<number | null>(null);
  const [listHighlight, setListHighlight] = useState<number | null>(null);
  const n = data.textures.length;
  const { sand, silt, clay, texture } = data.points;
  const spacing = (LAYOUT.side * data.step) / 100;
  const radius = spacing * 0.56;

  const index = useMemo(() => {
    const map = new Map<string, number>();
    sand.forEach((s, i) => map.set(`${s},${silt[i]}`, i));
    return map;
  }, [sand, silt]);

  const centroids = useMemo(() => {
    const sums = data.textures.map(() => ({ x: 0, y: 0, count: 0 }));
    texture.forEach((t, i) => {
      const p = place(sand[i], silt[i], clay[i]);
      sums[t].x += p.x;
      sums[t].y += p.y;
      sums[t].count += 1;
    });
    return sums.map((s) => (s.count ? { x: s.x / s.count, y: s.y / s.count } : null));
  }, [data.textures, texture, sand, silt, clay]);

  const highlighted = listHighlight ?? (hovered !== null ? texture[hovered] : null);

  const onMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * LAYOUT.width;
    const py = ((e.clientY - rect.top) / rect.height) * LAYOUT.height;
    const f = invertTernary((px - LAYOUT.left) / LAYOUT.side, (LAYOUT.base - py) / LAYOUT.side);
    const slack = data.step / 200;
    if (f.sand < -slack || f.silt < -slack || f.clay < -slack) {
      setHovered(null);
      return;
    }
    const s = Math.round((f.sand * 100) / data.step) * data.step;
    const si = Math.round((f.silt * 100) / data.step) * data.step;
    setHovered(index.get(`${s},${si}`) ?? null);
  };

  const colourOf = (t: number) => mapTextureToColour(t, n, scheme);
  const corner = { sand: place(100, 0, 0), silt: place(0, 100, 0), clay: place(0, 0, 100) };

  return (
    <div className={styles.chart}>
      <svg className={styles.svg} viewBox={`0 0 ${LAYOUT.width} ${LAYOUT.height}`} role="img" aria-label="texture triangle" onMouseMove={onMouseMove} onMouseLeave={() => setHovered(null)}>
        {sand.map((s, i) => {
          const p = place(s, silt[i], clay[i]);
          const dim = highlighted !== null && texture[i] !== highlighted;
          return <circle key={i} cx={p.x} cy={p.y} r={radius} fill={colourOf(texture[i])} fillOpacity={dim ? 0.25 : 1} data-point={i} />;
        })}
        <polygon points={`${corner.sand.x},${corner.sand.y} ${corner.silt.x},${corner.silt.y} ${corner.clay.x},${corner.clay.y}`} fill="none" stroke="currentColor" strokeOpacity={0.6} />
        {TICKS.map((v) => {
          const bottom = place(v, 100 - v, 0);
          const leftEdge = place(100 - v, 0, v);
          const rightEdge = place(0, 100 - v, v);
          return (
            <g key={v}>
              <text x={bottom.x} y={bottom.y + 26} {...TEXT} textAnchor="middle">{v}</text>
              <text x={leftEdge.x - 14} y={leftEdge.y + 4} {...TEXT} textAnchor="end">{v}</text>
              <text x={rightEdge.x + 14} y={rightEdge.y + 4} {...TEXT} textAnchor="start">{v}</text>
            </g>
          );
        })}
        <text x={LAYOUT.left + LAYOUT.side / 2} y={LAYOUT.base + 56} {...TEXT} fontSize={TITLE_SIZE} textAnchor="middle">sand %</text>
        <text x={LAYOUT.left + LAYOUT.side / 4 - 50} y={LAYOUT.base - (LAYOUT.side * TRIANGLE_HEIGHT) / 2} {...TEXT} fontSize={TITLE_SIZE} textAnchor="middle" transform={`rotate(-60 ${LAYOUT.left + LAYOUT.side / 4 - 50} ${LAYOUT.base - (LAYOUT.side * TRIANGLE_HEIGHT) / 2})`}>clay %</text>
        <text x={LAYOUT.left + (3 * LAYOUT.side) / 4 + 50} y={LAYOUT.base - (LAYOUT.side * TRIANGLE_HEIGHT) / 2} {...TEXT} fontSize={TITLE_SIZE} textAnchor="middle" transform={`rotate(60 ${LAYOUT.left + (3 * LAYOUT.side) / 4 + 50} ${LAYOUT.base - (LAYOUT.side * TRIANGLE_HEIGHT) / 2})`}>silt %</text>
        {centroids.map((c, t) => c && (
          <text key={t} x={c.x} y={c.y + 6} {...TEXT} fontSize={REGION_SIZE} textAnchor="middle" paintOrder="stroke" stroke={scheme === "dark" ? "#0a0a0a" : "#ffffff"} strokeWidth={3} strokeOpacity={0.7} data-region={data.textures[t]}>
            {data.textures[t]}
          </text>
        ))}
        {data.typical.map((rec) => {
          const p = place(rec.sand, rec.silt, rec.clay);
          return <circle key={rec.texture} cx={p.x} cy={p.y} r={6} fill="none" stroke="currentColor" strokeWidth={1.5} data-typical={rec.texture} />;
        })}
        {hovered !== null && (() => { const p = place(sand[hovered], silt[hovered], clay[hovered]); return <circle cx={p.x} cy={p.y} r={radius + 3} fill="none" stroke="currentColor" strokeWidth={2} data-testid="cursor" />; })()}
      </svg>
      <div className={styles.side}>
        <div className={styles.reading} aria-label="reading">
          {hovered === null ? (
            <p className={styles.hint}>Move over the triangle to read a composition. Rings mark table 2.4&apos;s typical soils.</p>
          ) : (
            <>
              <h2>{data.textures[texture[hovered]]}</h2>
              <dl>
                <dt>sand / silt / clay</dt>
                <dd>{sand[hovered]} / {silt[hovered]} / {clay[hovered]} %</dd>
                <dt>geometric mean diameter</dt>
                <dd>{data.points.diameter[hovered].toFixed(2)} µm</dd>
                <dt>air entry, estimated</dt>
                <dd>{data.points.psiE[hovered].toFixed(2)} J/kg</dd>
                <dt>b, estimated</dt>
                <dd>{data.points.b[hovered].toFixed(2)}</dd>
              </dl>
            </>
          )}
        </div>
        <ul className={styles.list} aria-label="classes">
          {data.textures.map((name, t) => (
            <li key={name} data-highlighted={highlighted === t} onMouseEnter={() => setListHighlight(t)} onMouseLeave={() => setListHighlight(null)}>
              <span className={styles.swatch} style={{ background: colourOf(t) }} />
              {name}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
