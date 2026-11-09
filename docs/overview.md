# Overview

<!-- nav -->
[Index](README.md) · [Model inputs](model-inputs.md) →
<!-- /nav -->

TerraSim2 is a process-based model of soil water on a 10 m terrain grid, with the tooling needed to prepare its inputs from public national datasets, run it, look at a run as it proceeds, and score it against field observations.

## Why

Soil moisture is decided at the scale of a paddock or hillslope: aspect, drainage position and soil depth change root-zone water content by 0.1–0.2 m³/m³ over tens of metres. Satellite retrievals resolve tens of kilometres, land-surface models about 5 km, and in-situ networks are points. The inputs for a finer estimate are public and cover Australia: SILO daily climate at 0.05°, the Copernicus 30 m elevation model, the Soil and Landscape Grid of Australia (SLGA) at 90 m, and Sentinel-2 imagery at 10 m every five days. TerraSim2 combines them on a 10 m grid and reports its own error against whatever has been measured on the ground.

## Three programs

```
troi_ingest  ──ModelInputs──▶  terrasim2  ◀──  app/api  ◀──  app/visualiser
(prepare)                      (model)         (service)      (viewer)
```

| Program | Role | Depends on |
|---|---|---|
| `troi_ingest/` | Reads the lab's data stores for a bounding box and date range, projects each source onto the Sentinel-2 10 m lattice, and writes prepared inputs, observations and a vegetation map to versioned folders | `troi`, `pysilo`, `pycopdem`, `pyslga`, `pysentinel2`, and `terrasim2` |
| `terrasim2/` | The model: classes, functions, the run loop and the readers and writers of its own formats | NumPy only (zarr for run stores). It never imports `troi_ingest` or a lab package and never touches a data store |
| `app/api/` | A FastAPI service that executes runs as separate processes and serves their state | `terrasim2` |
| `app/visualiser/` | A Next.js + TypeScript viewer: the terrain in 3D, the daily series, the comparison with observations, and the soil-physics reference pages | Node; talks only to `app/api` |

The handoff between the ingest and the model is a `ModelInputs` object: a terrain grid, a tile map onto each coarse source, the daily series, the soil layers, the latitude and free-form provenance. In memory it is one object; on disk it is one versioned folder of NumPy arrays and CSV files that only NumPy and the standard library are needed to read ([model-inputs.md](model-inputs.md)).

The handoff between the model and the service is a run store: a zarr group of the moisture and flux histories with the run's dates and flux names in its attributes ([runs.md](runs.md)). The viewer reads the service only.

## Conventions that hold everywhere

These are what keep the model publishable and every unit testable on its own.

- **One unit per file.** In Python, `terrasim2/k/` holds classes and `terrasim2/f/` holds functions, one per file, the file named after the unit (`terrasim2/f/bucket_step.py` defines `bucket_step`; `terrasim2/k/grid.py` defines `Grid`). There is no `utils.py`. `troi_ingest` and `app/api` follow the same `k/` and `f/` layout. In the viewer, `src/c/` holds components, `src/f/` pure functions, `src/h/` hooks, `src/t/` shared types, `src/api/` the fetch wrappers; again one per file.
- **Names are verbs.** Every function and method name is a verb (`get_cell`, `compute_capacity`, `write_model_inputs`). Properties are nouns. Components are nouns; hooks are `use` plus a noun.
- **Units in docstrings.** Every physical quantity states its unit in the docstring entry for each parameter and attribute (`mm`, `m³/m³`, `J/kg`, `kg s m⁻³`). There are no unit comments in code lines.
- **Every file tests itself.** Every Python unit file defines `t()`, split into `t1()`, `t2()`, … where useful, raising `AssertionError` on failure. Every viewer file in `c/`, `f/` and `h/` has a `.test.ts(x)` beside it. See [development.md](development.md) for the runners.
- **Physics is cited.** Soil physics comes from *Soil Physics with Python* (Bittelli, Campbell and Tomei, 2015), cited by equation number in the docstrings.
- **Modern Python.** Python 3.12 or later; `X | None` and `tuple[int, int]` directly; no `from __future__ import annotations`.

## Where things are

```
TerraSim2/
├── CLAUDE.md            # the compact reference the code is held to
├── docs/                # these pages
├── tests.py             # terrasim2 test runner
├── terrasim2/           # the model: k/ classes, f/ functions
├── troi_ingest/         # input preparation from the lab stores: k/, f/, tests.py
├── app/api/             # the service: k/, f/, tests.py
├── app/visualiser/      # the viewer: src/{c,f,h,t,api,app}
└── data/
    ├── dense_sites.csv  # one row per validation site: stub, bbox, start, end
    ├── dense_sites.md   # the same with caveats and provenance
    └── dev_sites/       # committed prepared inputs, observations and vegetation per site
```

<!-- nav -->
[Index](README.md) · [Model inputs](model-inputs.md) →
<!-- /nav -->
