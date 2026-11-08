import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ComparisonTable, formatScore } from "./ComparisonTable";
import type { RunComparison } from "@/t/RunComparison";

const scores = { observedMean: 0.35, modelledMean: 0.3, bias: -0.05, rmse: 0.06, ubrmse: 0.03, r: 0.81, nse: 0.2, kge: 0.5 };
const comparison: RunComparison = {
  daysWritten: 100,
  nPoints: 5,
  nPaired: 4,
  rootDepth: 0.3,
  layers: [{ top: 0, bottom: 0.3, n: 5 }],
  stations: ["a"],
  overall: { n: 4, ...scores },
  byDate: [
    { date: "1995-09-25", t: 0, n: 2, ...scores },
    { date: "1996-02-13", t: 141, n: 2, ...scores, r: null },
    { date: "1997-01-01", t: null, n: 1, observedMean: 0.2, modelledMean: null, bias: null, rmse: null, ubrmse: null, r: null, nse: null, kge: null },
  ],
  byStation: [],
};

describe("ComparisonTable", () => {
  it("formats a score to fixed decimals and a null as a dash", () => {
    expect(formatScore(0.123456, 3)).toBe("0.123");
    expect(formatScore(null, 2)).toBe("–");
  });

  it("lists the whole run first, then a row per survey with its scores, dashes where unknown", () => {
    render(<ComparisonTable comparison={comparison} day={null} />);
    const rows = within(screen.getByRole("table", { name: "scores by survey" })).getAllByRole("row");
    expect(rows).toHaveLength(5);
    expect(rows[1].textContent).toBe("all days40.3500.300-0.0500.0600.81");
    expect(rows[2].textContent).toContain("1995-09-25");
    expect(rows[3].textContent?.endsWith("–")).toBe(true);
    expect(rows[4].textContent).toContain("1997-01-01");
  });

  it("highlights the survey of the day on screen and seeks on click, never for a date outside the run", () => {
    const onSeek = vi.fn();
    render(<ComparisonTable comparison={comparison} day={141} onSeek={onSeek} />);
    const rows = within(screen.getByRole("table")).getAllByRole("row");
    expect(rows[3].dataset.highlighted).toBe("true");
    expect(rows[2].dataset.highlighted).toBe("false");
    fireEvent.click(rows[2]);
    expect(onSeek).toHaveBeenLastCalledWith(0);
    fireEvent.click(rows[4]);
    expect(onSeek).toHaveBeenCalledTimes(1);
  });
});
