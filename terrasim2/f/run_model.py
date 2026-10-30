from pathlib import Path
from typing import Any

import numpy as np

from terrasim2.f.create_run_store import create_run_store
from terrasim2.f.get_values_on_cells import get_values_on_cells
from terrasim2.f.load_run_result import load_run_result
from terrasim2.f.write_run_block import write_run_block
from terrasim2.k.model_inputs import ModelInputs
from terrasim2.k.run_result import RunResult
from terrasim2.k.run_store_params import RunStoreParams
from terrasim2.k.step_function import StepFunction


def run_model(
    step: StepFunction,
    inputs: ModelInputs,
    params: Any,
    folder: Path | None = None,
    store_params: RunStoreParams = RunStoreParams(),
) -> RunResult:
    """Run a process step day by day over the whole series.

    Each day the rain and reference evapotranspiration fields are laid onto
    the cells, the step is called with the grid's moisture and capacity, and
    the moisture it returns is written back to the grid and recorded along
    with the fluxes. The physics lives entirely in ``step``.

    With no ``folder`` the histories are kept in memory. With one, they are
    written to a zarr store there in blocks of ``store_params.write_every_days``
    days, so memory never holds more than one block, and the returned result
    reads from that store.

    Parameters
    ----------
    step : StepFunction
        The process to run, for example ``step_bucket_model``.
    inputs : ModelInputs
        ``inputs.grid.moisture`` is the initial state and is updated in place.
    params : Any
        Passed through to ``step``.
    folder : Path, optional
        Where to write the run store. Replaced if it exists.
    store_params : RunStoreParams
        Chunking, write frequency and whether fluxes are recorded.
        ``record_fluxes`` applies to in-memory runs too.

    Returns
    -------
    RunResult
        Dates, moisture at the end of every day, and every day's fluxes if recorded.
    """
    grid = inputs.grid
    record_fluxes = store_params.record_fluxes

    if folder is None:
        moisture_history = np.empty((inputs.n_days, *grid.shape), dtype=np.float64)
        flux_history = None
        for t in range(inputs.n_days):
            fluxes = _step_day(step, inputs, params, t)
            moisture_history[t] = grid.moisture
            if record_fluxes:
                if flux_history is None:
                    flux_history = np.empty((inputs.n_days, *fluxes.shape), dtype=np.float64)
                flux_history[t] = fluxes
        return RunResult(inputs.dates, moisture_history, flux_history)

    group = None
    block_moisture: list[np.ndarray] = []
    block_fluxes: list[np.ndarray] = []
    t0 = 0
    for t in range(inputs.n_days):
        fluxes = _step_day(step, inputs, params, t)
        block_moisture.append(grid.moisture)
        if record_fluxes:
            block_fluxes.append(fluxes)
        if len(block_moisture) == store_params.write_every_days or t == inputs.n_days - 1:
            if group is None:
                group = create_run_store(inputs, fluxes.shape[0], folder, store_params)
            write_run_block(group, t0, np.stack(block_moisture), np.stack(block_fluxes) if record_fluxes else None)
            t0 = t + 1
            block_moisture, block_fluxes = [], []
    group.attrs["complete"] = True
    return load_run_result(folder)


def _step_day(step: StepFunction, inputs: ModelInputs, params: Any, t: int) -> np.ndarray:
    """Advance the grid by day t and return that day's fluxes."""
    rain_today = get_values_on_cells(inputs.cell_map, inputs.rain, t)
    pet_today = get_values_on_cells(inputs.cell_map, inputs.pet, t)
    inputs.grid.moisture, fluxes = step(inputs.grid.moisture, inputs.grid.capacity, rain_today, pet_today, params)
    return fluxes


def _inputs() -> ModelInputs:
    from terrasim2.k.cell_to_tile_map import CellToTileMap
    from terrasim2.k.terrain_grid import TerrainGrid
    from terrasim2.k.tile_series import TileSeries

    grid = TerrainGrid(elevation=np.zeros((2, 3)), cell_size=10.0, capacity=np.full((2, 3), 100.0))
    cell_map = CellToTileMap(grid, tile_index=[[0, 0, 1], [0, 1, 1]], n_tiles=2)
    dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
    rain = TileSeries("rain", "mm", dates, [[10.0, 0.0], [0.0, 30.0], [5.0, 5.0]])
    pet = TileSeries("pet", "mm", dates, [[2.0, 2.0], [2.0, 2.0], [2.0, 2.0]])
    return ModelInputs(grid, cell_map, rain, pet)


