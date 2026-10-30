import { useCallback, useEffect, useRef, useState } from "react";
import { fetchMoistureDay } from "@/api/fetchMoistureDay";
import { fetchRunStatus } from "@/api/fetchRunStatus";
import { fetchTerrain } from "@/api/fetchTerrain";
import { startRun } from "@/api/startRun";
import type { RunRequest } from "@/t/RunRequest";
import type { RunStatus } from "@/t/RunStatus";
import type { TerrainGrid } from "@/t/TerrainGrid";

export const POLL_MS = 500;

/**
 * What the hook exposes.
 *
 * status : the latest status from the service, null before the run is started
 * terrain : the run's terrain once the service has it, null before
 * latest : the most recent written day fetched so far, null before any day exists
 * error : a message if any request failed, else null
 * fetchDay : get any written day's moisture, cached after the first fetch
 */
export type RunState = {
  status: RunStatus | null;
  terrain: TerrainGrid | null;
  latest: { t: number; moisture: Float32Array } | null;
  error: string | null;
  fetchDay: (t: number) => Promise<Float32Array>;
};

type Inner = {
  request: RunRequest | null;
  runId: string | null;
  status: RunStatus | null;
  terrain: TerrainGrid | null;
  latest: RunState["latest"];
  error: string | null;
};

const fresh = (request: RunRequest | null): Inner => ({ request, runId: null, status: null, terrain: null, latest: null, error: null });

/**
 * Start a run for a request and follow it.
 *
 * On a new request: POST it, then poll the status every POLL_MS while the
 * run is missing or running. The terrain is fetched once the status reports
 * a shape. Whenever more days are written, the newest one is fetched and
 * exposed as `latest`. Days are cached per run, so scrubbing back is free
 * after the first look. A null request does nothing.
 *
 * State is keyed on the request object: a different request reads as a
 * fresh run until its own first response arrives, so nothing from the old
 * run leaks through.
 */
export function useRun(request: RunRequest | null): RunState {
  const [inner, setInner] = useState<Inner>(() => fresh(request));
  const caches = useRef(new Map<string, Map<number, Float32Array>>());
  const current = inner.request === request ? inner : fresh(request);
  const runId = current.runId;
  const rows = current.status?.rows ?? 0;
  const cols = current.status?.cols ?? 0;

  const update = useCallback((forRequest: RunRequest, patch: Partial<Inner>) => {
    setInner((prev) => (prev.request === forRequest ? { ...prev, ...patch } : prev));
  }, []);

  useEffect(() => {
    if (request === null) return;
    let cancelled = false;
    startRun(request)
      .then(({ runId: id }) => {
        if (!cancelled) setInner({ ...fresh(request), runId: id });
      })
      .catch((err: unknown) => {
        if (!cancelled) setInner({ ...fresh(request), error: messageOf(err) });
      });
    return () => {
      cancelled = true;
    };
  }, [request]);

  useEffect(() => {
    if (request === null || runId === null) return;
    const forRequest = request;
    const cache = cacheFor(caches.current, runId);
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let lastFetchedDay = -1;
    let terrainRequested = false;

    const poll = async () => {
      try {
        const s = await fetchRunStatus(runId);
        if (cancelled) return;
        update(forRequest, { status: s });
        if (s.rows > 0 && s.cols > 0) {
          if (!terrainRequested) {
            terrainRequested = true;
            fetchTerrain(runId)
              .then((g) => { if (!cancelled) update(forRequest, { terrain: g }); })
              .catch((err: unknown) => { if (!cancelled) update(forRequest, { error: messageOf(err) }); });
          }
          const newest = s.daysWritten - 1;
          if (newest > lastFetchedDay) {
            lastFetchedDay = newest;
            const day = cache.get(newest) ?? (await fetchMoistureDay(runId, newest, s.rows, s.cols));
            if (cancelled) return;
            cache.set(newest, day);
            update(forRequest, { latest: { t: newest, moisture: day } });
          }
        }
        if (s.status === "missing" || s.status === "running") {
          timer = setTimeout(poll, POLL_MS);
        }
      } catch (err: unknown) {
        if (!cancelled) update(forRequest, { error: messageOf(err) });
      }
    };
    void poll();
    return () => {
      cancelled = true;
      if (timer !== null) clearTimeout(timer);
    };
  }, [request, runId, update]);

  const fetchDay = useCallback(
    async (t: number): Promise<Float32Array> => {
      if (runId === null || rows === 0 || cols === 0) throw new Error("no run in progress");
      const cache = cacheFor(caches.current, runId);
      const hit = cache.get(t);
      if (hit) return hit;
      const day = await fetchMoistureDay(runId, t, rows, cols);
      cache.set(t, day);
      return day;
    },
    [runId, rows, cols],
  );

  return { status: current.status, terrain: current.terrain, latest: current.latest, error: current.error, fetchDay };
}

function cacheFor(all: Map<string, Map<number, Float32Array>>, runId: string): Map<number, Float32Array> {
  let cache = all.get(runId);
  if (!cache) {
    cache = new Map();
    all.set(runId, cache);
  }
  return cache;
}

function messageOf(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}
