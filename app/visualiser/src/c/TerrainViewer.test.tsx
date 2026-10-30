import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { TerrainGridState } from "@/h/useTerrainGrid";
import type { TerrainGrid } from "@/t/TerrainGrid";

const useTerrainGrid = vi.fn<(url: string) => TerrainGridState>();

vi.mock("@/h/useTerrainGrid", () => ({
  useTerrainGrid: (url: string) => useTerrainGrid(url),
}));

vi.mock("@/c/TerrainScene", () => ({
  TerrainScene: ({ grid }: { grid: TerrainGrid }) => <div data-testid="scene">{`${grid.rows}x${grid.cols}`}</div>,
}));

const { TerrainViewer } = await import("./TerrainViewer");

describe("TerrainViewer", () => {
  it("asks the hook for the given url", () => {
    useTerrainGrid.mockReturnValue({ loading: true, grid: null, error: null });
    render(<TerrainViewer url="/terrain/sample.json" />);
    expect(useTerrainGrid).toHaveBeenCalledWith("/terrain/sample.json");
  });

  it("shows a status line while loading", () => {
    useTerrainGrid.mockReturnValue({ loading: true, grid: null, error: null });
    render(<TerrainViewer url="/terrain/sample.json" />);
    expect(screen.getByRole("status").textContent).toBe("Loading terrain…");
    expect(screen.queryByTestId("scene")).toBeNull();
  });

  it("shows the error when loading fails", () => {
    useTerrainGrid.mockReturnValue({ loading: false, grid: null, error: "cell_size must be a positive finite number" });
    render(<TerrainViewer url="/terrain/sample.json" />);
    expect(screen.getByRole("alert").textContent).toBe("Could not load terrain: cell_size must be a positive finite number");
    expect(screen.queryByTestId("scene")).toBeNull();
  });

  it("renders the scene with the grid once loaded", async () => {
    const grid: TerrainGrid = { rows: 2, cols: 3, cellSize: 1, elevation: Float64Array.from([0, 0, 0, 0, 0, 0]) };
    useTerrainGrid.mockReturnValue({ loading: false, grid, error: null });
    render(<TerrainViewer url="/terrain/sample.json" />);
    expect((await screen.findByTestId("scene")).textContent).toBe("2x3");
    expect(screen.queryByRole("status")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
