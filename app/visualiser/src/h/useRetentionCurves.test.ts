import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchRetentionCurves = vi.fn();
vi.mock("@/api/fetchRetentionCurves", () => ({ fetchRetentionCurves: () => fetchRetentionCurves() }));

const { useRetentionCurves } = await import("./useRetentionCurves");

const settle = () => act(async () => { await Promise.resolve(); await Promise.resolve(); });
const data = { suction: [1, 10], fieldCapacity: 33, wiltingPoint: 1500, models: { campbell: [], van_genuchten: [] } };

describe("useRetentionCurves", () => {
  beforeEach(() => fetchRetentionCurves.mockReset());

  it("starts loading and exposes the data once fetched", async () => {
    fetchRetentionCurves.mockResolvedValueOnce(data);
    const { result } = renderHook(() => useRetentionCurves());
    expect(result.current).toEqual({ loading: true, data: null, error: null });
    await settle();
    expect(result.current).toEqual({ loading: false, data, error: null });
    expect(fetchRetentionCurves).toHaveBeenCalledTimes(1);
  });

  it("exposes the error message when the fetch fails", async () => {
    fetchRetentionCurves.mockRejectedValueOnce(new Error("status 500"));
    const { result } = renderHook(() => useRetentionCurves());
    await settle();
    expect(result.current).toEqual({ loading: false, data: null, error: "status 500" });
  });
});
