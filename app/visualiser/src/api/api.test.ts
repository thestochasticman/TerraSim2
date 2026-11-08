import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fetchMoistureDay } from "./fetchMoistureDay";
import { fetchRetentionCurves } from "./fetchRetentionCurves";
import { fetchRunSeries } from "./fetchRunSeries";
import { fetchRunStatus } from "./fetchRunStatus";
import { fetchSites } from "./fetchSites";
import { fetchSoilColumn } from "./fetchSoilColumn";
import { fetchTextureTriangle } from "./fetchTextureTriangle";
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
    const out = await startRun({ stub: "tarrawarra", step: "routed", stressExponent: 1, initialFullness: 0.5, rootDepth: 0.3, writeEveryDays: 1, recordFluxes: true });
    expect(out).toEqual({ runId: "tarrawarra-abc", status: "running" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/runs");
    expect(JSON.parse(String(init?.body))).toEqual({ stub: "tarrawarra", step: "routed", stress_exponent: 1, initial_fullness: 0.5, root_depth: 0.3, write_every_days: 1, record_fluxes: true });
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

  it("fetchRetentionCurves calls /api/soils/retention and parses the records", async () => {
    const record = { texture: "sand", theta: [0.3, 0.1], theta_fc: 0.04, theta_pwp: 0.004, available_water: 36 };
    fetchMock.mockResolvedValueOnce(jsonResponse({ suction: [1, 10], field_capacity: 33, wilting_point: 1500, models: { campbell: [record], van_genuchten: [record] } }));
    const out = await fetchRetentionCurves();
    expect(fetchMock).toHaveBeenLastCalledWith("/api/soils/retention");
    expect(out.models.campbell[0].availableWater).toBe(36);
    fetchMock.mockResolvedValueOnce(jsonResponse({}, 500));
    await expect(fetchRetentionCurves()).rejects.toThrow("status 500");
  });

  it("fetchTextureTriangle calls /api/soils/texture and parses the columns", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ textures: ["sand"], step: 100, points: { sand: [100], silt: [0], clay: [0], texture: [0], diameter: [317], psi_e: [-0.4], b: [1] }, typical: [] }));
    const out = await fetchTextureTriangle();
    expect(fetchMock).toHaveBeenLastCalledWith("/api/soils/texture");
    expect(out.points.psiE).toEqual([-0.4]);
    fetchMock.mockResolvedValueOnce(jsonResponse({}, 503));
    await expect(fetchTextureTriangle()).rejects.toThrow("status 503");
  });

  it("fetchSoilColumn puts the inputs in the query and parses the layers", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ textures: ["sand"], layer_bounds: [0, 1], root_depth: 0.5, model: "campbell", layers: [{ top: 0, bottom: 1, texture: "sand", fraction: 0.035, thickness_in_roots: 0.5, mm: 17.5 }], total: 17.5 }));
    const out = await fetchSoilColumn(["sand"], 0.5, "campbell");
    expect(fetchMock).toHaveBeenLastCalledWith("/api/soils/column?textures=sand&root_depth=0.5&model=campbell");
    expect(out.layers[0].thicknessInRoots).toBe(0.5);
    fetchMock.mockResolvedValueOnce(jsonResponse({}, 422));
    await expect(fetchSoilColumn(["sand"], 0.5, "campbell")).rejects.toThrow("status 422");
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
    await expect(startRun({ stub: "x", step: "bucket", stressExponent: 1, initialFullness: 0, rootDepth: 0.3, writeEveryDays: 1, recordFluxes: false })).rejects.toThrow("500");
  });
});
