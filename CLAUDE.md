# TerraSim2

Process-based soil moisture modelling on terrain, with a React app for visualising the simulation.

## Git

- Work goes on feature branches off `main`, with one pull request each into `main`. There is no `dev` branch.
- `soil-physics-with-python` is a long-lived branch for programming modules of the textbook *Soil Physics with Python* (Bittelli, Campbell, Tomei, 2015). Work for it goes on branches off `soil-physics-with-python`, with one pull request each into it.

## Advice

- Do not assert claims about tooling that you have not verified.

## Model inputs

- The model assumes its inputs are already prepared. `troi_ingest` prepares them from a `Troi`; `terrasim2` consumes them. The handoff is a `ModelInputs` object: a `TerrainGrid`, a `CellToTileMap` on it, and `rain` and `pet` as `TileSeries` on the same tiles and dates, plus free-form `meta` provenance.
- Soil comes from the Soil and Landscape Grid of Australia (SLGA) at 90 m, so it is held like SILO: a second `CellToTileMap` onto SLGA's pixels and, per pixel and depth layer, the prepared plant-available fraction and textural class (`SoilLayers`). A cell's capacity is that fraction summed over the layers the roots reach; `capacity.npy` holds it for the root depth recorded in `meta`, and `load_model_inputs(folder, root_depth)` recomputes it for another.
- On disk, a `ModelInputs` is one folder in a versioned layout (`ModelInputs.FORMAT_VERSION`, now 2): `manifest.json`, `elevation.npy`, `capacity.npy`, `tile_index.npy`, `rain.csv`, `pet.csv`, and when the inputs carry soil layers `soil_tile_index.npy`, `soil_fraction.npy`, `soil_texture.npy` with the layer bounds in the manifest. Only NumPy and the standard library are needed to read it. `write_model_inputs` and `load_model_inputs` in `terrasim2/f/` define the layout; `load_model_inputs` refuses other versions.
- `troi_ingest.ingest_to_disk(troi)` writes to `{troi.out_dir}/model_inputs` and skips the work when a manifest with the same version, stub, bbox and dates is already there.
- `data/dev_sites/{stub}/model_inputs/` holds committed, prepared inputs: `example` (the lab example region, January 2024) and the six validation sites from `data/dense_sites.csv`, produced by `python -m troi_ingest.f.ingest_sites` and copied in. `terrasim2` tests that need real inputs load these; nothing in `terrasim2` ever calls `troi_ingest` or needs a store. Regenerate and re-copy when the format version or the site table changes.

## Run outputs and the service

- A run's histories go to a zarr store when `run_model` is given a folder: `moisture` (T, rows, cols) and `fluxes` (T, n_fluxes, rows, cols), float64, chunked per `RunStoreParams`, written in blocks of `write_every_days`. The store's attributes carry `dates`, `days_written` (leading days safe to read while the run is going) and `complete`. `load_run_result` opens it read-only; `RunResult` never copies the arrays.
- `app/api` is the service the visualiser talks to. A `RunRequest` (site stub plus model and store settings, including the root depth) and the inputs' write time hash to a run id; the same request on the same inputs is the same run, and a complete store is served without rerunning. Runs execute as a separate process (`execute_run`) so the service stays responsive. Readers never go past `days_written`.
- Routes: `GET /sites`, `POST /runs`, `GET /runs/{id}`, `GET /runs/{id}/terrain`, `GET /runs/{id}/moisture/{t}` (float32 bytes), `GET /runs/{id}/series`, `GET /soils/retention` (the book's retention curves per texture), `GET /soils/texture` (the USDA triangle on a grid, classified), `GET /soils/column` (one layered column's available water; query `textures`, `root_depth`, `model`). Start it with `python -m app.api.f.serve [port]` from the repo root in the `borevitz_lab` environment.

## Python structure

- Python 3.12 or later. Use modern syntax directly (`X | None`, `tuple[int, int]`). No `from __future__ import annotations`.
- The Python package is `terrasim2/` at the repo root.
- All classes live in `terrasim2/k/`. All functions live in `terrasim2/f/`.
- One file is exactly one function or one class. The file name is the function name (`terrasim2/f/bucket_step.py` defines `bucket_step`) or the class name in snake case (`terrasim2/k/grid.py` defines `Grid`).
- Write as many small functions as needed. There is no `utils.py` or any file that bundles several functions together.
- A function may take class objects or other functions as inputs.
- Every physical quantity states its unit in the docstring entry for each parameter and attribute. No unit comments in code lines.
- Every function name is a verb, whether it is a free function in `f/` or a method on a class. `_field` is wrong; `_create_field` is right. `cell()` is wrong; `get_cell()` is right. The only exceptions are properties, which are nouns, and the test functions `t`, `t1`, `t2` and so on.

