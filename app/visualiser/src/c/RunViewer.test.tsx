import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { RunState } from "@/h/useRun";
import type { RunComparison } from "@/t/RunComparison";
import type { RunPairs } from "@/t/RunPairs";
import type { TerrainGrid } from "@/t/TerrainGrid";

const fetchSites = vi.fn();
const useRun = vi.fn<(request: unknown) => RunState>();
const useRunSeries = vi.fn<(runId: string | null, daysWritten: number) => { series: unknown; error: string | null }>();
const useRunComparison = vi.fn<(runId: string | null, daysWritten: number) => { comparison: RunComparison | null; pairs: RunPairs | null; error: string | null }>();

vi.mock("@/api/fetchSites", () => ({ fetchSites: () => fetchSites() }));
vi.mock("@/h/useRun", () => ({ useRun: (r: unknown) => useRun(r) }));
vi.mock("@/h/useRunSeries", () => ({ useRunSeries: (id: string | null, d: number) => useRunSeries(id, d) }));
vi.mock("@/h/useRunComparison", () => ({ useRunComparison: (id: string | null, d: number) => useRunComparison(id, d) }));
vi.mock("@/c/ComparisonView", () => ({
  ComparisonView: ({ day, onSeek }: { day: number | null; onSeek?: (d: number) => void }) => <div data-testid="comparison" data-day={day ?? "none"} data-seekable={onSeek ? "yes" : "no"} />,
}));
vi.mock("@/c/SeriesChart", () => ({
  SeriesChart: ({ day, onSeek }: { day: number | null; onSeek?: (d: number) => void }) => (
    <div data-testid="chart" data-day={day ?? "none"} data-seekable={onSeek ? "yes" : "no"} />
  ),
}));
vi.mock("@/c/TerrainScene", () => ({
  TerrainScene: ({ grid, moisture, colourBy, fullCapacity, markers }: { grid: TerrainGrid; moisture?: Float32Array; colourBy?: string; fullCapacity?: Float64Array; markers?: { count: number } }) => (
    <div data-testid="scene" data-colour-by={colourBy ?? "none"} data-full={fullCapacity ? Array.from(fullCapacity).join(",") : "none"} data-markers={markers ? markers.count : "none"}>{`${grid.rows}x${grid.cols}:${moisture ? Array.from(moisture).join(",") : "none"}`}</div>
  ),
}));

const { RunViewer } = await import("./RunViewer");

const scores = { observedMean: 0.3, modelledMean: 0.2, bias: -0.1, rmse: 0.1, ubrmse: 0, r: null, nse: null, kge: null };
const comparison: RunComparison = { daysWritten: 5, nPoints: 3, nPaired: 3, rootDepth: 0.3, layers: [{ top: 0, bottom: 0.3, n: 3 }], stations: ["a", "b"], overall: { n: 3, ...scores }, byDate: [{ date: "d2", t: 2, n: 2, ...scores }], byStation: [] };
const pairs: RunPairs = { t: Float32Array.from([2, 2, 0]), row: Float32Array.from([0, 0, 0]), col: Float32Array.from([0, 1, 1]), station: Float32Array.from([0, 1, 1]), observed: Float32Array.from([0.2, 0.4, 0.3]), modelled: Float32Array.from([0.3, 0.3, 0.3]) };

const terrain: TerrainGrid = { rows: 1, cols: 2, cellSize: 10, elevation: Float64Array.from([1, 2]) };
const idle: RunState = { status: null, terrain: null, latest: null, error: null, fetchDay: async () => new Float32Array() };
const dates = ["d0", "d1", "d2", "d3", "d4"];

