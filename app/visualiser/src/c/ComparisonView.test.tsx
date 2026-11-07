import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { RunComparison } from "@/t/RunComparison";
import type { RunPairs } from "@/t/RunPairs";

vi.mock("@/c/ComparisonTable", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/c/ComparisonTable")>()),
  ComparisonTable: ({ day, onSeek }: { day: number | null; onSeek?: (d: number) => void }) => <div data-testid="table" data-day={day ?? "none"} data-seekable={onSeek ? "yes" : "no"} />,
}));
vi.mock("@/c/ScatterChart", () => ({
  ScatterChart: ({ day, stations }: { day: number | null; stations: string[] }) => <div data-testid="scatter" data-day={day ?? "none"} data-stations={stations.length} />,
}));

const { ComparisonView } = await import("./ComparisonView");

const comparison: RunComparison = {
  daysWritten: 10,
  nPoints: 8644,
  nPaired: 8000,
  rootDepth: 0.3,
  layers: [{ top: 0, bottom: 0.3, n: 8644 }],
  stations: ["a", "b"],
  overall: { n: 8000, observedMean: 0.36, modelledMean: 0.17, bias: -0.19, rmse: 0.205, ubrmse: 0.077, r: 0.659, nse: -3.82, kge: null },
  byDate: [],
  byStation: [],
};
const pairs: RunPairs = { t: new Float32Array(0), row: new Float32Array(0), col: new Float32Array(0), station: new Float32Array(0), observed: new Float32Array(0), modelled: new Float32Array(0) };

describe("ComparisonView", () => {
  it("says what was paired and how the run is read, and shows the whole-run scores", () => {
    render(<ComparisonView comparison={comparison} pairs={pairs} day={3} dates={[]} onSeek={() => {}} />);
    expect(screen.getByText(/8000 of 8644 observations paired, measured over 0–0.3 m at 2 stations/)).toBeTruthy();
    expect(screen.getByText(/0.3 m root depth/)).toBeTruthy();
    expect(screen.getByTestId("headline").textContent).toBe("bias-0.190rmse0.205ubrmse0.077r0.66NSE-3.82KGE–");
  });

  it("passes the day and the seek to the table and the scatter", () => {
    render(<ComparisonView comparison={comparison} pairs={pairs} day={3} dates={[]} onSeek={() => {}} />);
    expect(screen.getByTestId("table").dataset.day).toBe("3");
    expect(screen.getByTestId("table").dataset.seekable).toBe("yes");
    expect(screen.getByTestId("scatter").dataset.day).toBe("3");
    expect(screen.getByTestId("scatter").dataset.stations).toBe("2");
  });
});
