/** The two retention-curve models from the book, as the service names them. */
export const CURVE_MODELS = ["campbell", "van_genuchten"] as const;

export type CurveModel = (typeof CURVE_MODELS)[number];