describe("RunViewer", () => {
  beforeEach(() => {
    fetchSites.mockReset().mockResolvedValue(["example", "tarrawarra"]);
    useRun.mockReset().mockReturnValue(idle);
    useRunSeries.mockReset().mockReturnValue({ series: null, error: null });
    useRunComparison.mockReset().mockReturnValue({ comparison: null, pairs: null, error: null });
  });

  const completeRun = (): RunState => ({
    ...idle,
    status: { runId: "x", status: "complete", daysWritten: 5, nDays: 5, rows: 1, cols: 2, dates },
    terrain,
    latest: { t: 4, moisture: Float32Array.from([1, 2]) },
  });

  it("a site without observations shows no observations select and no comparison", async () => {
    useRun.mockReturnValue(completeRun());
    render(<RunViewer />);
    await waitFor(() => expect(screen.getByTestId("scene")).toBeTruthy());
    expect(screen.queryByRole("combobox", { name: "observations" })).toBeNull();
    expect(screen.queryByTestId("comparison")).toBeNull();
    expect(screen.getByTestId("scene").dataset.markers).toBe("none");
  });

  it("with observations: the day's markers go to the scene coloured by observed content, the comparison follows the day, and the select can hide them or show the error", async () => {
    useRun.mockReturnValue(completeRun());
    useRunComparison.mockReturnValue({ comparison, pairs, error: null });
    render(<RunViewer />);
    await waitFor(() => expect(screen.getByTestId("comparison")).toBeTruthy());
    expect(useRunComparison).toHaveBeenLastCalledWith("x", 5);
    expect(screen.getByTestId("scene").dataset.markers).toBe("none");
    expect(screen.getByTestId("comparison").dataset.day).toBe("4");
    expect(screen.getByTestId("comparison").dataset.seekable).toBe("yes");
    expect(screen.getByTestId("observed-legend").textContent).toContain("0.20 to 0.40");

    fireEvent.change(screen.getByRole("slider"), { target: { value: "2" } });
    await waitFor(() => expect(screen.getByTestId("scene").dataset.markers).toBe("2"));
    expect(screen.getByTestId("comparison").dataset.day).toBe("2");

    fireEvent.change(screen.getByRole("combobox", { name: "observations" }), { target: { value: "error" } });
    expect(screen.getByTestId("scene").dataset.markers).toBe("2");
    expect(screen.getByTestId("error-legend").textContent).toContain("0.10");
    expect(screen.queryByTestId("observed-legend")).toBeNull();

    fireEvent.change(screen.getByRole("combobox", { name: "observations" }), { target: { value: "none" } });
    expect(screen.getByTestId("scene").dataset.markers).toBe("none");
  });

  const select = () => screen.getByRole("combobox", { name: "site" }) as HTMLSelectElement;

  it("lists sites, defaults to the first, and shows no run and no scrubber until started", async () => {
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    expect(within(select()).getAllByRole("option").map((o) => o.textContent)).toEqual(["example", "tarrawarra"]);
    expect(screen.getByRole("status").textContent).toBe("no run");
    expect(screen.queryByRole("slider")).toBeNull();
    expect(useRun).toHaveBeenLastCalledWith(null);
  });

  it("starting a run passes a request for the chosen site to the hook", async () => {
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    fireEvent.change(select(), { target: { value: "tarrawarra" } });
    fireEvent.click(screen.getByRole("button", { name: "run" }));
    await waitFor(() => expect(useRun).toHaveBeenLastCalledWith(expect.objectContaining({ stub: "tarrawarra", writeEveryDays: 1, rootDepth: 0.3, step: "bucket" })));
  });

  it("the model select goes into the request", async () => {
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    fireEvent.change(screen.getByRole("combobox", { name: "model" }), { target: { value: "routed" } });
    fireEvent.click(screen.getByRole("button", { name: "run" }));
    await waitFor(() => expect(useRun).toHaveBeenLastCalledWith(expect.objectContaining({ step: "routed" })));
  });

  it("the subsurface model shows its leak and rain-hours fields and sends them", async () => {
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    expect(screen.queryByLabelText("leak fraction")).toBeNull();
    fireEvent.change(screen.getByRole("combobox", { name: "model" }), { target: { value: "subsurface" } });
    fireEvent.change(screen.getByLabelText("leak fraction"), { target: { value: "0.2" } });
    fireEvent.change(screen.getByLabelText("rain hours"), { target: { value: "6" } });
    fireEvent.change(screen.getByLabelText("lateral multiplier"), { target: { value: "30" } });
    fireEvent.click(screen.getByRole("button", { name: "run" }));
    await waitFor(() => expect(useRun).toHaveBeenLastCalledWith(expect.objectContaining({ step: "subsurface", leakFraction: 0.2, rainHours: 6, lateralMultiplier: 30 })));
  });

  it("the tree root depth is null until set, goes into the request, and clears back to null", async () => {
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    fireEvent.click(screen.getByRole("button", { name: "run" }));
    await waitFor(() => expect(useRun).toHaveBeenLastCalledWith(expect.objectContaining({ rootDepth: 0.3, treeRootDepth: null })));
    fireEvent.change(screen.getByLabelText("tree root depth"), { target: { value: "1.5" } });
    fireEvent.click(screen.getByRole("button", { name: "run" }));
    await waitFor(() => expect(useRun).toHaveBeenLastCalledWith(expect.objectContaining({ treeRootDepth: 1.5 })));
    fireEvent.change(screen.getByLabelText("tree root depth"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: "run" }));
    await waitFor(() => expect(useRun).toHaveBeenLastCalledWith(expect.objectContaining({ treeRootDepth: null })));
  });

  it("offers the vegetation colouring only when the terrain has a map, with a legend naming the classes", async () => {
    useRun.mockReturnValue(completeRun());
    render(<RunViewer />);
    await waitFor(() => expect(screen.getByTestId("scene")).toBeTruthy());
    expect(within(screen.getByRole("combobox", { name: "colour by" })).queryByRole("option", { name: /vegetation/ })).toBeNull();
    useRun.mockReturnValue({ ...completeRun(), terrain: { ...terrain, vegetation: Float64Array.from([0, 1]), vegetationClasses: ["grass", "tree"] } });
    fireEvent.change(select(), { target: { value: "tarrawarra" } });
    await waitFor(() => expect(within(screen.getByRole("combobox", { name: "colour by" })).getByRole("option", { name: /vegetation/ })).toBeTruthy());
    fireEvent.change(screen.getByRole("combobox", { name: "colour by" }), { target: { value: "vegetation" } });
    expect(screen.getByTestId("scene").dataset.colourBy).toBe("vegetation");
    expect(screen.getByTestId("vegetation-legend").textContent).toContain("grass");
    expect(screen.getByTestId("vegetation-legend").textContent).toContain("tree");
  });

  it("the root depth field goes into the request, and an empty one disables the run button", async () => {
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    fireEvent.change(screen.getByLabelText("root depth"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "run" }));
    await waitFor(() => expect(useRun).toHaveBeenLastCalledWith(expect.objectContaining({ rootDepth: 1 })));
    fireEvent.change(screen.getByLabelText("root depth"), { target: { value: "" } });
    expect((screen.getByRole("button", { name: "run" }) as HTMLButtonElement).disabled).toBe(true);
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

  it("the colour select switches the scene to capacity and shows the capacity range", async () => {
    const withCapacity: TerrainGrid = { ...terrain, capacity: Float64Array.from([12.4, 57.6]) };
    useRun.mockReturnValue({
      ...idle,
      status: { runId: "x", status: "complete", daysWritten: 5, nDays: 5, rows: 1, cols: 2, dates },
      terrain: withCapacity,
      latest: { t: 4, moisture: Float32Array.from([1, 2]) },
    });
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    expect(screen.getByTestId("scene").getAttribute("data-colour-by")).toBe("moisture");
    expect(screen.queryByTestId("capacity-legend")).toBeNull();
    fireEvent.change(screen.getByRole("combobox", { name: "colour by" }), { target: { value: "capacity" } });
    expect(screen.getByTestId("scene").getAttribute("data-colour-by")).toBe("capacity");
    expect(screen.getByTestId("capacity-legend").textContent).toBe("capacity 12 to 58 mm, light to dark");
  });

  it("a subsurface run measures fullness over the plant store plus the free store", async () => {
    const withFree: TerrainGrid = { ...terrain, capacity: Float64Array.from([40, 40]), freeCapacity: Float64Array.from([60, 70]) };
    useRun.mockReturnValue({ ...idle, status: { runId: "x", status: "complete", daysWritten: 5, nDays: 5, rows: 1, cols: 2, dates }, terrain: withFree, latest: { t: 4, moisture: Float32Array.from([1, 2]) } });
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    expect(screen.getByTestId("scene").getAttribute("data-full")).toBe("none");
    fireEvent.change(screen.getByRole("combobox", { name: "model" }), { target: { value: "subsurface" } });
    fireEvent.click(screen.getByRole("button", { name: "run" }));
    await waitFor(() => expect(screen.getByTestId("scene").getAttribute("data-full")).toBe("100,110"));
  });

  it("the relative option passes through and shows the day's range", async () => {
    useRun.mockReturnValue({ ...idle, status: { runId: "x", status: "complete", daysWritten: 5, nDays: 5, rows: 1, cols: 2, dates }, terrain, latest: { t: 4, moisture: Float32Array.from([10.25, 12.75]) } });
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    fireEvent.change(screen.getByRole("combobox", { name: "colour by" }), { target: { value: "relative" } });
    expect(screen.getByTestId("scene").getAttribute("data-colour-by")).toBe("relative");
    expect(screen.getByTestId("relative-legend").textContent).toBe("10.3 to 12.8 mm this day, light to dark");
  });

  it("the drainage option colours by upslope cells and shows their range", async () => {
    const withUpslope: TerrainGrid = { ...terrain, upslopeCells: Float64Array.from([1, 2]) };
    useRun.mockReturnValue({ ...idle, status: { runId: "x", status: "complete", daysWritten: 5, nDays: 5, rows: 1, cols: 2, dates }, terrain: withUpslope, latest: null });
    render(<RunViewer />);
    await waitFor(() => expect(select().disabled).toBe(false));
    fireEvent.change(screen.getByRole("combobox", { name: "colour by" }), { target: { value: "upslope" } });
    expect(screen.getByTestId("scene").getAttribute("data-colour-by")).toBe("upslope");
    expect(screen.getByTestId("upslope-legend").textContent).toContain("1 to 2 cells drain through");
  });
});
