import { describe, expect, it } from "vitest";
import { parseScores } from "./parseScores";

describe("parseScores", () => {
  it("maps the snake_case fields, keeps nulls, and leaves absent fields null", () => {
    const s = parseScores({ n: 3, observed_mean: 0.3, modelled_mean: 0.25, bias: -0.05, rmse: 0.06, ubrmse: 0.03, r: 0.8, nse: null, kge: 0.5 }, "x");
    expect(s).toEqual({ n: 3, observedMean: 0.3, modelledMean: 0.25, bias: -0.05, rmse: 0.06, ubrmse: 0.03, r: 0.8, nse: null, kge: 0.5 });
    expect(parseScores({ n: 0 }, "x")).toEqual({ n: 0, observedMean: null, modelledMean: null, bias: null, rmse: null, ubrmse: null, r: null, nse: null, kge: null });
  });

  it("refuses a bad n and a non-numeric score, naming the place", () => {
    expect(() => parseScores({ n: -1 }, "overall")).toThrow("overall: n");
    expect(() => parseScores({ n: 2, rmse: "0.1" }, "by_date[0]")).toThrow("by_date[0]: rmse");
    expect(() => parseScores({ n: 2, r: Number.NaN }, "x")).toThrow("r must be");
  });
});
