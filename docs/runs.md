# Runs

<!-- nav -->
← [Process steps](process-steps.md) · [Index](README.md) · [Vegetation](vegetation.md) →
<!-- /nav -->

## The loop

`run_model(step, inputs, params, folder=None, store_params=RunStoreParams())` (`terrasim2/f/run_model.py`) runs a step over every day of the inputs. It builds one `SoilHydraulics` from the soil layers at the inputs' root depth and one `TerrainDerivatives` from the grid and latitude, then for each day expands the rain and demand tile series to cells, multiplies the demand by `inputs.demand_factor` when one is set, and calls the step.

With no folder it returns a `RunResult` in memory. With a folder it writes the histories into a zarr store in blocks and returns a `RunResult` over the store; the arrays are never copied.

## The run store

`create_run_store` makes the group; `write_run_block` writes `n` consecutive days; `load_run_result` opens it read-only.

| Array | Shape | Type | Chunks |
|---|---|---|---|
| `moisture` | (T, rows, cols) | float64, mm | (`chunk_days`, `chunk_rows`, `chunk_cols`) |
| `fluxes` | (T, n_fluxes, rows, cols) | float64, mm | the same, all fluxes in one chunk |

| Attribute | What it holds |
|---|---|
| `dates` | ISO dates, length T |
| `days_written` | How many leading days are safe to read while the run is in progress |
| `complete` | True once every day is written |
| `flux_names` | The step's flux names in axis order, so a reader need not know which step ran |
| `meta` | The inputs' provenance |

`RunStoreParams(chunk_days=32, chunk_rows=256, chunk_cols=256, write_every_days=32, record_fluxes=True)` sets the chunking and the block size. Readers never go past `days_written`; `load_run_result` refuses an incomplete store unless asked.

## Reading a run

`RunResult` holds `dates`, `moisture_history` (T, rows, cols) and `flux_history` (T, n_fluxes, rows, cols) or `None`. The arrays may be zarr arrays; slicing them reads only the chunks touched.

Water content is read back as θ = θwp + moisture / root depth (`compute_water_content`), so a run is comparable with a probe or a TDR reading over the same depth ([observations.md](observations.md)).

## As the service runs it

`app/api/f/execute_run.py` is the worker: given a run folder holding `request.json`, it loads the inputs at the request's root depth (capacity and hydraulics alike), builds the root-depth field and the demand factor if the request asks for them and the site has a vegetation map, picks the step and parameters, and calls `run_model` into `store.zarr`, logging to `worker.log`. `launch_run` starts it as a subprocess so the service stays responsive; `read_run_status` reports `missing`, `running`, `complete` or `failed` from the store and the worker. `python -m app.api.f.execute_run <folder>` runs a worker by hand ([service.md](service.md)).

Compute: the downslope cascade is a Python loop over cells in flow order, about 0.6 s per day on 400,000 cells, so a 2,078-day run at MRI takes about twenty minutes; Tarrawarra (7,000 cells, 432 days) takes seconds. A vectorised, level-by-level cascade would give the same results and is the next engineering step.

<!-- nav -->
← [Process steps](process-steps.md) · [Index](README.md) · [Vegetation](vegetation.md) →
<!-- /nav -->
