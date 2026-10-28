# TerraSim2

Process-based soil moisture modelling on terrain, with a React app for visualising the simulation.

## Git

- Work goes on feature branches off `main`, with one pull request each into `main`. There is no `dev` branch.

## Advice

- Do not assert claims about tooling that you have not verified.

## Model inputs

- The model assumes its inputs are already prepared. `troi_ingest` prepares them from a `Troi`; `terrasim2` consumes them. The handoff is a `ModelInputs` object: a `TerrainGrid`, a `CellToTileMap` on it, and `rain` and `pet` as `TileSeries` on the same tiles and dates, plus free-form `meta` provenance.
- On disk, a `ModelInputs` is one folder in a versioned layout (`ModelInputs.FORMAT_VERSION`): `manifest.json`, `elevation.npy`, `capacity.npy`, `tile_index.npy`, `rain.csv`, `pet.csv`. Only NumPy and the standard library are needed to read it. `write_model_inputs` and `load_model_inputs` in `terrasim2/f/` define the layout; `load_model_inputs` refuses other versions.
- `troi_ingest.ingest_to_disk(troi)` writes to `{troi.out_dir}/model_inputs` and skips the work when a manifest with the same version, stub, bbox and dates is already there.
- `dev_data/{stub}/model_inputs/` holds committed, prepared inputs: `example` (the lab example region, January 2024) and the six validation sites from `data/dense_sites.csv`, produced by `python -m troi_ingest.f.ingest_sites` and copied in. `terrasim2` tests that need real inputs load these; nothing in `terrasim2` ever calls `troi_ingest` or needs a store. Regenerate and re-copy when the format version or the site table changes.

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
│   │   ├── step_function.py         # Protocol: (moisture, capacity, rain, pet, params) -> (moisture (rows, cols), fluxes (n_fluxes, rows, cols))
│   │   ├── run_result.py            # dates, moisture_history (T, rows, cols), flux_history (T, n_fluxes, rows, cols)
│   │   └── model_inputs.py          # grid + cell_map + rain + pet + meta, checked for consistency; FORMAT_VERSION
│   └── f/
│       ├── __init__.py
│       ├── get_values_on_cells.py   # (map, series, day) -> (rows, cols) field; tiles as flat patches
│       ├── step_bucket_model.py     # one day of closed per-cell buckets: infiltrate, overflow, evaporate; no lateral flow
│       ├── run_model.py             # (step, ModelInputs, params) -> RunResult; loop over days calling any StepFunction
│       ├── write_model_inputs.py    # ModelInputs -> folder (manifest.json, .npy arrays, .csv series)
│       └── load_model_inputs.py     # folder -> ModelInputs; refuses other FORMAT_VERSIONs
├── dev_data/                        # committed prepared inputs, ~13 MB in all
│   ├── example/model_inputs/        # lab example region, January 2024
│   ├── esdale/model_inputs/         # one folder per site in data/dense_sites.csv ...
│   ├── llara/model_inputs/
│   ├── mri/model_inputs/
│   ├── sasmas_stanley/model_inputs/
│   ├── tarrawarra/model_inputs/
│   └── nerrigundah/model_inputs/
├── data/
│   ├── dense_sites.csv    # one row per validation site: stub, bbox (WSEN), start, end; source of truth for site Trois
│   └── dense_sites.md     # the same table with caveats and provenance
├── troi_ingest/           # Troi -> TerrainGrid on the Sentinel-2 grid; own k/, f/, tests.py; imports terrasim2 and the lab packages
│   ├── __init__.py
│   ├── tests.py           # own runner; PASS / SKIP / FAIL; --watch reruns a file on save (a: all, q: quit); cache in troi_ingest/.tests_cache.json
│   ├── k/__init__.py
│   └── f/
│       ├── compute_window.py    # bbox -> (row0, row1, col0, col1) on the 10 m EPSG:6933 lattice, fitted to the bbox
│       ├── load_elevation.py    # Troi -> elevation array on that window, from the Copernicus DEM store at troi.config
│       ├── compute_silo_tiles.py # bbox -> (tile_index, SILO points): cell centres snapped to SILO's 0.05 degree lattice
│       ├── load_silo_series.py  # (Troi, grid, variable, name, units) -> (CellToTileMap, TileSeries) from the SILO store at troi.config
│       ├── load_rain.py         # load_silo_series with daily_rain, named "rain", mm
│       ├── load_pet.py          # load_silo_series with et_short_crop, named "pet", mm
│       ├── make_test_troi.py    # Troi for the example region with a throwaway registry; used by tests only
│       ├── ingest.py            # Troi -> ModelInputs in memory, with provenance in meta
│       ├── ingest_to_disk.py    # Troi -> folder via write_model_inputs; skips when the manifest is current
│       ├── read_dense_sites.py  # data/dense_sites.csv -> list of site dicts (stub, bbox, start, end)
│       ├── make_site_troi.py    # stub -> Troi from the site table, under a given Config
│       └── ingest_sites.py      # stubs -> {stub: folder}; `python -m troi_ingest.f.ingest_sites [stubs]` runs every site
└── app/                   # Next.js + TypeScript; see App structure
    ├── package.json       # scripts: dev, build, lint, test, test:changed
    ├── vitest.config.mts
    ├── public/terrain/sample.json         # synthetic 40x40 hill; replaced by Python output later
    └── src/
        ├── app/
        │   ├── layout.tsx                 # root html, fonts, metadata
        │   ├── page.tsx                   # renders <TerrainViewer url="/terrain/sample.json" />
        │   └── globals.css
        ├── c/                             # every .tsx has a .test.tsx beside it
        │   ├── TerrainViewer.tsx          # fetches via useTerrainGrid, shows status/error, loads scene client-only
        │   ├── TerrainViewer.module.css
        │   ├── TerrainScene.tsx           # Canvas, camera frame, lights, OrbitControls, TerrainSurface
        │   └── TerrainSurface.tsx         # the mesh; must sit inside a Canvas
        ├── f/                             # every .ts has a .test.ts beside it
        │   ├── buildTerrainMesh.ts        # TerrainGrid -> vertex positions and triangle indices
        │   ├── createTerrainGeometry.ts   # TerrainGrid -> Three.js BufferGeometry with normals
        │   ├── frameTerrainCamera.ts      # TerrainGrid -> camera target, position, near, far
        │   ├── parseTerrainGrid.ts        # JSON -> TerrainGrid
        │   └── readPositiveInteger.ts
        ├── h/
        │   └── useTerrainGrid.ts          # fetch + parse a terrain JSON by url
        └── t/
            ├── TerrainGrid.ts
            └── TerrainMesh.ts
