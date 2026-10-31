import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchRunSeries = vi.fn();
vi.mock("@/api/fetchRunSeries", () => ({ fetchRunSeries: (...a: unknown[]) => fetchRunSeries(...a) }));

const { useRunSeries } = await import("./useRunSeries");

const settle = () => act(async () => { await Promise.resolve(); await Promise.resolve(); });
const series = (n: number) => ({ dates: Array.from({ length: n }, (_, i) => `d${i}`), rain: new Array(n).fill(1), pet: new Array(n).fill(2), moisture: new Array(n).fill(3) });

describe("useRunSeries", () => {
  beforeEach(() => fetchRunSeries.mockReset());

  it("fetches nothing without a run or before any day is written", async () => {
    const { result, rerender } = renderHook(({ id, d }) => useRunSeries(id, d), { initialProps: { id: null as string | null, d: 0 } });
    await settle();
    rerender({ id: "x", d: 0 });
    await settle();
    expect(fetchRunSeries).not.toHaveBeenCalled();
    expect(result.current.series).toBeNull();
  });

  it("refetches when daysWritten changes and exposes the latest series", async () => {
    fetchRunSeries.mockResolvedValueOnce(series(2)).mockResolvedValueOnce(series(5));
    const { result, rerender } = renderHook(({ d }) => useRunSeries("x", d), { initialProps: { d: 2 } });
    await settle();
    expect(result.current.series?.dates.length).toBe(2);
    rerender({ d: 5 });
    await settle();
    expect(result.current.series?.dates.length).toBe(5);
    expect(fetchRunSeries).toHaveBeenCalledTimes(2);
  });

  it("a new run reads as empty until its own series arrives", async () => {
    fetchRunSeries.mockResolvedValueOnce(series(3)).mockResolvedValueOnce(series(1));
    const { result, rerender } = renderHook(({ id }) => useRunSeries(id, 3), { initialProps: { id: "x" } });
    await settle();
    expect(result.current.series?.dates.length).toBe(3);
    rerender({ id: "y" });
    expect(result.current.series).toBeNull();
    await settle();
    expect(result.current.series?.dates.length).toBe(1);
  });

  it("reports a failed fetch and keeps the previous series of the same run", async () => {
    fetchRunSeries.mockResolvedValueOnce(series(2)).mockRejectedValueOnce(new Error("status 500"));
    const { result, rerender } = renderHook(({ d }) => useRunSeries("x", d), { initialProps: { d: 2 } });
    await settle();
    rerender({ d: 3 });
    await settle();
    expect(result.current.error).toContain("500");
    expect(result.current.series?.dates.length).toBe(2);
  });
});
