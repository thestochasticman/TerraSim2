from typing import Any

import numpy as np

from terrasim2.f.get_values_on_cells import get_values_on_cells
from terrasim2.k.model_inputs import ModelInputs
from terrasim2.k.run_result import RunResult
from terrasim2.k.step_function import StepFunction


def run_model(step: StepFunction, inputs: ModelInputs, params: Any) -> RunResult:
    """Run a process step day by day over the whole series.

    Each day the rain and reference evapotranspiration fields are laid onto
    the cells, the step is called with the grid's moisture and capacity, and
    the moisture it returns is written back to the grid and recorded. The
    fluxes it returns are recorded too, one slice per day. The physics lives
    entirely in ``step``.

    Parameters
    ----------
    step : StepFunction
        The process to run, for example ``step_bucket_model``.
    inputs : ModelInputs
        ``inputs.grid.moisture`` is the initial state and is updated in place.
    params : Any
        Passed through to ``step``.

    Returns
    -------
    RunResult
        Dates, moisture at the end of every day, and every day's fluxes.
    """
    grid, cell_map = inputs.grid, inputs.cell_map
    moisture_history = np.empty((inputs.n_days, *grid.shape), dtype=np.float64)
    flux_history = None
    for t in range(inputs.n_days):
        rain_today = get_values_on_cells(cell_map, inputs.rain, t)
        pet_today = get_values_on_cells(cell_map, inputs.pet, t)
        grid.moisture, fluxes = step(grid.moisture, grid.capacity, rain_today, pet_today, params)
        if flux_history is None:
            flux_history = np.empty((inputs.n_days, *fluxes.shape), dtype=np.float64)
        moisture_history[t] = grid.moisture
        flux_history[t] = fluxes
    return RunResult(inputs.dates, moisture_history, flux_history)


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


def t():
    t1()
    t2()
