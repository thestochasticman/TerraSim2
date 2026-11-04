import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { TextureTriangleState } from "@/h/useTextureTriangle";
import type { TextureTriangle } from "@/t/TextureTriangle";

const useTextureTriangle = vi.fn<() => TextureTriangleState>();
vi.mock("@/h/useTextureTriangle", () => ({ useTextureTriangle: () => useTextureTriangle() }));
vi.mock("@/c/TextureTriangle", () => ({
  TextureTriangle: ({ data }: { data: TextureTriangle }) => <div data-testid="triangle">{data.points.sand.length} points</div>,
}));

const { TextureTriangleViewer } = await import("./TextureTriangleViewer");

describe("TextureTriangleViewer", () => {
  it("shows a status line while loading", () => {
    useTextureTriangle.mockReturnValue({ loading: true, data: null, error: null });
    render(<TextureTriangleViewer />);
    expect(screen.getByRole("status").textContent).toBe("Loading triangle…");
    expect(screen.queryByTestId("triangle")).toBeNull();
  });

  it("shows the error when loading fails", () => {
    useTextureTriangle.mockReturnValue({ loading: false, data: null, error: "status 500" });
    render(<TextureTriangleViewer />);
    expect(screen.getByRole("alert").textContent).toBe("Could not load triangle: status 500");
  });

  it("renders the triangle with the data once loaded", () => {
    const data: TextureTriangle = { textures: ["sand"], step: 100, points: { sand: [100], silt: [0], clay: [0], texture: [0], diameter: [317], psiE: [-0.4], b: [1] }, typical: [] };
    useTextureTriangle.mockReturnValue({ loading: false, data, error: null });
    render(<TextureTriangleViewer />);
    expect(screen.getByTestId("triangle").textContent).toBe("1 points");
  });
});
