import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fetchMoistureDay } from "./fetchMoistureDay";
import { fetchRunSeries } from "./fetchRunSeries";
import { fetchRunStatus } from "./fetchRunStatus";
import { fetchSites } from "./fetchSites";
import { fetchTerrain } from "./fetchTerrain";
import { startRun } from "./startRun";

const fetchMock = vi.fn<typeof fetch>();

function jsonResponse(body: unknown, status = 200): Response {
  return { ok: status < 400, status, json: async () => body, arrayBuffer: async () => new ArrayBuffer(0) } as unknown as Response;
}

describe("api wrappers", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockReset();
  });
  afterEach(() => vi.unstubAllGlobals());

  it("fetchSites calls /api/sites and validates the list", async () => {
    fetchMock.mockResolvedValue(jsonResponse(["example", "tarrawarra"]));
    expect(await fetchSites()).toEqual(["example", "tarrawarra"]);
    expect(fetchMock).toHaveBeenCalledWith("/api/sites");
    fetchMock.mockResolvedValue(jsonResponse([1]));
    await expect(fetchSites()).rejects.toThrow("array of strings");
  });

  it("startRun posts snake_case fields and returns id and status", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ run_id: "tarrawarra-abc", status: "running" }));
    const out = await startRun({ stub: "tarrawarra", stressExponent: 1, initialFullness: 0.5, writeEveryDays: 1, recordFluxes: true });
    expect(out).toEqual({ runId: "tarrawarra-abc", status: "running" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/runs");
    expect(JSON.parse(String(init?.body))).toEqual({ stub: "tarrawarra", stress_exponent: 1, initial_fullness: 0.5, write_every_days: 1, record_fluxes: true });
  });

  it("fetchRunStatus, fetchTerrain and fetchRunSeries parse their bodies", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ run_id: "x", status: "complete", days_written: 2, n_days: 2, rows: 1, cols: 2, dates: ["a", "b"] }));
    expect((await fetchRunStatus("x")).daysWritten).toBe(2);
    expect(fetchMock).toHaveBeenLastCalledWith("/api/runs/x");

    fetchMock.mockResolvedValueOnce(jsonResponse({ rows: 1, cols: 2, cell_size: 10, elevation: [[1, 2]], capacity: [[100, 100]] }));
    const terrain = await fetchTerrain("x");
    expect(Array.from(terrain.capacity ?? [])).toEqual([100, 100]);

    fetchMock.mockResolvedValueOnce(jsonResponse({ dates: ["a"], rain: [1], pet: [2], moisture: [3] }));
    expect((await fetchRunSeries("x")).moisture).toEqual([3]);
  });

  it("fetchMoistureDay decodes the bytes and surfaces a 409 as an error", async () => {
    const buffer = new ArrayBuffer(8);
    new DataView(buffer).setFloat32(0, 7, true);
    new DataView(buffer).setFloat32(4, 9, true);
    fetchMock.mockResolvedValueOnce({ ok: true, status: 200, arrayBuffer: async () => buffer } as unknown as Response);
    expect(Array.from(await fetchMoistureDay("x", 3, 1, 2))).toEqual([7, 9]);
    expect(fetchMock).toHaveBeenLastCalledWith("/api/runs/x/moisture/3");
    fetchMock.mockResolvedValueOnce(jsonResponse({}, 409));
    await expect(fetchMoistureDay("x", 99, 1, 2)).rejects.toThrow("status 409");
  });

  it("every wrapper rejects on a non-ok response", async () => {
    fetchMock.mockResolvedValue(jsonResponse({}, 500));
    await expect(fetchSites()).rejects.toThrow("500");
    await expect(fetchRunStatus("x")).rejects.toThrow("500");
    await expect(fetchTerrain("x")).rejects.toThrow("500");
    await expect(fetchRunSeries("x")).rejects.toThrow("500");
    await expect(startRun({ stub: "x", stressExponent: 1, initialFullness: 0, writeEveryDays: 1, recordFluxes: false })).rejects.toThrow("500");
  });
});
