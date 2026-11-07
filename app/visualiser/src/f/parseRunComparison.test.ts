import { describe, expect, it } from "vitest";
import { parseRunComparison } from "./parseRunComparison";

const scores = { n: 2, observed_mean: 0.3, modelled_mean: 0.2, bias: -0.1, rmse: 0.1, ubrmse: 0.0, r: null, nse: null, kge: null };
const body = {
  days_written: 10,
  n_points: 3,
  n_paired: 2,
  root_depth: 0.3,
  layers: [{ top: 0, bottom: 0.3, n: 3 }],
  stations: ["a", "b"],
  overall: scores,
  by_date: [
    { date: "1995-09-25", t: 0, ...scores },
    { date: "1997-01-01", t: null, n: 1 },
  ],
  by_station: [
    { station: 0, ...scores },
    { station: 1, n: 1 },
  ],
};

describe("parseRunComparison", () => {
  it("reads every field into camelCase with nulls kept", () => {
    const c = parseRunComparison(body);
    expect(c.daysWritten).toBe(10);
    expect(c.nPoints).toBe(3);
    expect(c.nPaired).toBe(2);
    expect(c.rootDepth).toBe(0.3);
    expect(c.layers).toEqual([{ top: 0, bottom: 0.3, n: 3 }]);
    expect(c.stations).toEqual(["a", "b"]);
    expect(c.overall.bias).toBe(-0.1);
    expect(c.overall.r).toBeNull();
    expect(c.byDate[0]).toMatchObject({ date: "1995-09-25", t: 0, n: 2, observedMean: 0.3 });
    expect(c.byDate[1]).toMatchObject({ date: "1997-01-01", t: null, n: 1, bias: null });
    expect(c.byStation[1]).toMatchObject({ station: 1, n: 1, rmse: null });
  });

  it("names the first bad field", () => {
    expect(() => parseRunComparison([])).toThrow("JSON object");
    expect(() => parseRunComparison({ ...body, root_depth: 0 })).toThrow("root_depth");
    expect(parseRunComparison({ ...body, root_depth: null }).rootDepth).toBeNull();
    expect(() => parseRunComparison({ ...body, layers: [{ top: 0.3, bottom: 0.3, n: 1 }] })).toThrow("layers[0]");
    expect(() => parseRunComparison({ ...body, by_date: [{ date: 5, t: 0, n: 1 }] })).toThrow("by_date[0]: date");
    expect(() => parseRunComparison({ ...body, by_date: [{ date: "d", t: -1, n: 1 }] })).toThrow("by_date[0]: t");
    expect(() => parseRunComparison({ ...body, by_station: [{ station: 2, n: 1 }] })).toThrow("by_station[0]: station");
    expect(() => parseRunComparison({ ...body, overall: { n: 1, rmse: "x" } })).toThrow("overall: rmse");
  });
});