```

### Tests

- Every function file and every class file defines a `t()` function that tests the unit in that file.
- `t()` may be split into `t1()`, `t2()`, `t3()` and so on for tooling. `t()` calls them in order. Each raises `AssertionError` on failure. `t()` returns nothing on success.
- `tests.py` at the repo root is the test runner. It finds files in `terrasim2/k/` and `terrasim2/f/` that were edited since they last passed, imports each one, and calls its `t()`. It reports pass or fail per file.
- `tests.py` tracks edits with a cache of per-file content hashes. A file's hash is recorded only when its `t()` passes. `tests.py --all` runs every file regardless. `tests.py <file>` runs just that file.
- `tests.py --watch` keeps running: it reruns a file's `t()` in a fresh subprocess whenever that file is saved, `a` runs every file, `q` quits.

## App structure

- The visualisation app is `app/` at the repo root: Next.js with TypeScript. The terrain renders as a 3D mesh with orbit controls via Three.js.
- `app/src/c/` holds components, one per file, file named after the component.
- `app/src/f/` holds pure functions, one per file, same rules as the Python `f/`. No React, no browser APIs.
- `app/src/h/` holds hooks, one per file, each named `useSomething`.
- `app/src/t/` holds types shared by more than one file, one type per file, file named after the type. A type used by a single file stays in that file.
- `app/src/app/` is the Next.js routing folder. Pages compose components and hold no logic.
- Function names are verbs here too. Components and hooks are the exceptions: a component is a noun, a hook is `use` plus a noun.

### Tests

- Every file in `c/`, `f/` and `h/` has a test file beside it with the same name and a `.test.ts` or `.test.tsx` suffix. This is the app's equivalent of `t()`; tests stay out of the source file so they stay out of the browser bundle.
- Pure functions are tested against hand-computed outputs. Components are rendered in a test DOM and asserted on. The 3D scene is asserted on its scene graph, not on pixels.
- Vitest is the runner. `vitest --changed` runs only tests for files edited since the last commit, the counterpart of `tests.py`.
