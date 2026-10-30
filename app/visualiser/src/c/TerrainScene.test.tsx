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
  TerrainSurface: ({ grid }: { grid: TerrainGrid }) => <div data-testid="surface">{`${grid.rows}x${grid.cols}`}</div>,
}));

const { TerrainScene } = await import("./TerrainScene");

describe("TerrainScene", () => {
  const grid: TerrainGrid = { rows: 3, cols: 5, cellSize: 10, elevation: Float64Array.from(new Array(15).fill(0)) };

  it("renders the surface for the given grid inside the canvas", () => {
    render(<TerrainScene grid={grid} />);
    expect(screen.getByTestId("canvas").contains(screen.getByTestId("surface"))).toBe(true);
    expect(screen.getByTestId("surface").textContent).toBe("3x5");
  });

  it("orbits around the grid centre and starts the camera framed to the grid", () => {
    render(<TerrainScene grid={grid} />);
    expect(JSON.parse(screen.getByTestId("orbit").dataset.target ?? "")).toEqual([20, 0, 10]);
    expect(JSON.parse(screen.getByTestId("canvas").dataset.camera ?? "")).toEqual([20, 32, 50]);
  });
});
