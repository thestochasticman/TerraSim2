# Service

<!-- nav -->
← [Ingest](ingest.md) · [Index](README.md) · [Visualiser](visualiser.md) →
<!-- /nav -->

`app/api` is the FastAPI service the viewer talks to. It starts runs as separate processes, serves their state and reads them back for the viewer. It imports `terrasim2` only.

## Start

```
python -m app.api.f.serve [port]      # from the repo root, in the borevitz_lab environment; default port 8000
```

Runs go to `{troi out_dir}/terrasim2_runs/{run_id}/` with `request.json`, `store.zarr` and `worker.log`. Inputs are looked up first under the `troi` output directory and then under `data/dev_sites` (`find_inputs`; `find_observations` and `find_vegetation` search the same roots). `create_app(runs_root, inputs_roots)` builds the app for a test or another layout.

## The run request

`RunRequest` (`app/api/k/run_request.py`, pydantic):

| Field | Default | Meaning |
|---|---|---|
| `stub` | required | A site with prepared inputs |
| `step` | `bucket` | `bucket`, `routed` or `subsurface` |
| `stress_exponent` | 1.0 | Evaporation falls with fullness to this power |
| `initial_fullness` | 0.5 | The plant store's starting fraction of capacity |
| `root_depth` | 0.3 | m; the inputs are prepared at this depth, capacity and hydraulics alike |
| `leak_fraction` | 0.0 | Subsurface: fraction of the free store lost downward per day |
| `rain_hours` | 24.0 | Subsurface: hours the day's rain falls over, setting the infiltration limit |
| `lateral_multiplier` | 1.0 | Subsurface: anisotropy of the downslope drainage |
| `aspect_strength` | 0.0 | Subsurface: demand follows `solar_ratio` to this power |
| `cover_strength` | 0.0 | Any step: demand follows the crop coefficient relative to the site mean to this power, when the site has a vegetation map |
| `tree_root_depth` | none | Any step: tree cells take this depth when the site has a vegetation map |
| `write_every_days` | 1 | Days per block written to the store |
| `chunk_days` | 32 | Store chunking along time |
| `record_fluxes` | true | Whether the flux history is stored |

`compute_run_id(request, inputs_key)` hashes the request with `read_inputs_key(folder)` = `v{version}@{written_at}` to `"{stub}-{12 hex}"`, so the same request on the same inputs is the same run, a complete store is served without rerunning, and a store made from older inputs is never served.

## Routes

| Route | Returns |
|---|---|
| `GET /sites` | Stubs with prepared inputs |
| `POST /runs` | Body `RunRequest` → `{run_id, status}`; starts the worker unless the store is complete or in progress |
| `GET /runs/{id}` | `status` (`missing`, `running`, `complete`, `failed`), `days_written`, `n_days`, `rows`, `cols`, `dates`, `meta` |
| `GET /runs/{id}/terrain` | Elevation, capacity and free capacity at the run's root depth (a depth per cell when the request names a tree depth), upslope cell counts, and the vegetation classes when the site has a map, in the viewer's JSON shape |
| `GET /runs/{id}/moisture/{t}` | One day as little-endian float32 bytes; 409 until written |
| `GET /runs/{id}/series` | Grid-mean daily rain, pet, moisture and every flux named in the store, for the days written |
| `GET /runs/{id}/comparison` | Scores against the site's observations: overall, per survey date (with the day index) and per station, plus layers and stations; 404 without observations |
| `GET /runs/{id}/pairs` | Every observation with the run's value at it: six float32 columns `t, row, col, station, observed, modelled`; 404 likewise |
| `GET /soils/retention` | The book's retention curves per texture for both models over a log suction grid, with θ at field capacity and wilting point and mm per metre |
| `GET /soils/texture` | The USDA triangle on a one-per-cent grid: class, geometric mean diameter, estimated ψe and b per point, plus table 2.4's typical soils |
| `GET /soils/column` | One layered column's available water: query `textures` (six, comma-separated), `root_depth`, `model`; read at the model's conventions |

The comparison pairs every reading in the site's observation file at the run's root depth and starts the run from `initial_fullness`, so its scores differ from the evaluation's, which reads each site's layers against the store and starts from the first survey's mean ([evaluation.md](evaluation.md)).

## Known limitation

`GET /runs/{id}/series` reads the whole flux history to take grid means and fails with a 500 on the largest store (MRI: 2,078 days × 901 × 444 cells × 6 fluxes). Reading in blocks of days, as `pair_run_with_observations` does, is the fix.

## Tests

`python app/api/tests.py --all` runs every file's `t()` (PASS / SKIP / FAIL; `--watch` reruns a file on save). The tests use the example site and a temporary runs root; `launch_run`'s test runs a real worker on the 31-day example.

<!-- nav -->
← [Ingest](ingest.md) · [Index](README.md) · [Visualiser](visualiser.md) →
<!-- /nav -->
