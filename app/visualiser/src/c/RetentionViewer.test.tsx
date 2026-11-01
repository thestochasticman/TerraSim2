import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { RetentionCurvesState } from "@/h/useRetentionCurves";
import type { RetentionCurves } from "@/t/RetentionCurves";

const useRetentionCurves = vi.fn<() => RetentionCurvesState>();
vi.mock("@/h/useRetentionCurves", () => ({ useRetentionCurves: () => useRetentionCurves() }));
vi.mock("@/c/RetentionChart", () => ({
  RetentionChart: ({ data }: { data: RetentionCurves }) => <div data-testid="chart">{data.models.campbell.length} textures</div>,
}));

const { RetentionViewer } = await import("./RetentionViewer");

describe("RetentionViewer", () => {
  it("shows a status line while loading", () => {
    useRetentionCurves.mockReturnValue({ loading: true, data: null, error: null });
    render(<RetentionViewer />);
    expect(screen.getByRole("status").textContent).toBe("Loading curves…");
    expect(screen.queryByTestId("chart")).toBeNull();
  });

  it("shows the error when loading fails", () => {
    useRetentionCurves.mockReturnValue({ loading: false, data: null, error: "status 500" });
    render(<RetentionViewer />);
    expect(screen.getByRole("alert").textContent).toBe("Could not load curves: status 500");
  });

  it("renders the chart with the data once loaded", () => {
    const data: RetentionCurves = { suction: [1, 10], fieldCapacity: 33, wiltingPoint: 1500, models: { campbell: [{ texture: "sand", theta: [0.3, 0.1], thetaFc: 0.04, thetaPwp: 0.004, availableWater: 36 }], van_genuchten: [{ texture: "sand", theta: [0.3, 0.1], thetaFc: 0.06, thetaPwp: 0.02, availableWater: 38 }] } };
    useRetentionCurves.mockReturnValue({ loading: false, data, error: null });
    render(<RetentionViewer />);
    expect(screen.getByTestId("chart").textContent).toBe("1 textures");
    expect(screen.getByRole("heading").textContent).toContain("retention");
  });
});
