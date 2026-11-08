import { NO_DATA_COLOUR } from "@/f/mapMoistureToColour";

/** The diverging pair of the reference palette: red for a model drier than observed, blue for wetter, a neutral grey between. */
const DRY: [number, number, number] = hex("#e34948");
const NEUTRAL: [number, number, number] = hex("#f0efec");
const WET: [number, number, number] = hex("#2a78d6");

function hex(h: string): [number, number, number] {
  return [parseInt(h.slice(1, 3), 16) / 255, parseInt(h.slice(3, 5), 16) / 255, parseInt(h.slice(5, 7), 16) / 255];
}

/**
 * Map a model error to a colour on the diverging ramp.
 *
 * error : m³/m³
 *     Modelled minus observed. Negative is a model drier than the ground, positive wetter.
 * scale : m³/m³
 *     The error that reaches the full colour at either end; larger errors are clamped. Must be positive.
 *
 * Returns [r, g, b] in 0..1: the neutral grey at zero, red at -scale, blue at +scale,
 * linearly between. NaN gives NO_DATA_COLOUR. A non-positive scale is an Error.
 */
export function mapErrorToColour(error: number, scale: number): [number, number, number] {
  if (!(scale > 0)) throw new Error(`scale must be positive, got ${scale}`);
  if (!Number.isFinite(error)) return NO_DATA_COLOUR;
  const f = Math.min(1, Math.max(-1, error / scale));
  const pole = f < 0 ? DRY : WET;
  const w = Math.abs(f);
  return [NEUTRAL[0] + (pole[0] - NEUTRAL[0]) * w, NEUTRAL[1] + (pole[1] - NEUTRAL[1]) * w, NEUTRAL[2] + (pole[2] - NEUTRAL[2]) * w];
}
