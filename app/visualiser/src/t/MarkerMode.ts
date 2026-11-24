/**
 * What the observation markers on the terrain encode: nothing (no markers),
 * the observed water content on the sequential ramp, or the run's error
 * at each point, modelled minus observed, on the diverging ramp, or the
 * day's sensors in one plain red, to find them against the bucket columns.
 */
export type MarkerMode = "none" | "observed" | "error" | "sensors";
