from unittest import SkipTest

import numpy as np
from pysilo.store import Store
from troi import Troi

from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.terrain_grid import TerrainGrid
from terrasim2.k.tile_series import TileSeries
from troi_ingest.f.compute_silo_tiles import compute_silo_tiles

VARIABLE = "daily_rain"


def load_rain(troi: Troi, grid: TerrainGrid) -> tuple[CellToTileMap, TileSeries]:
    """Daily SILO rain for a Troi, as a cell-to-tile map on a grid and a per-tile series.

    Each cell of the Troi's window snaps to its nearest SILO point. Each
    distinct point's ``daily_rain`` is fetched for the Troi's dates from
    the SILO store located by the Troi's config (first use downloads; later
    uses read the cache). One column per point, one row per day.

    Parameters
    ----------
    troi : Troi
        ``bbox`` (degrees), ``start``/``end`` (inclusive dates), ``config``
        (store location and SILO email).
    grid : TerrainGrid
        The terrain the map is laid out on. Must have the window's shape.

    Returns
    -------
    cell_map : CellToTileMap
        On ``grid``, one tile per distinct SILO point.
    series : TileSeries
        ``name="rain"``, ``units="mm"``, values in millimetres per day.
    """
    tile_index, points = compute_silo_tiles(troi.bbox)
    if tile_index.shape != grid.shape:
        raise ValueError(f"grid shape {grid.shape} does not match the Troi's window {tile_index.shape}")

    store = Store(config=troi.config)
    columns = []
    dates = None
    for lat, lon in points:
        df = store.get_df(lat, lon, troi.start, troi.end)
        point_dates = df["date"].to_numpy().astype("datetime64[D]")
        if dates is None:
            dates = point_dates
        elif not np.array_equal(point_dates, dates):
            raise ValueError(f"SILO point ({lat}, {lon}) returned different dates from the first point")
        columns.append(df[VARIABLE].to_numpy(dtype=np.float64))

    values = np.stack(columns, axis=1)
    cell_map = CellToTileMap(grid, tile_index, n_tiles=len(points))
    series = TileSeries("rain", "mm", dates, values)
    return cell_map, series


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
    """One row per day of the Troi, one column per SILO point, rain non-negative, map and series agree."""
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    cell_map, series = _load_or_skip(troi, _grid_for(troi))
    assert series.name == "rain" and series.units == "mm"
    assert series.n_days == 31, series.n_days
    assert series.dates[0] == np.datetime64("2024-01-01") and series.dates[-1] == np.datetime64("2024-01-31")
    assert series.n_tiles == cell_map.n_tiles
    assert np.all(np.nan_to_num(series.values) >= 0.0)
    assert cell_map.shape == _grid_for(troi).shape


def t2():
    """Laid onto the cells, a day of rain is flat within each tile."""
    from terrasim2.f.get_values_on_cells import get_values_on_cells
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    cell_map, series = _load_or_skip(troi, _grid_for(troi))
    field = get_values_on_cells(cell_map, series, 0)
    assert field.shape == cell_map.shape
    for k in range(cell_map.n_tiles):
        in_tile = field[cell_map.tile_index == k]
        assert np.all(in_tile == series.values[0, k])


def t3():
    """A grid of the wrong shape is rejected before any fetch."""
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    wrong = TerrainGrid(elevation=np.zeros((2, 2)), cell_size=10.0)
    try:
        load_rain(troi, wrong)
    except ValueError as err:
        assert "does not match" in str(err)
    else:
        raise AssertionError("expected ValueError for grid shape mismatch")


def t():
    t1()
    t2()
    t3()
