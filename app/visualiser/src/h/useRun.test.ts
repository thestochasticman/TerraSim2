import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { RunRequest } from "@/t/RunRequest";
import type { RunStatus } from "@/t/RunStatus";

const startRun = vi.fn();
const fetchRunStatus = vi.fn();
const fetchTerrain = vi.fn();
const fetchMoistureDay = vi.fn();

vi.mock("@/api/startRun", () => ({ startRun: (...a: unknown[]) => startRun(...a) }));
vi.mock("@/api/fetchRunStatus", () => ({ fetchRunStatus: (...a: unknown[]) => fetchRunStatus(...a) }));
vi.mock("@/api/fetchTerrain", () => ({ fetchTerrain: (...a: unknown[]) => fetchTerrain(...a) }));
vi.mock("@/api/fetchMoistureDay", () => ({ fetchMoistureDay: (...a: unknown[]) => fetchMoistureDay(...a) }));

const { useRun, POLL_MS } = await import("./useRun");

const request: RunRequest = { stub: "example", stressExponent: 1, initialFullness: 0.5, writeEveryDays: 1, recordFluxes: true };
const base: RunStatus = { runId: "example-abc", status: "running", daysWritten: 0, nDays: 3, rows: 1, cols: 2, dates: ["a", "b", "c"] };
const terrain = { rows: 1, cols: 2, cellSize: 10, elevation: Float64Array.from([1, 2]) };

/** Let pending promises and timers up to `ms` settle inside act. */
const settle = (ms = 0) => act(async () => { await vi.advanceTimersByTimeAsync(ms); });

describe("useRun", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    startRun.mockReset().mockResolvedValue({ runId: "example-abc", status: "running" });
    fetchTerrain.mockReset().mockResolvedValue(terrain);
    fetchMoistureDay.mockReset().mockImplementation(async (_id: string, t: number) => Float32Array.from([t, t + 10]));
    fetchRunStatus.mockReset();
  });
  afterEach(() => vi.useRealTimers());

  it("does nothing for a null request", async () => {
    const { result } = renderHook(() => useRun(null));
    await settle();
    expect(result.current.status).toBeNull();
    expect(startRun).not.toHaveBeenCalled();
  });

  it("starts the run, polls while running, fetches terrain once, follows the newest day, and stops polling when complete", async () => {
    fetchRunStatus
      .mockResolvedValueOnce({ ...base, status: "missing", rows: 0, cols: 0, nDays: 0, dates: [] })
      .mockResolvedValueOnce({ ...base, daysWritten: 1 })
      .mockResolvedValue({ ...base, daysWritten: 3, status: "complete" });

    const { result } = renderHook(() => useRun(request));
    await settle();
    expect(startRun).toHaveBeenCalledWith(request);
    expect(result.current.status?.status).toBe("missing");
    expect(result.current.terrain).toBeNull();
    expect(fetchTerrain).not.toHaveBeenCalled();

    await settle(POLL_MS);
    expect(result.current.status?.daysWritten).toBe(1);
    expect(result.current.latest?.t).toBe(0);
    expect(fetchTerrain).toHaveBeenCalledTimes(1);
    expect(result.current.terrain).toEqual(terrain);

    await settle(POLL_MS);
    expect(result.current.status?.status).toBe("complete");
    expect(result.current.latest?.t).toBe(2);
    expect(Array.from(result.current.latest?.moisture ?? [])).toEqual([2, 12]);

    const calls = fetchRunStatus.mock.calls.length;
    await settle(POLL_MS * 5);
    expect(fetchRunStatus.mock.calls.length).toBe(calls);
    expect(fetchTerrain).toHaveBeenCalledTimes(1);
  });

  it("fetchDay caches: the newest day fetched by polling is not fetched again, other days are fetched once", async () => {
    fetchRunStatus.mockResolvedValue({ ...base, daysWritten: 3, status: "complete" });
    const { result } = renderHook(() => useRun(request));
    await settle();
    expect(result.current.latest?.t).toBe(2);
    const fetchesSoFar = fetchMoistureDay.mock.calls.length;

    let day: Float32Array | undefined;
    await act(async () => { day = await result.current.fetchDay(2); });
    expect(Array.from(day ?? [])).toEqual([2, 12]);
    expect(fetchMoistureDay.mock.calls.length).toBe(fetchesSoFar);

    await act(async () => { await result.current.fetchDay(1); await result.current.fetchDay(1); });
    expect(fetchMoistureDay.mock.calls.length).toBe(fetchesSoFar + 1);
  });

  it("a new request reads as a fresh run and the old run's state does not leak", async () => {
    fetchRunStatus.mockResolvedValue({ ...base, daysWritten: 3, status: "complete" });
    const { result, rerender } = renderHook(({ r }) => useRun(r), { initialProps: { r: request } });
    await settle();
    expect(result.current.latest?.t).toBe(2);

    startRun.mockResolvedValue({ runId: "example-def", status: "running" });
    rerender({ r: { ...request, stressExponent: 2 } });
    expect(result.current.status).toBeNull();
    expect(result.current.latest).toBeNull();
    await settle();
    expect(startRun).toHaveBeenCalledTimes(2);
    expect(fetchRunStatus).toHaveBeenLastCalledWith("example-def");
  });

  it("surfaces a failure to start as an error", async () => {
    startRun.mockRejectedValue(new Error("POST /api/runs failed with status 404"));
    const { result } = renderHook(() => useRun(request));
    await settle();
    expect(result.current.error).toContain("404");
    expect(fetchRunStatus).not.toHaveBeenCalled();
  });
});