### Current tree

```
TerraSim2/
├── CLAUDE.md
├── tests.py               # terrasim2 runner; --all, <file>, --watch (a: all, q: quit)
├── .tests_cache.json      # written by tests.py; per-file hash of last passing version
├── terrasim2/
│   ├── __init__.py
│   ├── k/
│   │   ├── __init__.py
│   │   ├── terrain_grid.py          # elevation, capacity, moisture arrays on 10 m cells
│   │   ├── cell_to_tile_map.py      # which tile (column of a coarse source) each cell reads; one per source lattice
│   │   ├── tile_series.py           # one variable's daily values, one column per tile; source-agnostic
│   │   ├── bucket_model_params.py   # frozen dataclass of the bucket step's tunables (stress_exponent)
│   │   ├── bucket_flux.py           # IntEnum: INFILTRATION=0, RUNOFF=1, EVAPORATION=2; axis-0 index of the bucket step's flux array
│   │   ├── step_function.py         # Protocol: (moisture, capacity, rain, pet, terrain_derivatives, params) -> (moisture (rows, cols), fluxes (n_fluxes, rows, cols))
│   │   ├── run_result.py            # dates, moisture_history (T, rows, cols), flux_history (T, n_fluxes, rows, cols) or None; arrays may be zarr, never copied
│   │   ├── run_store_params.py      # chunk_days, chunk_rows, chunk_cols, write_every_days, record_fluxes
│   │   ├── model_inputs.py          # grid + cell_map + rain + pet + meta + optional soil, checked for consistency; FORMAT_VERSION
│   │   ├── soil_texture.py          # StrEnum of the 12 USDA textural classes, coarsest first; values as the book's tables spell them
│   │   ├── campbell_params.py       # frozen dataclass of Campbell's retention curve: theta_s, psi_e, b (book eq. 5.27); floats, or arrays for one curve per cell
│   │   ├── van_genuchten_params.py  # frozen dataclass of van Genuchten's curve: theta_s, theta_r, alpha, n; m = 1 - 1/n (book eq. 5.29)
│   │   ├── soil_layers.py           # a layered soil per tile of a coarse soil source: CellToTileMap, layer bounds, available fraction and texture per layer; compute_capacity(root depth) -> mm per cell
│   │   └── terrain_derivatives.py   # what follows from a terrain's shape, each a cached property computed on first use: filled, downstream (-1 at outlets), slope, order, upslope_cells
│   └── f/
│       ├── __init__.py
│       ├── get_values_on_cells.py   # (map, series, day) -> (rows, cols) field; tiles as flat patches
│       ├── step_bucket_model.py     # one day of closed per-cell buckets: infiltrate, overflow, evaporate; no lateral flow
│       ├── run_model.py             # (step, ModelInputs, params, folder=None, store_params) -> RunResult; one TerrainDerivatives per run; in memory, or blocks into a zarr store
│       ├── create_run_store.py      # empty zarr group: moisture (T, rows, cols), fluxes (T, n, rows, cols), attrs dates/complete/meta
│       ├── write_run_block.py       # write n consecutive days into the store
│       ├── load_run_result.py       # open a store read-only as a RunResult; refuses incomplete runs unless asked
│       ├── write_model_inputs.py    # ModelInputs -> folder (manifest.json, .npy arrays, .csv series, soil_*.npy when soil is present)
│       ├── load_model_inputs.py     # (folder, root_depth=None) -> ModelInputs; refuses other FORMAT_VERSIONs; a root depth recomputes capacity from the soil layers
│       ├── lookup_campbell_params.py          # SoilTexture -> CampbellParams from the book's table 5.3
│       ├── compute_campbell_water_content.py  # (psi J/kg, CampbellParams) -> theta m3/m3; saturated at and above air entry
│       ├── lookup_van_genuchten_params.py     # SoilTexture -> VanGenuchtenParams from the book's table 5.4
│       ├── compute_van_genuchten_water_content.py  # (psi J/kg, VanGenuchtenParams) -> theta m3/m3; saturated at and above zero
│       ├── compute_available_water.py         # (curve, params, root depth m) -> mm: the available fraction times the depth
│       ├── compute_available_fraction.py      # (curve, params) -> theta at field capacity -33 minus theta at wilting point -1500 J/kg, m3/m3; arrays per cell
│       ├── compute_layer_thickness_in_depth.py # (layer bounds m, depth m or field) -> how much of each layer lies above the depth, (L,) or (L, rows, cols)
│       ├── compute_capacity_map.py            # (available fraction (L, rows, cols), layer bounds, root depth) -> mm per cell; the layered sum behind TerrainGrid.capacity
│       ├── classify_soil_texture.py           # (sand, silt, clay fractions) -> index into list(SoilTexture) by the USDA triangle rules; partitions the triangle
│       ├── compute_geometric_mean_diameter.py # (sand, silt, clay fractions) -> d_g in micrometres, book eq. 2.36
│       ├── estimate_campbell_params.py        # (d_g, theta_s) -> CampbellParams by the book's regressions, eqs. 5.36 and 5.37; array-valued per cell
│       ├── lookup_typical_fractions.py        # SoilTexture -> typical (sand, silt, clay) fractions from the book's table 2.4
│       ├── prepare_soil_layer.py              # (sand, silt, clay, bulk density kg/m3) -> (available fraction, texture index) by the book's continuous route; NaN-safe
│       ├── fill_pits.py                       # elevation -> elevation with depressions raised to their spill level plus a faint slope (priority flood)
│       ├── compute_flow_direction.py          # (elevation, cell size) -> (downstream flat index or -1, slope) by steepest descent to one of eight neighbours
│       ├── compute_flow_order.py              # (elevation, downstream) -> flat indices upstream before downstream; refuses non-descending directions
│       └── compute_upslope_cells.py           # (downstream, order) -> cells draining through each cell, itself included
├── data/
│   ├── dense_sites.csv    # one row per validation site: stub, bbox (WSEN), start, end; source of truth for site Trois
│   ├── dense_sites.md     # the same table with caveats and provenance
│   └── dev_sites/         # committed prepared inputs, ~13 MB in all
│       ├── example/model_inputs/        # lab example region, January 2024
│       ├── esdale/model_inputs/         # one folder per site in data/dense_sites.csv ...
│       ├── llara/model_inputs/
│       ├── mri/model_inputs/
│       ├── sasmas_stanley/model_inputs/
│       ├── tarrawarra/model_inputs/
│       └── nerrigundah/model_inputs/
├── troi_ingest/           # Troi -> TerrainGrid on the Sentinel-2 grid; own k/, f/, tests.py; imports terrasim2 and the lab packages
│   ├── __init__.py
│   ├── tests.py           # own runner; PASS / SKIP / FAIL; --watch reruns a file on save (a: all, q: quit); cache in troi_ingest/.tests_cache.json
│   ├── k/__init__.py
│   └── f/
│       ├── compute_window.py    # bbox -> (row0, row1, col0, col1) on the 10 m EPSG:6933 lattice, fitted to the bbox
│       ├── load_elevation.py    # Troi -> elevation array on that window, from the Copernicus DEM store at troi.config
│       ├── compute_silo_tiles.py # bbox -> (tile_index, SILO points): cell centres snapped to SILO's 0.05 degree lattice
│       ├── compute_slga_tiles.py # (bbox, lat axis, lon axis) -> (tile_index, pixels): cell centres matched to the nearest SLGA 90 m pixel
│       ├── load_silo_series.py  # (Troi, grid, variable, name, units) -> (CellToTileMap, TileSeries) from the SILO store at troi.config
│       ├── load_rain.py         # load_silo_series with daily_rain, named "rain", mm
│       ├── load_pet.py          # load_silo_series with et_short_crop, named "pet", mm
│       ├── load_soil_layers.py  # (Troi, grid) -> SoilLayers from the SLGA store: clay, sand, silt, bulk density at six depths through prepare_soil_layer
│       ├── make_test_troi.py    # Troi for the example region with a throwaway registry; used by tests only
│       ├── ingest.py            # Troi -> ModelInputs in memory with soil layers; capacity at ROOT_DEPTH (0.3 m); provenance in meta
│       ├── ingest_to_disk.py    # Troi -> folder via write_model_inputs; skips when the manifest is current
│       ├── read_dense_sites.py  # data/dense_sites.csv -> list of site dicts (stub, bbox, start, end)
│       ├── make_site_troi.py    # stub -> Troi from the site table, under a given Config
│       └── ingest_sites.py      # stubs -> {stub: folder}; `python -m troi_ingest.f.ingest_sites [stubs]` runs every site
└── app/                   # the visualiser and the service it talks to
    ├── api/               # Python service: own k/, f/, tests.py (PASS/SKIP/FAIL, --watch); imports terrasim2
    │   ├── k/run_request.py        # pydantic RunRequest: stub, stress_exponent, initial_fullness, root_depth, write_every_days, chunk_days, record_fluxes
    │   └── f/
    │       ├── compute_run_id.py   # (RunRequest, inputs key) -> "{stub}-{12 hex}"; same request on the same inputs, same id
    │       ├── read_inputs_key.py  # model_inputs folder -> "v{version}@{written_at}", so a store from older inputs is never served
    │       ├── find_inputs.py      # stub -> model_inputs folder, searching roots in order (data/dev_sites by default)
    │       ├── execute_run.py      # the worker: inputs + request -> run_model into a store, capacity from the soil at the request's root depth; also `python -m app.api.f.execute_run`
    │       ├── launch_run.py       # start execute_run as a subprocess; writes request.json and worker.log beside the store
    │       ├── read_run_status.py  # store -> missing | running | complete, days_written, shape, dates
    │       ├── read_moisture_day.py # store, t -> float32 bytes; refuses days not yet written
    │       ├── read_terrain.py     # (model_inputs, root_depth) -> elevation, capacity at that root depth and upslope cell counts (via TerrainDerivatives) in the visualiser's JSON shape
    │       ├── read_series.py      # grid-mean daily rain, pet, moisture and fluxes for the days written
    │       ├── compute_retention_curves.py # both book curves for the 12 textures over a log suction grid, with theta at FC and WP and mm per m
    │       ├── compute_texture_triangle.py # the triangle on a 1 percent grid: class, d_g, estimated psi_e and b per point, plus table 2.4's typical soils
    │       ├── compute_soil_column.py      # (6 textures, root depth, model) -> per-layer fraction, thickness in roots and mm on SLGA's depth intervals, plus the total
    │       ├── create_app.py       # FastAPI routes over the above; takes runs_root and inputs_roots
    │       └── serve.py            # `python -m app.api.f.serve [port]`: runs under {troi out_dir}/terrasim2_runs
    └── visualiser/        # Next.js + TypeScript; see App structure
        ├── package.json   # scripts: dev, dev:all (service + next together), build, lint, test, test:changed
        ├── next.config.ts # rewrites /api/* to the service (TERRASIM2_API_URL, default http://127.0.0.1:8000)
        ├── scripts/dev.mjs # starts `python -m app.api.f.serve` and `next dev`; stops both together
        ├── vitest.config.mts
        ├── public/terrain/sample.json         # synthetic 40x40 hill; replaced by Python output later
        └── src/
            ├── api/                           # the only place fetch is called; one wrapper per route, tests in api.test.ts
            │   ├── fetchSites.ts, startRun.ts, fetchRunStatus.ts, fetchTerrain.ts, fetchMoistureDay.ts, fetchRunSeries.ts, fetchRetentionCurves.ts, fetchTextureTriangle.ts, fetchSoilColumn.ts
            ├── app/
            │   ├── layout.tsx                 # root html, fonts, metadata
            │   ├── page.tsx                   # renders <TerrainViewer url="/terrain/sample.json" />
            │   ├── runs/page.tsx              # renders <RunViewer />
            │   ├── soils/page.tsx             # renders <RetentionViewer />, <TextureTriangleViewer />, <SoilColumnViewer />
            │   └── globals.css
            ├── c/                             # every .tsx has a .test.tsx beside it
            │   ├── TerrainViewer.tsx          # fetches via useTerrainGrid, shows status/error, loads scene client-only
            │   ├── TerrainViewer.module.css
            │   ├── TerrainScene.tsx           # Canvas, camera frame, lights, OrbitControls, TerrainSurface; optional moisture and colourBy
            │   ├── TerrainSurface.tsx         # the mesh; must sit inside a Canvas; vertex colours always on: moisture when given, capacity or drainage with colourBy="capacity" or "upslope", else an earth tone (switching the material mode after it has drawn leaves it white)
            │   ├── RunViewer.tsx              # site picker, root depth field, run button, status, colour-by select (moisture, capacity, drainage) with a legend; follows the newest day while running, scrubs when complete
            │   ├── RunViewer.module.css
            │   ├── DayScrubber.tsx            # play/pause, day slider, date; a locked progress bar until the run completes
            │   ├── DayScrubber.module.css
            │   ├── SeriesChart.tsx            # two visx panels: stored mm as a line; fluxes mm/day as bars from zero (rain up, evaporation + runoff stacked down, demand outlined); marker, hover legend, click to seek, drag to zoom, double click to reset
            │   ├── SeriesChart.module.css
            │   ├── SeriesPanel.tsx            # one panel: y axis (|values|), grid rows, bar groups up/down from zero with optional outline, lines, marker; parent owns the SVG
            │   ├── RetentionViewer.tsx        # fetches the book's curves via useRetentionCurves, caption, status/error, then RetentionChart
            │   ├── RetentionViewer.module.css
            │   ├── RetentionChart.tsx         # one line per texture over a log suction axis with FC and WP marked; bars of mm per m per model; radio picks the model; hover highlights a texture in lines, bars and table
            │   ├── RetentionChart.module.css
            │   ├── TextureTriangleViewer.tsx  # fetches the classified triangle via useTextureTriangle, caption, status/error, then TextureTriangle
            │   ├── TextureTriangleViewer.module.css
            │   ├── TextureTriangle.tsx        # the USDA triangle as a dot per grid composition coloured by class, class names at centroids, table 2.4 soils ringed; pointer reads the nearest composition; hovering a class dims the rest
            │   ├── TextureTriangle.module.css
            │   ├── SoilColumnViewer.tsx       # a texture picker per SLGA layer, a root depth slider and a model radio; fetches via useSoilColumn, then SoilColumnChart
            │   ├── SoilColumnViewer.module.css
            │   ├── SoilColumnChart.tsx        # depth down the page, a bar per layer as wide as its available fraction, solid within the roots and faded below; total mm as the headline, a table of layers
            │   └── SoilColumnChart.module.css
            ├── f/                             # every .ts has a .test.ts beside it
            │   ├── buildTerrainMesh.ts        # TerrainGrid -> vertex positions and triangle indices
            │   ├── createTerrainGeometry.ts   # TerrainGrid -> Three.js BufferGeometry with normals
            │   ├── frameTerrainCamera.ts      # TerrainGrid -> camera target, position, near, far
            │   ├── parseTerrainGrid.ts        # JSON -> TerrainGrid (elevation, optional capacity and upslope_cells)
            │   ├── parseRunStatus.ts          # service status JSON -> RunStatus
            │   ├── parseRunSeries.ts          # service series JSON -> RunSeries
            │   ├── decodeMoistureDay.ts       # float32 bytes -> Float32Array for one day
            │   ├── mapMoistureToColour.ts     # fullness 0..1 -> sequential blue, light (dry) to dark (wet); NaN -> grey
            │   ├── computeVertexColours.ts    # moisture + capacity -> RGB per vertex
            │   ├── computeChartExtent.ts      # RunSeries -> y-axis tops for the moisture and flux panels
            │   ├── computeCapacityColours.ts  # capacity per cell -> RGB per vertex on the ramp, scaled by the largest finite capacity; NaN -> grey
            │   ├── computeUpslopeColours.ts   # upslope cell counts -> RGB per vertex on the ramp over log(count); ridges light, channels dark
            │   ├── computeFiniteRange.ts      # {min, max} of the finite values, or null
            │   ├── createUniformColours.ts    # one RGB repeated per vertex, the colour attribute's layout
            │   ├── pickDay.ts                 # x pixel within a plot -> nearest day index, within an optional visible range
            │   ├── clampDayRange.ts           # requested span -> valid visible range inside the run, at least a week wide
            │   ├── parseRetentionCurves.ts    # service retention JSON -> RetentionCurves; both models must list the same textures in order
            │   ├── mapTextureToColour.ts      # (index, count, scheme) -> css rgb on the blue ramp; sand to clay runs light to dark on a light surface, mid to lightest on a dark one
            │   ├── parseTextureTriangle.ts    # service texture JSON -> TextureTriangle; columns must line up and classes must index the texture list
            │   ├── projectTernary.ts          # (sand, silt, clay) -> {x, y} in a unit triangle: sand at (0, 0), silt at (1, 0), clay at the apex
            │   ├── invertTernary.ts           # {x, y} -> fractions; negative outside the triangle
            │   ├── parseSoilColumn.ts         # service column JSON -> SoilColumn; one layer per bound interval
            │   └── readPositiveInteger.ts
            ├── h/
            │   ├── useTerrainGrid.ts          # fetch + parse a terrain JSON by url
            │   ├── useRun.ts                  # start a run, poll while it writes, cache days, expose the newest day
            │   ├── usePlayback.ts             # the scrubber's day (null = follow newest) and play timer
            │   ├── useRunSeries.ts            # the run's grid-mean series, refetched as days are written
            │   ├── useRetentionCurves.ts      # fetch the book's curves once on mount
            │   ├── useColourScheme.ts         # "light" | "dark" from prefers-color-scheme, following changes; light on the server
            │   ├── useTextureTriangle.ts      # fetch the classified triangle once on mount
            │   └── useSoilColumn.ts           # refetch a column as its textures, root depth or model change; keeps the last column on a failure
            └── t/
                ├── TerrainGrid.ts             # rows, cols, cellSize, elevation, capacity?, upslopeCells?
                ├── TerrainMesh.ts
                ├── RunRequest.ts              # mirrors app/api RunRequest, camelCase, with rootDepth
                ├── RunStatus.ts
                ├── RunSeries.ts
                ├── CurveModel.ts              # "campbell" | "van_genuchten", and CURVE_MODELS in that order
                ├── TextureCurve.ts            # texture, theta per suction, thetaFc, thetaPwp, availableWater mm per m
                ├── RetentionCurves.ts         # suction, fieldCapacity, wiltingPoint, models: per-model TextureCurve lists
                ├── ColourScheme.ts            # "light" | "dark"
                ├── ColourBy.ts                # "moisture" | "capacity" | "upslope": what the terrain surface's colour encodes
                ├── TextureTriangle.ts         # textures, step, point columns (sand, silt, clay %, texture index, diameter, psiE, b), typical soils
                └── SoilColumn.ts              # textures, layerBounds, rootDepth, model, layers (top, bottom, texture, fraction, thicknessInRoots, mm), total
```

