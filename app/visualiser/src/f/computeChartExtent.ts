import type { RunSeries } from "@/t/RunSeries";

/**
 * The y-axis extents of the two series panels.
 *
 * series : RunSeries, millimetres (mm)
 *
 * Returns, each padded up by 5 percent so the largest mark is not on the
 * frame and at least 1 so an all-zero series still has a visible axis:
 *   maxMoisture : top of the stored-water panel
 *   maxIn : top of the flux panel's upward side, the largest daily rain plus inflow
 *   maxOut : depth of the flux panel's downward side, the larger of the
 *            largest daily demand and the largest evaporation plus runoff plus drainage plus leak
 */
export function computeChartExtent(series: RunSeries): { maxMoisture: number; maxIn: number; maxOut: number } {
  const n = series.dates.length;
  let out = 0;
  let gained = 0;
  for (let t = 0; t < n; t++) {
    const lost = (series.evaporation?.[t] ?? 0) + (series.runoff?.[t] ?? 0) + (series.drainage?.[t] ?? 0) + (series.leak?.[t] ?? 0);
    out = Math.max(out, series.pet[t] ?? 0, lost);
    gained = Math.max(gained, (series.rain[t] ?? 0) + (series.inflow?.[t] ?? 0));
  }
  return {
    maxMoisture: pad(Math.max(0, ...series.moisture)),
    maxIn: pad(gained),
    maxOut: pad(out),
  };
}

function pad(max: number): number {
  return Math.max(1, max * 1.05);
}
