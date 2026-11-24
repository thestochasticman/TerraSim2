# Service

<!-- nav -->
← [Ingest](ingest.md) · [Index](README.md) · [Visualiser](visualiser.md) →
<!-- /nav -->

`app/api` is a FastAPI service. It runs the model in subprocesses and serves results to the viewer. It imports `terrasim2` and does not import `troi_ingest`.

## Start

```
python -m app.api.f.serve [port]      # from the repository root, borevitz_lab environment; default port 8000, host 127.0.0.1
```

Runs are written to `{troi out_dir}/terrasim2_runs/{run_id}/` as `request.json`, `store.zarr` and `worker.log`. Inputs are looked up first under the `troi` output directory, then under `data/dev_sites` (`find_inputs`). `find_observations` and `find_vegetation` search the same roots. `create_app(runs_root, inputs_roots)` builds the app with other roots, as the tests do.

## Run request

`RunRequest` (`app/api/k/run_request.py`, pydantic):

| Field | Default | Constraint | Meaning |
|---|---|---|---|
| `stub` | required | non-empty | Site with prepared inputs |
| `step` | `bucket` | `bucket`, `routed`, `subsurface` | Process step |
| `stress_exponent` | 1.0 | > 0 | Exponent on store fullness in evapotranspiration |
| `initial_fullness` | 0.5 | 0 to 1 | Starting moisture as a fraction of `capacity` (plant store); the free store starts empty |
| `root_depth` | 0.3 | > 0 | m; inputs and hydraulics are prepared at this depth |
| `percolation_fraction` | 0.0 | 0 to 1 | Subsurface step only |
| `rain_hours` | 24.0 | > 0 | Subsurface step only; sets the infiltration limit |
| `lateral_multiplier` | 1.0 | > 0 | Subsurface step only |
| `aspect_strength` | 0.0 | ≥ 0 | Subsurface step only |
| `cover_strength` | 0.0 | ≥ 0 | Any step; needs a vegetation map |
| `tree_root_depth` | none | > 0 | Any step; needs a vegetation map |
| `write_every_days` | 1 | ≥ 1 | Days per block written to the store |
| `chunk_days` | 32 | ≥ 1 | Store chunking along time |
| `record_fluxes` | true | | Whether fluxes are stored |

Parameters that do not apply to the chosen step are accepted and ignored.

`compute_run_id(request, inputs_key)` hashes the request together with `read_inputs_key(folder)` = `v{version}@{written_at}` to `"{stub}-{12 hex}"`. The same request on the same inputs gives the same id. A complete store is served without re-running, and a store made from different inputs is not reused.

## Routes

| Route | Response |
|---|---|
| `GET /sites` | Stubs with prepared inputs |
| `POST /runs` | Body `RunRequest`; returns `{run_id, status}`. Returns `complete` if the store is complete. Otherwise starts a worker, unless one started by this process is still running |
| `GET /runs/{id}` | `status` (`missing`, `running`, `complete` or `failed`), `days_written`, `n_days`, `rows`, `cols`, `dates`, `meta` |
| `GET /runs/{id}/terrain` | Elevation, capacity and free capacity at the run's root depth, upslope cell counts, and vegetation classes if a map exists, as JSON |
| `GET /runs/{id}/moisture/{t}` | Day `t` as little-endian float32, row-major; 409 until written |
| `GET /runs/{id}/series` | Grid-mean daily rain, reference evapotranspiration, moisture and every stored flux, for the days written; 409 before writing starts |
| `GET /runs/{id}/comparison` | Scores against the site's observations, overall, per date and per station; 404 without observations |
| `GET /runs/{id}/pairs` | Six float32 columns `t, row, col, station, observed, modelled`; 404 without observations |
| `GET /soils/retention` | Textbook retention curves per texture, both models, at −33/−1500 J/kg |
| `GET /soils/texture` | USDA triangle on a 1 % grid with class, geometric mean diameter, estimated ψe and b |
| `GET /soils/column` | Available water of a six-layer column; query `textures`, `root_depth`, `model`; at the model's conventions |

The comparison route pairs every observation record at the run's root depth, whatever its measured depth, and the run starts from `initial_fullness`. Its numbers therefore differ from [evaluation.md](evaluation.md).

## Known limitations

- **Failure detection.** `failed` is reported only for workers started by the running service process, and only when they exit with a non-zero code. If the service restarts during a run, an incomplete store reports `running` indefinitely. A new `POST /runs` with the same request then starts a new worker.
- **Concurrency.** There is no limit on concurrent workers and no queue.
- **Series memory.** `GET /runs/{id}/series` reads the flux history 64 days at a time. At MRI one block is 64 × 7 × 400,044 × 8 bytes, about 1.4 GB.
- **Authentication.** There is none. The service binds to 127.0.0.1.

## Tests

`python app/api/tests.py --all` runs each file's `t()` and reports PASS, SKIP or FAIL; `--watch` re-runs a file when it is saved. The tests use the `example` site and a temporary runs root. `launch_run`'s test runs a real worker on the 31-day example.
