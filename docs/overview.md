# Overview

<!-- nav -->
[Index](README.md) · [Model inputs](model-inputs.md) →
<!-- /nav -->

TerraSim2 is a daily soil-water balance of the root zone on a 10 m grid. It consists of a model package, an input-preparation package that reads the lab's data stores, a web service that runs the model, and a viewer.

These pages describe the code on `soil-physics-with-python` at commit `b8eebfc`.

## Scope

The model represents, per 10 m cell and per day:

- infiltration of rain, limited by the room in the cell's store and, in the subsurface step, by a daily infiltration limit;
- evapotranspiration as a reference demand scaled by store fullness;
- overflow and subsurface lateral flow passed to one downslope neighbour within the day;
- percolation out of the bottom of the root zone.

It does not represent an energy balance, plant growth, nutrients, a layered soil profile with vertical flow between layers, capillary rise, a water table, canopy interception, snow, sub-daily rainfall, channels, or management. See [process-steps.md](process-steps.md) for the exact rules.

Inputs come from SILO daily climate (0.05°, about 5 km), the Copernicus GLO-30 elevation model (30 m), the Soil and Landscape Grid of Australia (SLGA, 90 m) and Sentinel-2 NDVI (10 m). The model's output carries the spatial information of these inputs and no more. Within one SILO tile, every cell receives the same rain.

## Programs

```
troi_ingest  ──ModelInputs folder──▶  terrasim2  ◀──imports──  app/api  ◀──HTTP──  app/visualiser
```

| Program | Role | Imports |
|---|---|---|
| `troi_ingest/` | Reads the lab's stores for a bounding box and date range, resamples each source onto the 10 m EPSG:6933 lattice of Sentinel-2, and writes inputs, observations and vegetation maps to versioned folders | `troi`, `pysilo`, `pycopdem`, `pyslga`, `pysentinel2`, `rasterio`, `pandas`, `terrasim2` |
| `terrasim2/` | The model: classes in `k/`, functions in `f/`, the run loop, and readers and writers of its own formats | NumPy; zarr for run stores. It does not import `troi_ingest` or any lab package |
| `app/api/` | FastAPI service that runs the model in subprocesses and serves results | `terrasim2`, FastAPI, pydantic, uvicorn |
| `app/visualiser/` | Next.js and TypeScript viewer | Calls `app/api` only |

The ingest hands the model a `ModelInputs` folder ([model-inputs.md](model-inputs.md)). The model hands the service a zarr run store ([runs.md](runs.md)).

## Code conventions

These rules are stated in `CLAUDE.md` and enforced by review. No linter or check enforces them.

- One unit per file. `k/` holds classes and `f/` holds functions, and each file is named after its unit. `troi_ingest` and `app/api` use the same layout. The viewer uses `src/c/` for components, `src/f/` for pure functions, `src/h/` for hooks, `src/t/` for shared types and `src/api/` for fetch wrappers.
- Function and method names are verbs. Properties are nouns.
- Every physical quantity states its unit in the docstring.
- Every Python unit file defines a `t()` test. Every viewer file in `c/`, `f/` and `h/` has a `.test.ts(x)` file beside it.
- Soil physics follows *Soil Physics with Python* (Bittelli, Campbell and Tomei, 2015), cited by equation number.
- `CLAUDE.md` asks for Python 3.12 or later. The `borevitz_lab` environment the code is run and tested in is Python 3.11.15, and the code runs there.

## Layout

```
TerraSim2/
├── CLAUDE.md            # compact reference and the file tree
├── docs/                # these pages
├── tests.py             # terrasim2 test runner
├── terrasim2/           # model: k/ classes, f/ functions
├── troi_ingest/         # input preparation: k/, f/, tests.py
├── app/api/             # service: k/, f/, tests.py
├── app/visualiser/      # viewer: src/{c,f,h,t,api,app}
└── data/
    ├── dense_sites.csv  # one row per validation site: stub, bbox, start, end
    ├── dense_sites.md   # the same table with sources and caveats
    └── dev_sites/       # committed inputs, observations and vegetation maps, 27 MB
```
