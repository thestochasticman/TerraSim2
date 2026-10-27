from unittest import SkipTest

from pysentinel2 import grid as s2
from troi import Troi

from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.terrain_grid import TerrainGrid
from terrasim2.k.tile_series import TileSeries
from troi_ingest.f.load_elevation import load_elevation
from troi_ingest.f.load_rain import load_rain


def ingest(troi: Troi) -> tuple[TerrainGrid, CellToTileMap, TileSeries]:
    """Build TerraSim2 inputs for a Troi on the Sentinel-2 grid.

    Parameters
    ----------
    troi : Troi
        Region (``bbox``, degrees), dates (``start``/``end``) and store
        location plus credentials (``config``).

    Returns
    -------
    grid : TerrainGrid
        Elevation in metres (m) on the 10 m window that fits the bbox,
        with default capacity and zero moisture.
    rain_map : CellToTileMap
        Which SILO tile each cell of ``grid`` reads.
    rain : TileSeries
        Daily SILO rain, millimetres (mm), one column per tile, for the
        Troi's dates.
    """
    elevation = load_elevation(troi)
    grid = TerrainGrid(elevation=elevation, cell_size=s2.RES)
    rain_map, rain = load_rain(troi, grid)
    return grid, rain_map, rain


def t1():
    """The three outputs agree with each other and with the Troi."""
    import numpy as np

    from terrasim2.f.get_values_on_cells import get_values_on_cells
    from troi_ingest.f.compute_window import compute_window
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    try:
        grid, rain_map, rain = ingest(troi)
    except (OSError, ConnectionError, TimeoutError) as err:
        raise SkipTest(f"a data store is unavailable: {err}") from err
    row0, row1, col0, col1 = compute_window(troi.bbox)
    assert grid.shape == (row1 - row0, col1 - col0)
    assert grid.cell_size == 10.0
    assert 100 < grid.elevation.min() < grid.elevation.max() < 1500
    assert rain_map.grid is grid and rain_map.shape == grid.shape
    assert rain.n_tiles == rain_map.n_tiles
    assert rain.dates[0] == np.datetime64(troi.start) and rain.dates[-1] == np.datetime64(troi.end)
    assert get_values_on_cells(rain_map, rain, 0).shape == grid.shape


def t():
    t1()
