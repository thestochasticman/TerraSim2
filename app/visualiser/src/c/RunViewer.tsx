"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import { fetchSites } from "@/api/fetchSites";
import { ComparisonView } from "@/c/ComparisonView";
import { DayScrubber } from "@/c/DayScrubber";
import { SeriesChart } from "@/c/SeriesChart";
import { buildObservationMarkers } from "@/f/buildObservationMarkers";
import { computeComparisonRanges } from "@/f/computeComparisonRanges";
import { computeFiniteRange } from "@/f/computeFiniteRange";
import { VEGETATION_COLOURS } from "@/f/computeVegetationColours";
import { usePlayback } from "@/h/usePlayback";
import { useRun } from "@/h/useRun";
import { useRunComparison } from "@/h/useRunComparison";
import { useRunSeries } from "@/h/useRunSeries";
import type { ColourBy } from "@/t/ColourBy";
import type { MarkerMode } from "@/t/MarkerMode";
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
 * play, pause and a day slider, each day fetched once and cached. The
 * series chart below grows with the run and marks the day on screen.
 *
 * When the site has observations, the day's points sit on the terrain as
 * markers coloured by what was observed or by the run's error there, and
 * the comparison below the chart scores the run against them.
 */
export function RunViewer() {
  const [sites, setSites] = useState<string[]>([]);
  const [sitesError, setSitesError] = useState<string | null>(null);
  const [stub, setStub] = useState<string>("");
  const [rootDepth, setRootDepth] = useState(0.3);
  const [treeRootDepth, setTreeRootDepth] = useState<number | null>(null);
  const [step, setStep] = useState<RunRequest["step"]>("bucket");
  const [leakFraction, setLeakFraction] = useState(0);
  const [rainHours, setRainHours] = useState(24);
  const [lateralMultiplier, setLateralMultiplier] = useState(1);
  const [aspectStrength, setAspectStrength] = useState(0);
  const [request, setRequest] = useState<RunRequest | null>(null);
  const { status, terrain, latest, error: runError, fetchDay } = useRun(request);
  const complete = status?.status === "complete";
  const playback = usePlayback(status?.nDays ?? 0, complete);
  const { series, error: seriesError } = useRunSeries(status?.runId ?? null, status?.daysWritten ?? 0);
  const { comparison, pairs, error: comparisonError } = useRunComparison(status?.runId ?? null, status?.daysWritten ?? 0);
  const [scrubbed, setScrubbed] = useState<{ runId: string; t: number; moisture: Float32Array } | null>(null);
  const [scrubError, setScrubError] = useState<string | null>(null);
  const [colourBy, setColourBy] = useState<ColourBy>("moisture");
  const [markerMode, setMarkerMode] = useState<MarkerMode>("observed");
  const error = runError ?? sitesError ?? seriesError ?? comparisonError ?? scrubError;

  useEffect(() => {
    fetchSites()
      .then((list) => {
        setSites(list);
        setStub((current) => current || list[0] || "");
      })
      .catch((err: unknown) => setSitesError(err instanceof Error ? err.message : String(err)));
  }, []);

  const runId = status?.runId ?? null;

  useEffect(() => {
    const t = playback.day;
    if (t === null || runId === null) return;
    let cancelled = false;
    fetchDay(t)
      .then((moisture) => { if (!cancelled) setScrubbed({ runId, t, moisture }); })
      .catch((err: unknown) => { if (!cancelled) setScrubError(err instanceof Error ? err.message : String(err)); });
    return () => { cancelled = true; };
  }, [playback.day, fetchDay, runId]);

  const start = () => {
    if (!stub) return;
    setRequest({ stub, step, stressExponent: 1, initialFullness: 0.5, rootDepth, treeRootDepth, leakFraction, rainHours, lateralMultiplier, aspectStrength, writeEveryDays: 1, recordFluxes: true });
  };

  // A scrubbed day only counts for the run it was fetched from; anything else falls back to the newest day of the current run.
  const scrubbedHere = scrubbed !== null && scrubbed.runId === runId ? scrubbed : null;
  const shown = playback.day === null ? latest : scrubbedHere && scrubbedHere.t === playback.day ? scrubbedHere : scrubbedHere ?? latest;
  const progress = status === null ? "no run" : status.status === "missing" ? "starting…" : status.status;
  const capacityRange = terrain?.capacity ? computeFiniteRange(terrain.capacity) : null;
  const upslopeRange = terrain?.upslopeCells ? computeFiniteRange(terrain.upslopeCells) : null;
  const relativeRange = useMemo(() => (shown ? computeFiniteRange(shown.moisture) : null), [shown]);
  // A subsurface run holds water up to saturation, so its fullness is over the plant store plus the free store.
  const fullCapacity = useMemo(() => {
    if (!terrain?.capacity || !terrain.freeCapacity || request?.step !== "subsurface") return undefined;
    return terrain.capacity.map((c, i) => c + (terrain.freeCapacity?.[i] ?? 0));
  }, [terrain, request]);
  const ranges = useMemo(() => (pairs ? computeComparisonRanges(pairs) : null), [pairs]);
  const markers = useMemo(() => (terrain && pairs && ranges && shown ? buildObservationMarkers(terrain, pairs, shown.t, markerMode, ranges) : null), [terrain, pairs, ranges, shown, markerMode]);

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
        <label>
          model{" "}
          <select value={step} onChange={(e) => setStep(e.target.value as RunRequest["step"])} aria-label="model">
            <option value="bucket">closed buckets</option>
            <option value="routed">routed buckets, overflow runs downhill</option>
            <option value="subsurface">subsurface, free water drains downslope</option>
          </select>
        </label>
        {step === "subsurface" && (
          <>
            <label>
              leak{" "}
              <input type="number" min={0} max={1} step={0.05} value={leakFraction} onChange={(e) => setLeakFraction(Number(e.target.value))} aria-label="leak fraction" className={styles.depth} />
            </label>
            <label>
              rain hours{" "}
              <input type="number" min={0.5} max={24} step={0.5} value={rainHours} onChange={(e) => setRainHours(Number(e.target.value))} aria-label="rain hours" className={styles.depth} />
            </label>
            <label>
              lateral ×{" "}
              <input type="number" min={1} max={1000} step={1} value={lateralMultiplier} onChange={(e) => setLateralMultiplier(Number(e.target.value))} aria-label="lateral multiplier" className={styles.depth} />
            </label>
            <label title="how much a cell's evaporative demand follows the sun its slope receives; 0 ignores aspect">
              aspect{" "}
              <input type="number" min={0} max={3} step={0.25} value={aspectStrength} onChange={(e) => setAspectStrength(Number(e.target.value))} aria-label="aspect strength" className={styles.depth} />
            </label>
          </>
        )}
        <label>
          root depth, m{" "}
          <input type="number" min={0.05} max={2} step={0.05} value={rootDepth} onChange={(e) => setRootDepth(Number(e.target.value))} aria-label="root depth" className={styles.depth} />
        </label>
        <label title="where the site has a vegetation map, tree cells reach this deep; blank for the same depth everywhere">
          tree roots, m{" "}
          <input type="number" min={0.05} max={3} step={0.05} value={treeRootDepth ?? ""} placeholder="same" onChange={(e) => setTreeRootDepth(e.target.value === "" ? null : Number(e.target.value))} aria-label="tree root depth" className={styles.depth} />
        </label>
        <button type="button" onClick={start} disabled={!stub || !(rootDepth > 0)}>
          run
        </button>
        <span role="status">{progress}</span>
        {error && <span role="alert">{error}</span>}
        <label>
          colour{" "}
          <select value={colourBy} onChange={(e) => setColourBy(e.target.value as ColourBy)} aria-label="colour by">
            <option value="moisture">moisture, fraction of capacity</option>
            <option value="relative">moisture, stretched over the day</option>
            <option value="capacity">capacity, mm</option>
            <option value="upslope">drainage, cells upslope</option>
            {terrain?.vegetation && <option value="vegetation">vegetation, tree or grass</option>}
          </select>
        </label>
        {colourBy === "vegetation" && terrain?.vegetationClasses && (
          <span data-testid="vegetation-legend">
            {terrain.vegetationClasses.map((name, i) => (
              <span key={name}>
                <span className={styles.swatch} style={{ background: VEGETATION_COLOURS[i] }} />
                {name}{" "}
              </span>
            ))}
            <span className={styles.swatch} style={{ background: "#999" }} />
            unknown
          </span>
        )}
        {colourBy === "capacity" && capacityRange && (
          <span data-testid="capacity-legend">
            capacity {capacityRange.min.toFixed(0)} to {capacityRange.max.toFixed(0)} mm, light to dark
          </span>
        )}
        {colourBy === "relative" && relativeRange && (
          <span data-testid="relative-legend">
            {relativeRange.min.toFixed(1)} to {relativeRange.max.toFixed(1)} mm this day, light to dark
          </span>
        )}
        {colourBy === "upslope" && upslopeRange && (
          <span data-testid="upslope-legend">
            {upslopeRange.min.toFixed(0)} to {upslopeRange.max.toFixed(0)} cells drain through, light to dark on a log scale
          </span>
        )}
        {comparison && (
          <label>
            observations{" "}
            <select value={markerMode} onChange={(e) => setMarkerMode(e.target.value as MarkerMode)} aria-label="observations">
              <option value="none">hidden</option>
              <option value="observed">observed content</option>
              <option value="error">model minus observed</option>
            </select>
          </label>
        )}
        {comparison && markerMode === "observed" && ranges?.observed && (
          <span data-testid="observed-legend">
            observed {ranges.observed.min.toFixed(2)} to {ranges.observed.max.toFixed(2)} m³/m³, light to dark
          </span>
        )}
        {comparison && markerMode === "error" && ranges?.errorScale && (
          <span data-testid="error-legend">
            red where the model is drier, blue where wetter, full at {ranges.errorScale.toFixed(2)} m³/m³
          </span>
        )}
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
      <div className={styles.scene}>{terrain && <TerrainScene grid={terrain} moisture={shown?.moisture} colourBy={colourBy} fullCapacity={fullCapacity} markers={markers ?? undefined} />}</div>
      {series && series.dates.length > 0 && <SeriesChart series={series} day={shown?.t ?? null} onSeek={complete ? playback.setDay : undefined} />}
      {comparison && pairs && status && <ComparisonView comparison={comparison} pairs={pairs} day={shown?.t ?? null} dates={status.dates} onSeek={complete ? playback.setDay : undefined} />}
    </div>
  );
}