def _site_inputs(stub: str) -> ModelInputs:
    from terrasim2.f.load_model_inputs import load_model_inputs

    return load_model_inputs(Path(__file__).resolve().parents[2] / "dev_data" / stub / "model_inputs")


def t1():
    """With the real bucket step: a day per date, grid ends where history ends, fluxes close the water balance."""
    from terrasim2.f.step_bucket_model import step_bucket_model
    from terrasim2.k.bucket_flux import BucketFlux
    from terrasim2.k.bucket_model_params import BucketModelParams

    inputs = _inputs()
    result = run_model(step_bucket_model, inputs, BucketModelParams())
    assert result.n_days == 3 and result.n_fluxes == 3 and result.shape == (2, 3)
    assert np.array_equal(result.get_moisture(2), inputs.grid.moisture)
    total_rain = sum(get_values_on_cells(inputs.cell_map, inputs.rain, t) for t in range(3))
    out = result.get_flux_total(BucketFlux.RUNOFF) + result.get_flux_total(BucketFlux.EVAPORATION)
    assert np.abs(result.get_moisture(2) - (total_rain - out)).max() < 1e-9


def t2():
    """The step is a parameter: a recording step sees one call per day with that day's rain, and its fluxes are kept per day."""
    seen = []

    def recording_step(moisture, capacity, rain, pet, params):
        seen.append(rain.copy())
        return moisture + rain, rain[np.newaxis]

    inputs = _inputs()
    result = run_model(recording_step, inputs, None)
    assert len(seen) == 3 and result.n_fluxes == 1
    assert np.array_equal(seen[1], [[0.0, 0.0, 30.0], [0.0, 30.0, 30.0]])
    assert np.array_equal(result.flux_history[1, 0], seen[1])
    assert np.array_equal(result.get_flux_total(0), sum(seen))
    assert np.array_equal(inputs.grid.moisture, sum(seen))


def t3():
    """A run written to disk in small blocks equals the same run in memory, and loads back complete."""
    import tempfile

    from terrasim2.f.step_bucket_model import step_bucket_model
    from terrasim2.k.bucket_model_params import BucketModelParams

    a, b = _site_inputs("tarrawarra"), _site_inputs("tarrawarra")
    in_memory = run_model(step_bucket_model, a, BucketModelParams())
    folder = Path(tempfile.mkdtemp()) / "tarrawarra.zarr"
    on_disk = run_model(step_bucket_model, b, BucketModelParams(), folder=folder, store_params=RunStoreParams(chunk_days=50, write_every_days=37))
    assert on_disk.n_days == in_memory.n_days and on_disk.n_fluxes == 3
    assert np.array_equal(np.asarray(on_disk.moisture_history[:]), in_memory.moisture_history)
    assert np.array_equal(np.asarray(on_disk.flux_history[:]), in_memory.flux_history)
    reloaded = load_run_result(folder)
    assert np.array_equal(reloaded.get_moisture(100), in_memory.get_moisture(100))
    assert np.array_equal(reloaded.dates, in_memory.dates)


def t4():
    """With record_fluxes off, neither path stores fluxes and the moisture is unchanged."""
    import tempfile

    from terrasim2.f.step_bucket_model import step_bucket_model
    from terrasim2.k.bucket_model_params import BucketModelParams

    quiet = RunStoreParams(record_fluxes=False)
    mem = run_model(step_bucket_model, _inputs(), BucketModelParams(), store_params=quiet)
    disk = run_model(step_bucket_model, _inputs(), BucketModelParams(), folder=Path(tempfile.mkdtemp()) / "q.zarr", store_params=quiet)
    full = run_model(step_bucket_model, _inputs(), BucketModelParams())
    assert mem.n_fluxes == 0 and disk.n_fluxes == 0
    assert np.array_equal(mem.moisture_history, full.moisture_history)
    assert np.array_equal(np.asarray(disk.moisture_history[:]), full.moisture_history)


def t():
    t1()
    t2()
    t3()
    t4()
