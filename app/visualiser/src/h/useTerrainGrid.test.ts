import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useTerrainGrid } from "./useTerrainGrid";

const validJson = {
  rows: 2,
  cols: 2,
  cell_size: 5,
  elevation: [
    [1, 2],
    [3, 4],
  ],
};

function respondWith(body: unknown, ok = true, status = 200): Response {
  return { ok, status, json: async () => body } as unknown as Response;
}

describe("useTerrainGrid", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("starts loading with no grid and no error", () => {
    fetchMock.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useTerrainGrid("/terrain/a.json"));
    expect(result.current).toEqual({ loading: true, grid: null, error: null });
    expect(fetchMock).toHaveBeenCalledWith("/terrain/a.json");
  });

  it("exposes the parsed grid on success", async () => {
    fetchMock.mockResolvedValue(respondWith(validJson));
    const { result } = renderHook(() => useTerrainGrid("/terrain/a.json"));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBeNull();
    expect(result.current.grid?.rows).toBe(2);
    expect(result.current.grid?.cellSize).toBe(5);
    expect(Array.from(result.current.grid?.elevation ?? [])).toEqual([1, 2, 3, 4]);
  });

  it("reports an HTTP failure as an error", async () => {
    fetchMock.mockResolvedValue(respondWith({}, false, 404));
    const { result } = renderHook(() => useTerrainGrid("/terrain/missing.json"));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.grid).toBeNull();
    expect(result.current.error).toBe("fetch of /terrain/missing.json failed with status 404");
  });

  it("reports an invalid terrain file as an error", async () => {
    fetchMock.mockResolvedValue(respondWith({ ...validJson, cell_size: -1 }));
    const { result } = renderHook(() => useTerrainGrid("/terrain/bad.json"));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.grid).toBeNull();
    expect(result.current.error).toBe("cell_size must be a positive finite number");
  });

  it("reports a network failure as an error", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    const { result } = renderHook(() => useTerrainGrid("/terrain/a.json"));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe("Failed to fetch");
  });

  it("refetches when the url changes and ignores the stale response", async () => {
    let resolveFirst: (r: Response) => void = () => {};
    fetchMock
      .mockReturnValueOnce(new Promise<Response>((resolve) => (resolveFirst = resolve)))
      .mockResolvedValueOnce(respondWith({ ...validJson, rows: 1, elevation: [[9, 9]] }));

    const { result, rerender } = renderHook(({ url }) => useTerrainGrid(url), {
      initialProps: { url: "/terrain/first.json" },
    });
    rerender({ url: "/terrain/second.json" });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.grid?.rows).toBe(1);

    resolveFirst(respondWith(validJson));
    await new Promise((r) => setTimeout(r, 0));
    expect(result.current.grid?.rows).toBe(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
