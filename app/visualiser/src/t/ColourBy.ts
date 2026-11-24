/**
 * What the terrain surface's colour encodes: a day's fullness, that day's moisture stretched over
 * its own range, the cells' capacity, how many cells drain through each, what grows on each,
 * or nothing: the earth tone, for when the bucket columns carry the water.
 */
export type ColourBy = "moisture" | "relative" | "capacity" | "upslope" | "vegetation" | "earth";
