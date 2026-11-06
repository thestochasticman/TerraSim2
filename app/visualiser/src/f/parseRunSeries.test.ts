import { describe, expect, it } from "vitest";
import { parseRunSeries } from "./parseRunSeries";

const valid = { dates: ["2024-01-01", "2024-01-02"], rain: [0, 5.5], pet: [4, 4.2], moisture: [50, 51.3], infiltration: [0, 5.5], runoff: [0, 0], evaporation: [2, 2.1] };

describe("parseRunSeries", () => {
  it("parses all series with one value per date", () => {
    expect(parseRunSeries(valid)).toEqual(valid);
  });

  it("allows the flux series to be absent", () => {
    expect(parseRunSeries({ ...valid, inflow: [0, 1.5] }).inflow).toEqual([0, 1.5]);
    expect(parseRunSeries({ ...valid, drainage: [0, 2], leak: [1, 1] }).leak).toEqual([1, 1]);
    expect(parseRunSeries(valid).inflow).toBeUndefined();
    const { infiltration: _a, runoff: _b, evaporation: _c, ...noFluxes } = valid;
    void _a; void _b; void _c;
    const s = parseRunSeries(noFluxes);
    expect(s.runoff).toBeUndefined();
    expect(s.moisture).toEqual([50, 51.3]);
  });

  it("accepts an empty series before any day is written", () => {
    expect(parseRunSeries({ dates: [], rain: [], pet: [], moisture: [] }).dates).toEqual([]);
  });

  it("rejects length mismatches, non-finite values and missing required series", () => {
    expect(() => parseRunSeries({ ...valid, rain: [1] })).toThrow("rain must have one value per date (2)");
    expect(() => parseRunSeries({ ...valid, pet: [1, null] })).toThrow("pet must contain only finite numbers");
    const { moisture: _m, ...noMoisture } = valid;
    void _m;
    expect(() => parseRunSeries(noMoisture)).toThrow("moisture");
    expect(() => parseRunSeries({ ...valid, dates: "x" })).toThrow("dates");
  });
});
