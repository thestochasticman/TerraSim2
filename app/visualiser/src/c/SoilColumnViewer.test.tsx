import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SoilColumnState } from "@/h/useSoilColumn";
import type { SoilColumn } from "@/t/SoilColumn";

const useSoilColumn = vi.fn<(t: string[], d: number, m: string) => SoilColumnState>();
vi.mock("@/h/useSoilColumn", () => ({ useSoilColumn: (t: string[], d: number, m: string) => useSoilColumn(t, d, m) }));
vi.mock("@/c/SoilColumnChart", () => ({
  SoilColumnChart: ({ column }: { column: SoilColumn }) => <div data-testid="chart">{column.total} mm</div>,
}));

const { SoilColumnViewer } = await import("./SoilColumnViewer");

const column: SoilColumn = { textures: ["sand"], layerBounds: [0, 1], rootDepth: 0.6, model: "campbell", layers: [], total: 42 };

describe("SoilColumnViewer", () => {
  beforeEach(() => useSoilColumn.mockReset());

  it("asks the hook for the initial sand-over-clay column and renders the chart", () => {
    useSoilColumn.mockReturnValue({ data: column, error: null });
    render(<SoilColumnViewer />);
    expect(useSoilColumn).toHaveBeenLastCalledWith(["sand", "sand", "sandy loam", "clay loam", "clay", "clay"], 0.6, "campbell");
    expect(screen.getByTestId("chart").textContent).toBe("42 mm");
    expect(screen.getAllByRole("combobox")).toHaveLength(6);
  });

  it("changing a layer, the depth or the model asks the hook again", () => {
    useSoilColumn.mockReturnValue({ data: column, error: null });
    render(<SoilColumnViewer />);
    fireEvent.change(screen.getByLabelText("texture 0–5 cm"), { target: { value: "clay" } });
    expect(useSoilColumn).toHaveBeenLastCalledWith(["clay", "sand", "sandy loam", "clay loam", "clay", "clay"], 0.6, "campbell");
    fireEvent.change(screen.getByLabelText("root depth"), { target: { value: "1.5" } });
    expect(useSoilColumn).toHaveBeenLastCalledWith(expect.anything(), 1.5, "campbell");
    fireEvent.click(screen.getByLabelText("van Genuchten"));
    expect(useSoilColumn).toHaveBeenLastCalledWith(expect.anything(), 1.5, "van_genuchten");
  });

  it("shows a status line before the first column and the error when a fetch fails", () => {
    useSoilColumn.mockReturnValue({ data: null, error: null });
    const { rerender } = render(<SoilColumnViewer />);
    expect(screen.getByRole("status").textContent).toBe("Loading column…");
    useSoilColumn.mockReturnValue({ data: column, error: "status 422" });
    rerender(<SoilColumnViewer />);
    expect(screen.getByRole("alert").textContent).toBe("Could not load column: status 422");
    expect(screen.getByTestId("chart")).not.toBeNull();
  });
});
