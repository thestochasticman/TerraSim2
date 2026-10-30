/**
 * Read a field from a parsed JSON object and require it to be a positive integer.
 *
 * obj : Record<string, unknown>
 *     The object to read from.
 * key : string
 *     The field name.
 *
 * Returns the value as a number, dimensionless.
 * Throws an Error naming the key if the value is missing, not a number,
 * not an integer, or not greater than zero.
 */
export function readPositiveInteger(obj: Record<string, unknown>, key: string): number {
  const value = obj[key];
  if (typeof value !== "number" || !Number.isInteger(value) || value <= 0) {
    throw new Error(`${key} must be a positive integer`);
  }
  return value;
}
