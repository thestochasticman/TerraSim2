from unittest import SkipTest

import numpy as np
from troi import Troi

from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.terrain_grid import TerrainGrid
from terrasim2.k.tile_series import TileSeries
from troi_ingest.f.load_silo_series import load_silo_series


def load_pet(troi: Troi, grid: TerrainGrid) -> tuple[CellToTileMap, TileSeries]:
    """Daily SILO reference evapotranspiration (FAO56 short crop) for a Troi, named ``pet`` in mm."""
    return load_silo_series(troi, grid, "et_short_crop", "pet", "mm")


def t1():
    """Named pet in mm, one row per day of the Troi, a few mm per day in January."""
    from troi_ingest.f.make_test_troi import make_test_troi
    from troi_ingest.f.load_rain import _grid_for

    troi = make_test_troi()
    try:
        cell_map, series = load_pet(troi, _grid_for(troi))
    except (OSError, ConnectionError, TimeoutError) as err:
        raise SkipTest(f"SILO store unavailable: {err}") from err
    assert series.name == "pet" and series.units == "mm"
    assert series.n_days == 31 and series.n_tiles == cell_map.n_tiles
    assert 0.5 < np.nanmean(series.values) < 15.0


def t():
    t1()
