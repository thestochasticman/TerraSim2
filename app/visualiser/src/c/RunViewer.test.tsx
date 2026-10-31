import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { RunState } from "@/h/useRun";
import type { TerrainGrid } from "@/t/TerrainGrid";

const fetchSites = vi.fn();
const useRun = vi.fn<(request: unknown) => RunState>();
const useRunSeries = vi.fn<(runId: string | null, daysWritten: number) => { series: unknown; error: string | null }>();

vi.mock("@/api/fetchSites", () => ({ fetchSites: () => fetchSites() }));
vi.mock("@/h/useRun", () => ({ useRun: (r: unknown) => useRun(r) }));
vi.mock("@/h/useRunSeries", () => ({ useRunSeries: (id: string | null, d: number) => useRunSeries(id, d) }));
vi.mock("@/c/SeriesChart", () => ({
  SeriesChart: ({ day, onSeek }: { day: number | null; onSeek?: (d: number) => void }) => (
    <div data-testid="chart" data-day={day ?? "none"} data-seekable={onSeek ? "yes" : "no"} />
  ),
}));
vi.mock("@/c/TerrainScene", () => ({
  TerrainScene: ({ grid, moisture }: { grid: TerrainGrid; moisture?: Float32Array }) => (
    <div data-testid="scene">{`${grid.rows}x${grid.cols}:${moisture ? Array.from(moisture).join(",") : "none"}`}</div>
  ),
}));

const { RunViewer } = await import("./RunViewer");

const terrain: TerrainGrid = { rows: 1, cols: 2, cellSize: 10, elevation: Float64Array.from([1, 2]) };
const idle: RunState = { status: null, terrain: null, latest: null, error: null, fetchDay: async () => new Float32Array() };
const dates = ["d0", "d1", "d2", "d3", "d4"];

describe("RunViewer", () => {
  beforeEach(() => {
    fetchSites.mockReset().mockResolvedValue(["example", "tarrawarra"]);
    useRun.mockReset().mockReturnValue(idle);
    useRunSeries.mockReset().mockReturnValue({ series: null, error: null });
  });

  const select = () => screen.getByRole("combobox") as HTMLSelectElement;

  it("lists sites, defaults to the first, and shows no run and no scrubber until started", async () => {
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    expect(screen.getAllByRole("option").map((o) => o.textContent)).toEqual(["example", "tarrawarra"]);
    expect(screen.getByRole("status").textContent).toBe("no run");
    expect(screen.queryByRole("slider")).toBeNull();
    expect(useRun).toHaveBeenLastCalledWith(null);
  });

  it("starting a run passes a request for the chosen site to the hook", async () => {
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    fireEvent.change(select(), { target: { value: "tarrawarra" } });
    fireEvent.click(screen.getByRole("button", { name: "run" }));
    await waitFor(() => expect(useRun).toHaveBeenLastCalledWith(expect.objectContaining({ stub: "tarrawarra", writeEveryDays: 1 })));
  });

  it("while running: follows the newest day, the scrubber is a locked progress bar", async () => {
    useRun.mockReturnValue({
      ...idle,
      status: { runId: "x", status: "running", daysWritten: 3, nDays: 5, rows: 1, cols: 2, dates },
      terrain,
      latest: { t: 2, moisture: Float32Array.from([1, 2]) },
    });
    render(<RunViewer />);
    expect(screen.getByRole("status").textContent).toBe("running");
    const slider = screen.getByRole("slider") as HTMLInputElement;
    expect(slider.disabled).toBe(true);
    expect(slider.value).toBe("2");
    expect(screen.getByText("d2")).toBeTruthy();
    expect((await screen.findByTestId("scene")).textContent).toBe("1x2:1,2");
  });

  it("when complete: scrubbing fetches that day through the hook and shows it", async () => {
    const fetchDay = vi.fn(async (t: number) => Float32Array.from([t, t * 10]));
    useRun.mockReturnValue({
      ...idle,
      status: { runId: "x", status: "complete", daysWritten: 5, nDays: 5, rows: 1, cols: 2, dates },
      terrain,
      latest: { t: 4, moisture: Float32Array.from([4, 40]) },
      fetchDay,
    });
    render(<RunViewer />);
    const slider = screen.getByRole("slider") as HTMLInputElement;
    expect(slider.disabled).toBe(false);
    expect((await screen.findByTestId("scene")).textContent).toBe("1x2:4,40");
    fireEvent.change(slider, { target: { value: "1" } });
    await waitFor(() => expect(screen.getByTestId("scene").textContent).toBe("1x2:1,10"));
    expect(fetchDay).toHaveBeenCalledWith(1);
    expect(screen.getByText("d1")).toBeTruthy();
    expect(screen.getByRole("button", { name: "play" })).toBeTruthy();
  });

  it("a scrubbed day from one run is not shown on another run's terrain after a site switch", async () => {
    const fetchDay = vi.fn(async (t: number) => Float32Array.from([t, t * 10]));
    useRun.mockReturnValue({
      ...idle,
      status: { runId: "esdale-1", status: "complete", daysWritten: 5, nDays: 5, rows: 1, cols: 2, dates },
      terrain,
      latest: { t: 4, moisture: Float32Array.from([4, 40]) },
      fetchDay,
    });
    const { rerender } = render(<RunViewer />);
    fireEvent.change(screen.getByRole("slider"), { target: { value: "1" } });
    await waitFor(() => expect(screen.getByTestId("scene").textContent).toBe("1x2:1,10"));

    // The next site's run: a different grid, no day fetched yet, scrubber reset by the hook being disabled.
    const other: TerrainGrid = { rows: 1, cols: 3, cellSize: 10, elevation: Float64Array.from([1, 2, 3]) };
    useRun.mockReturnValue({
      ...idle,
      status: { runId: "nerrigundah-1", status: "running", daysWritten: 0, nDays: 7, rows: 1, cols: 3, dates: [] },
      terrain: other,
      latest: null,
      fetchDay,
    });
    rerender(<RunViewer />);
    await waitFor(() => expect(screen.getByTestId("scene").textContent).toBe("1x3:none"));
  });

  it("shows the chart once a series exists, marked on the shown day, seekable only when complete", async () => {
    const seriesStub = { dates, rain: [0, 0, 0, 0, 0], pet: [1, 1, 1, 1, 1], moisture: [5, 5, 5, 5, 5] };
    useRunSeries.mockReturnValue({ series: seriesStub, error: null });
    useRun.mockReturnValue({
      ...idle,
      status: { runId: "x", status: "running", daysWritten: 3, nDays: 5, rows: 1, cols: 2, dates },
      terrain,
      latest: { t: 2, moisture: Float32Array.from([1, 2]) },
    });
    const { rerender } = render(<RunViewer />);
    expect(useRunSeries).toHaveBeenLastCalledWith("x", 3);
    const chart = screen.getByTestId("chart");
    expect(chart.dataset.day).toBe("2");
    expect(chart.dataset.seekable).toBe("no");

    useRun.mockReturnValue({
      ...idle,
      status: { runId: "x", status: "complete", daysWritten: 5, nDays: 5, rows: 1, cols: 2, dates },
      terrain,
      latest: { t: 4, moisture: Float32Array.from([4, 40]) },
    });
    rerender(<RunViewer />);
    expect(screen.getByTestId("chart").dataset.seekable).toBe("yes");
  });

  it("shows an error from the hook", () => {
    useRun.mockReturnValue({ ...idle, error: "POST /api/runs failed with status 404" });
    render(<RunViewer />);
    expect(screen.getByRole("alert").textContent).toContain("404");
  });
});
