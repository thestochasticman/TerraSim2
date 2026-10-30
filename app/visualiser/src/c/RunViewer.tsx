"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { fetchSites } from "@/api/fetchSites";
import { DayScrubber } from "@/c/DayScrubber";
import { usePlayback } from "@/h/usePlayback";
import { useRun } from "@/h/useRun";
import type { RunRequest } from "@/t/RunRequest";
import styles from "./RunViewer.module.css";

const TerrainScene = dynamic(() => import("@/c/TerrainScene").then((m) => m.TerrainScene), {
  ssr: false,
  loading: () => <p className={styles.message}>Loading viewer…</p>,
});

/**
 * Pick a site, start a run, watch it write, then scrub through it.
 *
 * While the run is going the surface follows the newest written day and
 * the scrubber is a progress bar. When it completes, the scrubber unlocks:
 * play, pause and a day slider, each day fetched once and cached.
 */
export function RunViewer() {
  const [sites, setSites] = useState<string[]>([]);
  const [sitesError, setSitesError] = useState<string | null>(null);
  const [stub, setStub] = useState<string>("");
  const [request, setRequest] = useState<RunRequest | null>(null);
  const { status, terrain, latest, error: runError, fetchDay } = useRun(request);
  const complete = status?.status === "complete";
  const playback = usePlayback(status?.nDays ?? 0, complete);
  const [scrubbed, setScrubbed] = useState<{ t: number; moisture: Float32Array } | null>(null);
  const [scrubError, setScrubError] = useState<string | null>(null);
  const error = runError ?? sitesError ?? scrubError;

  useEffect(() => {
    fetchSites()
      .then((list) => {
        setSites(list);
        setStub((current) => current || list[0] || "");
      })
      .catch((err: unknown) => setSitesError(err instanceof Error ? err.message : String(err)));
  }, []);

  useEffect(() => {
    const t = playback.day;
    if (t === null) return;
    let cancelled = false;
    fetchDay(t)
      .then((moisture) => { if (!cancelled) setScrubbed({ t, moisture }); })
      .catch((err: unknown) => { if (!cancelled) setScrubError(err instanceof Error ? err.message : String(err)); });
    return () => { cancelled = true; };
  }, [playback.day, fetchDay]);

  const start = () => {
    if (!stub) return;
    setRequest({ stub, stressExponent: 1, initialFullness: 0.5, writeEveryDays: 1, recordFluxes: true });
  };

  const shown = playback.day === null ? latest : scrubbed && scrubbed.t === playback.day ? scrubbed : scrubbed ?? latest;
  const progress =
    status === null ? "no run" : status.status === "missing" ? "starting…" : status.status;

  return (
    <div className={styles.viewer}>
      <div className={styles.bar}>
        <label>
          site{" "}
          <select value={stub} onChange={(e) => setStub(e.target.value)} disabled={sites.length === 0}>
            {sites.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={start} disabled={!stub}>
          run
        </button>
        <span role="status">{progress}</span>
        {error && <span role="alert">{error}</span>}
      </div>
      {status && status.daysWritten > 0 && (
        <DayScrubber
          daysAvailable={status.daysWritten}
          nDays={status.nDays}
          day={shown?.t ?? 0}
          date={shown ? status.dates[shown.t] ?? "" : ""}
          enabled={complete}
          playing={playback.playing}
          onSeek={playback.setDay}
          onTogglePlay={playback.togglePlay}
        />
      )}
      <div className={styles.scene}>{terrain && <TerrainScene grid={terrain} moisture={shown?.moisture} />}</div>
    </div>
  );
}
