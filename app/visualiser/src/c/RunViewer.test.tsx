import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { RunState } from "@/h/useRun";
import type { TerrainGrid } from "@/t/TerrainGrid";

const fetchSites = vi.fn();
const useRun = vi.fn<(request: unknown) => RunState>();

vi.mock("@/api/fetchSites", () => ({ fetchSites: () => fetchSites() }));
vi.mock("@/h/useRun", () => ({ useRun: (r: unknown) => useRun(r) }));
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

  it("shows an error from the hook", () => {
    useRun.mockReturnValue({ ...idle, error: "POST /api/runs failed with status 404" });
    render(<RunViewer />);
    expect(screen.getByRole("alert").textContent).toContain("404");
  });
});
