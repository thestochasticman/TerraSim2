import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchRunComparison = vi.fn();
const fetchRunPairs = vi.fn();
vi.mock("@/api/fetchRunComparison", () => ({ fetchRunComparison: (...a: unknown[]) => fetchRunComparison(...a) }));
vi.mock("@/api/fetchRunPairs", () => ({ fetchRunPairs: (...a: unknown[]) => fetchRunPairs(...a) }));

const { useRunComparison } = await import("./useRunComparison");

const settle = () => act(async () => { await Promise.resolve(); await Promise.resolve(); await Promise.resolve(); });
const comparison = (paired: number) => ({ daysWritten: paired, nPoints: 10, nPaired: paired, rootDepth: 0.3, layers: [], stations: [], overall: { n: paired }, byDate: [], byStation: [] });
const pairs = (n: number) => ({ t: new Float32Array(n), row: new Float32Array(n), col: new Float32Array(n), station: new Float32Array(n), observed: new Float32Array(n), modelled: new Float32Array(n) });

describe("useRunComparison", () => {
  beforeEach(() => {
    fetchRunComparison.mockReset();
    fetchRunPairs.mockReset();
  });

  it("fetches nothing without a run or before any day is written", async () => {
    const { result, rerender } = renderHook(({ id, d }) => useRunComparison(id, d), { initialProps: { id: null as string | null, d: 0 } });
    await settle();
    rerender({ id: "x", d: 0 });
    await settle();
    expect(fetchRunComparison).not.toHaveBeenCalled();
    expect(result.current.comparison).toBeNull();
    expect(result.current.pairs).toBeNull();
  });

  it("refetches both when daysWritten changes and exposes the latest", async () => {
    fetchRunComparison.mockResolvedValueOnce(comparison(2)).mockResolvedValueOnce(comparison(5));
    fetchRunPairs.mockResolvedValueOnce(pairs(2)).mockResolvedValueOnce(pairs(5));
    const { result, rerender } = renderHook(({ d }) => useRunComparison("x", d), { initialProps: { d: 2 } });
    await settle();
    expect(result.current.comparison?.nPaired).toBe(2);
    expect(result.current.pairs?.t.length).toBe(2);
    rerender({ d: 5 });
    await settle();
    expect(result.current.comparison?.nPaired).toBe(5);
    expect(result.current.pairs?.t.length).toBe(5);
    expect(fetchRunComparison).toHaveBeenCalledTimes(2);
    expect(fetchRunPairs).toHaveBeenCalledTimes(2);
  });

  it("a site without observations reads as null without an error", async () => {
    fetchRunComparison.mockResolvedValue(null);
    fetchRunPairs.mockResolvedValue(null);
    const { result } = renderHook(() => useRunComparison("x", 3));
    await settle();
    expect(result.current.comparison).toBeNull();
    expect(result.current.pairs).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("a new run reads as empty until its own response arrives", async () => {
    fetchRunComparison.mockResolvedValueOnce(comparison(3)).mockResolvedValueOnce(comparison(1));
    fetchRunPairs.mockResolvedValueOnce(pairs(3)).mockResolvedValueOnce(pairs(1));
    const { result, rerender } = renderHook(({ id }) => useRunComparison(id, 3), { initialProps: { id: "x" } });
    await settle();
    expect(result.current.comparison?.nPaired).toBe(3);
    rerender({ id: "y" });
    expect(result.current.comparison).toBeNull();
    await settle();
    expect(result.current.comparison?.nPaired).toBe(1);
  });

  it("reports a failed fetch and keeps the previous result of the same run", async () => {
    fetchRunComparison.mockResolvedValueOnce(comparison(2)).mockRejectedValueOnce(new Error("status 500"));
    fetchRunPairs.mockResolvedValue(pairs(2));
    const { result, rerender } = renderHook(({ d }) => useRunComparison("x", d), { initialProps: { d: 2 } });
    await settle();
    rerender({ d: 3 });
    await settle();
    expect(result.current.error).toContain("500");
    expect(result.current.comparison?.nPaired).toBe(2);
    expect(result.current.pairs?.t.length).toBe(2);
  });
});
