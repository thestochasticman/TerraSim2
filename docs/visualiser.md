# Visualiser

<!-- nav -->
← [Service](service.md) · [Index](README.md) · [Development](development.md) →
<!-- /nav -->

`app/visualiser` is a Next.js and TypeScript viewer. It calls only the service, through `/api/*` on its own origin. `next.config.ts` rewrites these calls to `TERRASIM2_API_URL` (default `http://127.0.0.1:8000`). `src/api/` is the only place `fetch` is called, with one wrapper per route.

## Commands

Run these in `app/visualiser`:

```
npm run dev          # viewer only; needs the service running
npm run dev:all      # scripts/dev.mjs: starts the service and the viewer, stops both together
npm run test         # vitest
npm run test:changed # tests for files changed since the last commit
npm run lint
```

## Pages

| Path | Content |
|---|---|
| `/` | `TerrainViewer` on `public/terrain/sample.json`, a synthetic 40 × 40 hill, not model output |
| `/runs` | `RunViewer` |
| `/soils` | `RetentionViewer`, `TextureTriangleViewer`, `SoilColumnViewer` |

## Run page

A control bar, which wraps onto further lines as needed, sets the site, step and request fields ([service.md](service.md)), and the run button posts the request. The scene takes 64 % of the viewport height and the page scrolls to the chart and comparison. The camera looks at a point 0.15 of the grid's longer side below the mid elevation, so the terrain sits in the upper part of the canvas. While the run writes, the view follows the newest day written. When the run is complete, the day scrubber can play or seek.

- **Terrain** (`TerrainScene`, `TerrainSurface`): a Three.js mesh with orbit controls. Vertex colour shows one of:
  - moisture as a fraction of capacity (of capacity plus free capacity for the subsurface step);
  - moisture stretched over the shown day's own range;
  - capacity;
  - log of upslope cells;
  - vegetation class;
  - a plain earth tone (no data), for use with the bucket columns.
- **Observation markers** (`ObservationMarkers`): spheres at the shown day's observation cells, hidden, coloured by observed content, by modelled minus observed, or drawn in one red.
- **Bucket columns** (`BucketColumns`, `buildBucketColumns`, `selectBucketStore`): with the buckets select set to each cell, 5 × 5 or 10 × 10 cells, one column hangs under the surface per block, and the surface is drawn at 30 % opacity. Column height is proportional to the block's mean capacity (plus mean free capacity for the subsurface step), scaled so the largest column is 0.12 of the grid's longer side. Within a column, the plant store fills from the bottom and the free store above it, from the block's mean moisture on the shown day. For a subsurface run, a store select shows both stores, the plant store alone or the free store alone, on the same scale. The two fills are ranges of water content in one root zone, drawn one above the other; they are not depths in the soil.
- **Series chart** (`SeriesChart`): grid-mean stored water as a line, and the day's fluxes as bars above and below zero, with the legend beside the chart. It supports hover, click to seek, drag to zoom and double-click to reset. Mouse positions are mapped through the SVG's rendered scale and offset (`computeSvgScale`).
- **Comparison** (`ComparisonView`), for sites with observations: whole-run scores, a table per date that seeks on click, and a scatter of modelled against observed with the shown day highlighted.

Scores on this page come from the service's comparison route and differ from [evaluation.md](evaluation.md) for the reasons given in [service.md](service.md).

## Soils page

- `RetentionChart`: Campbell or van Genuchten retention curves for the twelve textures, with field capacity and wilting point at −33/−1500 J/kg, and available water per metre.
- `TextureTriangle`: the USDA triangle on a 1 % grid, with the composition under the pointer.
- `SoilColumnChart`: six SLGA layers chosen by texture, a root depth, and the available water within it, at the model's −10/−500 J/kg.

## Code structure

| Folder | Content | Test rule |
|---|---|---|
| `src/c/` | Components, one per file | `.test.tsx` beside each; the 3D scene is tested on its scene graph, not pixels |
| `src/f/` | Pure functions, one per file, no React or browser APIs | `.test.ts` beside each, against hand-computed values |
| `src/h/` | Hooks, one per file | `.test.ts` beside each |
| `src/t/` | Types shared by more than one file | none |
| `src/api/` | Fetch wrappers | one test file for all |
| `src/app/` | Next.js routes; no logic | none |

Charts are drawn with visx as SVG React components.
