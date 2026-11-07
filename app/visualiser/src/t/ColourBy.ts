/**
 * What the terrain surface's colour encodes: a day's fullness, that day's moisture stretched over
 * its own range, the cells' capacity, how many cells drain through each, or what grows on each.
 */
export type ColourBy = "moisture" | "relative" | "capacity" | "upslope" | "vegetation";
