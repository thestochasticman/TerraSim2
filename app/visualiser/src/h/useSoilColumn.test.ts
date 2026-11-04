import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchSoilColumn = vi.fn();
vi.mock("@/api/fetchSoilColumn", () => ({ fetchSoilColumn: (...a: unknown[]) => fetchSoilColumn(...a) }));

const { useSoilColumn } = await import("./useSoilColumn");

const settle = () => act(async () => { await Promise.resolve(); await Promise.resolve(); });
const column = (total: number) => ({ textures: [], layerBounds: [0, 1], rootDepth: 1, model: "campbell", layers: [], total });

describe("useSoilColumn", () => {
  beforeEach(() => fetchSoilColumn.mockReset());

  it("fetches on mount with the inputs and again when they change", async () => {
    fetchSoilColumn.mockResolvedValueOnce(column(1)).mockResolvedValueOnce(column(2));
    const { result, rerender } = renderHook(({ t, d }) => useSoilColumn(t, d, "campbell"), { initialProps: { t: ["sand", "clay"], d: 0.5 } });
    await settle();
    expect(fetchSoilColumn).toHaveBeenLastCalledWith(["sand", "clay"], 0.5, "campbell");
    expect(result.current.data?.total).toBe(1);
    rerender({ t: ["sand", "clay"], d: 0.8 });
    await settle();
    expect(result.current.data?.total).toBe(2);
    expect(fetchSoilColumn).toHaveBeenCalledTimes(2);
  });

  it("an equal textures array does not refetch, and a failure keeps the last column", async () => {
    fetchSoilColumn.mockResolvedValueOnce(column(1)).mockRejectedValueOnce(new Error("status 422"));
    const { result, rerender } = renderHook(({ t, d }) => useSoilColumn(t, d, "campbell"), { initialProps: { t: ["sand"], d: 0.5 } });
    await settle();
    rerender({ t: ["sand"], d: 0.5 });
    await settle();
    expect(fetchSoilColumn).toHaveBeenCalledTimes(1);
    rerender({ t: ["sand"], d: 0.9 });
    await settle();
    expect(result.current.error).toBe("status 422");
    expect(result.current.data?.total).toBe(1);
  });
});