### Tests

- Every function file and every class file defines a `t()` function that tests the unit in that file.
- `t()` may be split into `t1()`, `t2()`, `t3()` and so on for tooling. `t()` calls them in order. Each raises `AssertionError` on failure. `t()` returns nothing on success.
- `tests.py` at the repo root is the test runner. It finds files in `terrasim2/k/` and `terrasim2/f/` that were edited since they last passed, imports each one, and calls its `t()`. It reports pass or fail per file.
- `tests.py` tracks edits with a cache of per-file content hashes. A file's hash is recorded only when its `t()` passes. `tests.py --all` runs every file regardless. `tests.py <file>` runs just that file.
- `tests.py --watch` keeps running: it reruns a file's `t()` in a fresh subprocess whenever that file is saved, `a` runs every file, `q` quits.

## App structure

- `app/` holds two programs: `app/visualiser/`, the Next.js + TypeScript viewer, and `app/api/`, the Python service it talks to. The terrain renders as a 3D mesh with orbit controls via Three.js.
- `app/visualiser/src/c/` holds components, one per file, file named after the component.
- `app/visualiser/src/f/` holds pure functions, one per file, same rules as the Python `f/`. No React, no browser APIs.
- `app/visualiser/src/h/` holds hooks, one per file, each named `useSomething`.
- `app/visualiser/src/t/` holds types shared by more than one file, one type per file, file named after the type. A type used by a single file stays in that file.
- `app/visualiser/src/app/` is the Next.js routing folder. Pages compose components and hold no logic.
- Function names are verbs here too. Components and hooks are the exceptions: a component is a noun, a hook is `use` plus a noun.
- Charts are built with visx: scales, axes and marks as React components in SVG, so every chart is ordinary components styled with the app's CSS and tested like any other component. Scale and data-shaping logic lives in `f/` as pure functions. No canvas charting library.
- The visualiser talks only to `app/api`, through `/api/*` on its own origin, which Next.js rewrites to the service's port. `src/api/` is the only place `fetch` is called.

### Tests

- Every file in `c/`, `f/` and `h/` has a test file beside it with the same name and a `.test.ts` or `.test.tsx` suffix. This is the app's equivalent of `t()`; tests stay out of the source file so they stay out of the browser bundle.
- Pure functions are tested against hand-computed outputs. Components are rendered in a test DOM and asserted on. The 3D scene is asserted on its scene graph, not on pixels.
- Vitest is the runner. `vitest --changed` runs only tests for files edited since the last commit, the counterpart of `tests.py`.
