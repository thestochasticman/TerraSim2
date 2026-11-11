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
  TerrainSurface: ({ grid, moisture, opacity }: { grid: TerrainGrid; moisture?: Float32Array; opacity?: number }) => (
    <div data-testid="surface" data-moisture={moisture ? moisture.length : "none"} data-opacity={opacity ?? "none"}>{`${grid.rows}x${grid.cols}`}</div>
  ),
}));

vi.mock("@/c/BucketColumns", () => ({
  BucketColumns: ({ buckets }: { buckets: { count: number } }) => <div data-testid="buckets" data-count={buckets.count} />,
}));

vi.mock("@/c/ObservationMarkers", () => ({
  ObservationMarkers: ({ markers }: { markers: { count: number } }) => <div data-testid="markers" data-count={markers.count} />,
}));

const { TerrainScene, SURFACE_OPACITY_OVER_BUCKETS } = await import("./TerrainScene");

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

  it("hangs bucket columns inside the canvas when given a non-empty set, and makes the surface translucent over them", () => {
    const empty = { count: 0, block: 1, size: 8, tops: new Float32Array(0), plantDepth: new Float32Array(0), freeDepth: new Float32Array(0), plantFill: new Float32Array(0), freeFill: new Float32Array(0) };
    const { rerender } = render(<TerrainScene grid={grid} />);
    expect(screen.queryByTestId("buckets")).toBeNull();
    expect(screen.getByTestId("surface").dataset.opacity).toBe("1");
    rerender(<TerrainScene grid={grid} buckets={empty} />);
    expect(screen.queryByTestId("buckets")).toBeNull();
    expect(screen.getByTestId("surface").dataset.opacity).toBe("1");
    rerender(<TerrainScene grid={grid} buckets={{ ...empty, count: 3, tops: new Float32Array(9), plantDepth: new Float32Array(3), freeDepth: new Float32Array(3), plantFill: new Float32Array(3), freeFill: new Float32Array(3) }} />);
    expect(screen.getByTestId("canvas").contains(screen.getByTestId("buckets"))).toBe(true);
    expect(screen.getByTestId("buckets").dataset.count).toBe("3");
    expect(screen.getByTestId("surface").dataset.opacity).toBe(String(SURFACE_OPACITY_OVER_BUCKETS));
  });

  it("orbits around the grid centre and starts the camera framed to the grid", () => {
    render(<TerrainScene grid={grid} />);
    expect(JSON.parse(screen.getByTestId("orbit").dataset.target ?? "")).toEqual([20, -6, 10]);
    expect(JSON.parse(screen.getByTestId("canvas").dataset.camera ?? "")).toEqual([20, 26, 50]);
  });
});
