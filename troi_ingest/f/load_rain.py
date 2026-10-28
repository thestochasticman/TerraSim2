from unittest import SkipTest

import numpy as np
from troi import Troi

from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.terrain_grid import TerrainGrid
from terrasim2.k.tile_series import TileSeries
from troi_ingest.f.load_silo_series import load_silo_series


def load_rain(troi: Troi, grid: TerrainGrid) -> tuple[CellToTileMap, TileSeries]:
    """Daily SILO rain for a Troi: ``load_silo_series`` with ``daily_rain``, named ``rain`` in mm."""
    return load_silo_series(troi, grid, "daily_rain", "rain", "mm")


def _load_or_skip(troi: Troi, grid: TerrainGrid) -> tuple[CellToTileMap, TileSeries]:
    try:
        return load_rain(troi, grid)
    except (OSError, ConnectionError, TimeoutError) as err:
        raise SkipTest(f"SILO store unavailable: {err}") from err
    except ValueError as err:
        if "email" in str(err).lower():
            raise SkipTest(f"SILO email not configured: {err}") from err
        raise


def _grid_for(troi: Troi) -> TerrainGrid:
    from troi_ingest.f.compute_window import compute_window

    row0, row1, col0, col1 = compute_window(troi.bbox)
    return TerrainGrid(elevation=np.zeros((row1 - row0, col1 - col0)), cell_size=10.0)


def t1():
    """Named rain in mm, one row per day of the Troi, laid onto cells as flat patches."""
    from terrasim2.f.get_values_on_cells import get_values_on_cells
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    cell_map, series = _load_or_skip(troi, _grid_for(troi))
    assert series.name == "rain" and series.units == "mm"
    assert series.n_days == 31
    assert series.dates[0] == np.datetime64("2024-01-01") and series.dates[-1] == np.datetime64("2024-01-31")
    field = get_values_on_cells(cell_map, series, 0)
    for k in range(cell_map.n_tiles):
        assert np.all(field[cell_map.tile_index == k] == series.values[0, k])


def t():
    t1()
