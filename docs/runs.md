# Runs

<!-- nav -->
← [Process steps](process-steps.md) · [Index](README.md) · [Vegetation](vegetation.md) →
<!-- /nav -->

## The loop

`run_model(step, inputs, params, folder=None, store_params=RunStoreParams())` (`terrasim2/f/run_model.py`) runs a step over every day of the inputs:

1. It builds one `SoilHydraulics` from the soil layers at `inputs.root_depth` and replaces its `capacity` with `inputs.grid.capacity`. Without soil layers, it uses the grid's capacity alone.
2. It builds one `TerrainDerivatives` from the grid and `inputs.latitude`.
3. Each day, it lays rain and reference evapotranspiration onto cells, multiplies the latter by `inputs.demand_factor` if one is set, and calls the step.

The initial state is `inputs.grid.moisture`, which the loop updates in place. The caller sets it.

With no `folder`, the histories are held in memory. The flux history alone takes `days × n_fluxes × rows × cols × 8` bytes. For MRI under the subsurface step (2,078 days, 7 fluxes, 400,044 cells) that is 43 GB, so in practice MRI needs a folder and enough disk for the store.

## The run store

With a `folder`, `run_model` writes a zarr group in blocks of `write_every_days` days and returns a `RunResult` that reads from it. `create_run_store` creates the group, `write_run_block` writes a block, and `load_run_result` opens the store read-only. It refuses an incomplete store unless asked.

| Array | Shape | Type | Chunks |
|---|---|---|---|
| `moisture` | (T, rows, cols) | float64, mm | (`chunk_days`, `chunk_rows`, `chunk_cols`) |
| `fluxes` | (T, n_fluxes, rows, cols) | float64, mm | (`chunk_days`, n_fluxes, `chunk_rows`, `chunk_cols`) |

Both arrays are created filled with NaN.

| Attribute | Content |
|---|---|
| `dates` | ISO dates, length T |
| `days_written` | Number of leading days written; readers must not read beyond it |
| `complete` | True once every day is written |
| `flux_names` | Flux names in axis-1 order |
| `meta` | The inputs' provenance |

`RunStoreParams` defaults: `chunk_days=32`, `chunk_rows=256`, `chunk_cols=256`, `write_every_days=32`, `record_fluxes=True`. With `record_fluxes=False` no `fluxes` array is written.

## Reading a run

`RunResult` holds `dates`, `moisture_history` and `flux_history` (or `None`). Over a store these are zarr arrays, and slicing reads only the chunks touched.

Volumetric water content is θ = θwp + moisture / root depth (`compute_water_content`). This assumes the cell's water is spread evenly over the root depth.

## Service runs

`app/api/f/execute_run.py` loads the inputs at the request's root depth, sets the initial moisture to `initial_fullness × capacity`, builds the root-depth field and demand factor if requested, and calls `run_model` into `{run folder}/store.zarr`, logging to `worker.log`. `launch_run` starts it as a subprocess. `python -m app.api.f.execute_run <folder>` runs it directly ([service.md](service.md)).

## Compute time

The cascade is processed by flow level (pull request #33), replacing a loop over single cells. The figures below were measured on 24 November 2026 on the lab workstation, for one day of the subsurface step on each site's wettest day:

| Site | Cells | Flow levels | Per-cell loop, ms per day | By level, ms per day |
|---|---|---|---|---|
| Tarrawarra | 6,984 | 100 | 29 | 4 |
| Esdale | 70,180 | 389 | 117 | 15 |
| MRI | 400,044 | 1,164 | 585 | 54 |

A year of MRI takes 20 s, which puts a full 2,078-day MRI run at about 2 minutes of stepping, before writing to the store. Whole Esdale runs took 47 s with the loop and 7.5 s by level, with the same scores to four decimals.
