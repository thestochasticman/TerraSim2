import type { RunSeries } from "@/t/RunSeries";

/**
 * The y-axis tops for the two series panels.
 *
 * series : RunSeries, millimetres (mm)
 *
 * Returns maxMoisture and maxFlux, each the largest value in its panel's
 * series padded up by 5 percent so the top point is not on the frame, and
 * at least 1 so an all-zero series still has a visible axis. Flux panel
 * covers rain, pet and any recorded fluxes.
 */
export function computeChartExtent(series: RunSeries): { maxMoisture: number; maxFlux: number } {
  const fluxSeries = [series.rain, series.pet, series.infiltration, series.runoff, series.evaporation].filter((s): s is number[] => s !== undefined);
  return {
    maxMoisture: pad(Math.max(0, ...series.moisture)),
    maxFlux: pad(Math.max(0, ...fluxSeries.flat())),
  };
}

function pad(max: number): number {
  return Math.max(1, max * 1.05);
}
