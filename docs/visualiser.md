# Visualiser

<!-- nav -->
← [Service](service.md) · [Index](README.md) · [Development](development.md) →
<!-- /nav -->

`app/visualiser` is a Next.js + TypeScript viewer. It talks only to the service, through `/api/*` on its own origin, which `next.config.ts` rewrites to the service's port (`TERRASIM2_API_URL`, default `http://127.0.0.1:8000`). `src/api/` is the only place `fetch` is called, one wrapper per route.

## Run

```
npm run dev        # the viewer alone, against a service already running
npm run dev:all    # scripts/dev.mjs starts python -m app.api.f.serve and next dev together, and stops both together
npm run test       # vitest
npm run test:changed
npm run lint
```

## Pages

| Page | Renders |
|---|---|
| `/` | `TerrainViewer` on `public/terrain/sample.json`, a synthetic hill |
| `/runs` | `RunViewer`: the run page |
| `/soils` | `RetentionViewer`, `TextureTriangleViewer`, `SoilColumnViewer`: the soil-physics reference pages |

Pages compose components and hold no logic.

## The run page

The bar sets the site, the process step and every parameter of the run request ([service.md](service.md)); `run` posts it. `useRun` starts the run, polls while it writes, caches days and exposes the newest; `usePlayback` owns the scrubber's day (null means follow the newest) and the play timer; `useRunSeries` and `useRunComparison` refetch as days are written.

- **Terrain** (`TerrainScene`, `TerrainSurface`): a Three.js mesh with orbit controls, coloured per vertex by the selected `ColourBy`: moisture as a fraction of capacity (sequential blue, light dry to dark wet, fixed over the run), the same day stretched over its own range (`relative`), capacity (mm), drainage (log of cells upslope: ridges light, channels dark) or vegetation class (grass yellow, tree green, unknown grey).
- **Observation markers** (`ObservationMarkers`, one instanced mesh of spheres above the surface): hidden, coloured by the measured content on a scale fixed over the run, or by modelled minus observed on a diverging scale (red dry, grey zero, blue wet).
- **Day scrubber**: play/pause, slider, date; a locked progress bar until the run completes.
- **Series chart** (`SeriesChart`, two `SeriesPanel`s, visx): stored mm as a line; the fluxes as bars from zero, rain with inflow stacked up, evaporation, runoff, subsurface lateral flow and percolation stacked down, demand and surface flow outlined; marker, hover legend, click to seek, drag to zoom, double click to reset.
- **Comparison** (`ComparisonView`, for a site with observations): what was paired and how the run is read, the whole-run scores, a table with the whole run and a row per survey date (`ComparisonTable`; the shown day highlighted, click to seek) beside modelled against observed with the shown day in full (`ScatterChart`, thinned past a maximum).

## The soils page

`RetentionChart`: one line per texture over a log suction axis with field capacity and wilting point marked, bars of mm per metre per model, a radio for Campbell or van Genuchten, hover highlighting across lines, bars and table. `TextureTriangle`: a dot per grid composition coloured by class, class names at centroids, table 2.4's soils ringed, the pointer reading the nearest composition. `SoilColumnChart`: depth down the page, a bar per SLGA layer as wide as its available fraction, solid within the roots and faded below, the total mm as the headline. The retention and triangle pages carry the textbook's conventions; the column page uses the model's ([soil.md](soil.md)).

## Structure

| Folder | Holds | Rule |
|---|---|---|
| `src/c/` | Components, one per file, named after the component | every `.tsx` has a `.test.tsx` beside it; the 3D scene is asserted on its scene graph, not pixels |
| `src/f/` | Pure functions, one per file, verbs | no React, no browser APIs; tested against hand-computed outputs |
| `src/h/` | Hooks, `useSomething` | one per file, tested in a test DOM |
| `src/t/` | Types shared by more than one file, one per file | a type used by one file stays in that file |
| `src/api/` | The fetch wrappers | the only `fetch` calls |
| `src/app/` | Next.js routing | no logic |

Charts are visx: scales, axes and marks as React components in SVG, so every chart is ordinary components styled with the app's CSS and tested like any other component; scale and data-shaping logic lives in `src/f/`. No canvas charting library.

<!-- nav -->
← [Service](service.md) · [Index](README.md) · [Development](development.md) →
<!-- /nav -->
