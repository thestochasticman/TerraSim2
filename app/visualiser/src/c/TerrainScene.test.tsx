import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import type { TerrainGrid } from "@/t/TerrainGrid";

vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children, camera }: { children: ReactNode; camera: { position: number[] } }) => (
    <div data-testid="canvas" data-camera={JSON.stringify(camera.position)}>
      {children}
    </div>
  ),
}));

vi.mock("@react-three/drei", () => ({
  OrbitControls: ({ target }: { target: number[] }) => <div data-testid="orbit" data-target={JSON.stringify(target)} />,
}));

vi.mock("@/c/TerrainSurface", () => ({
  TerrainSurface: ({ grid, moisture }: { grid: TerrainGrid; moisture?: Float32Array }) => (
    <div data-testid="surface" data-moisture={moisture ? moisture.length : "none"}>{`${grid.rows}x${grid.cols}`}</div>
  ),
}));

vi.mock("@/c/ObservationMarkers", () => ({
  ObservationMarkers: ({ markers }: { markers: { count: number } }) => <div data-testid="markers" data-count={markers.count} />,
}));

const { TerrainScene } = await import("./TerrainScene");

describe("TerrainScene", () => {
  const grid: TerrainGrid = { rows: 3, cols: 5, cellSize: 10, elevation: Float64Array.from(new Array(15).fill(0)) };

  it("renders the surface for the given grid inside the canvas", () => {
    render(<TerrainScene grid={grid} />);
    expect(screen.getByTestId("canvas").contains(screen.getByTestId("surface"))).toBe(true);
    expect(screen.getByTestId("surface").textContent).toBe("3x5");
    expect(screen.getByTestId("surface").dataset.moisture).toBe("none");
  });

  it("passes a day's moisture through to the surface", () => {
    render(<TerrainScene grid={grid} moisture={new Float32Array(15)} />);
    expect(screen.getByTestId("surface").dataset.moisture).toBe("15");
  });

  it("draws observation markers inside the canvas when given a non-empty set", () => {
    const { rerender } = render(<TerrainScene grid={grid} />);
    expect(screen.queryByTestId("markers")).toBeNull();
    rerender(<TerrainScene grid={grid} markers={{ count: 0, positions: new Float32Array(0), colours: new Float32Array(0), radius: 1 }} />);
    expect(screen.queryByTestId("markers")).toBeNull();
    rerender(<TerrainScene grid={grid} markers={{ count: 2, positions: new Float32Array(6), colours: new Float32Array(6), radius: 1 }} />);
    expect(screen.getByTestId("canvas").contains(screen.getByTestId("markers"))).toBe(true);
    expect(screen.getByTestId("markers").dataset.count).toBe("2");
  });

  it("orbits around the grid centre and starts the camera framed to the grid", () => {
    render(<TerrainScene grid={grid} />);
    expect(JSON.parse(screen.getByTestId("orbit").dataset.target ?? "")).toEqual([20, 0, 10]);
    expect(JSON.parse(screen.getByTestId("canvas").dataset.camera ?? "")).toEqual([20, 32, 50]);
  });
});
