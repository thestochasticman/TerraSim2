import type { Scores } from "@/t/Scores";

/**
 * A run scored against its site's observations, for the days written so far.
 *
 * daysWritten : dimensionless
 * nPoints : dimensionless, observations at the site
 * nPaired : dimensionless, observations the run has a value for so far
 * rootDepth : metres (m), the depth the run's stored water is read over
 * layers : the depth intervals observed, metres (m), with how many observations each has
 * stations : the station names, indexed by the pairs' station column
 * overall : scores over every paired observation
 * byDate : one entry per survey date; t is the run's day index for that date, or null when the date is outside the run
 * byStation : one entry per station, by index
 */
export type RunComparison = {
  daysWritten: number;
  nPoints: number;
  nPaired: number;
  rootDepth: number;
  layers: { top: number; bottom: number; n: number }[];
  stations: string[];
  overall: Scores;
  byDate: ({ date: string; t: number | null } & Scores)[];
  byStation: ({ station: number } & Scores)[];
};
