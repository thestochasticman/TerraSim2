import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchTextureTriangle = vi.fn();
vi.mock("@/api/fetchTextureTriangle", () => ({ fetchTextureTriangle: () => fetchTextureTriangle() }));

const { useTextureTriangle } = await import("./useTextureTriangle");

const settle = () => act(async () => { await Promise.resolve(); await Promise.resolve(); });
const data = { textures: ["sand"], step: 100, points: { sand: [100], silt: [0], clay: [0], texture: [0], diameter: [317], psiE: [-0.4], b: [1] }, typical: [] };

describe("useTextureTriangle", () => {
  beforeEach(() => fetchTextureTriangle.mockReset());

  it("starts loading and exposes the data once fetched", async () => {
    fetchTextureTriangle.mockResolvedValueOnce(data);
    const { result } = renderHook(() => useTextureTriangle());
    expect(result.current).toEqual({ loading: true, data: null, error: null });
    await settle();
    expect(result.current).toEqual({ loading: false, data, error: null });
    expect(fetchTextureTriangle).toHaveBeenCalledTimes(1);
  });

  it("exposes the error message when the fetch fails", async () => {
    fetchTextureTriangle.mockRejectedValueOnce(new Error("status 500"));
    const { result } = renderHook(() => useTextureTriangle());
    await settle();
    expect(result.current).toEqual({ loading: false, data: null, error: "status 500" });
  });
});
