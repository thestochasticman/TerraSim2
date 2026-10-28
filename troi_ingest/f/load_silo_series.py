from unittest import SkipTest

import numpy as np
from pysilo.store import Store
from troi import Troi

from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.terrain_grid import TerrainGrid
from terrasim2.k.tile_series import TileSeries
from troi_ingest.f.compute_silo_tiles import compute_silo_tiles


def load_silo_series(troi: Troi, grid: TerrainGrid, variable: str, name: str, units: str) -> tuple[CellToTileMap, TileSeries]:
    """One SILO variable for a Troi, as a cell-to-tile map on a grid and a per-tile series.

    Each cell of the Troi's window snaps to its nearest SILO point. Each
    distinct point's ``variable`` is fetched for the Troi's dates from the
    SILO store located by the Troi's config. One column per point, one row
    per day.

    Parameters
    ----------
    troi : Troi
        ``bbox`` (degrees), ``start``/``end`` (inclusive dates), ``config``
        (store location and SILO email).
    grid : TerrainGrid
        The terrain the map is laid out on. Must have the window's shape.
    variable : str
        SILO column to read, for example ``"daily_rain"`` or ``"et_short_crop"``.
    name, units : str
        Recorded on the returned series.

    Returns
    -------
    cell_map : CellToTileMap
        On ``grid``, one tile per distinct SILO point.
    series : TileSeries
        In ``units``.
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
        columns.append(df[variable].to_numpy(dtype=np.float64))

    values = np.stack(columns, axis=1)
    return CellToTileMap(grid, tile_index, n_tiles=len(points)), TileSeries(name, units, dates, values)


def _load_or_skip(troi: Troi, grid: TerrainGrid, variable: str) -> tuple[CellToTileMap, TileSeries]:
    try:
        return load_silo_series(troi, grid, variable, variable, "mm")
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
    """Two variables from the same Troi share dates and tiles; both are non-negative daily depths."""
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    grid = _grid_for(troi)
    rain_map, rain = _load_or_skip(troi, grid, "daily_rain")
    et_map, et = _load_or_skip(troi, grid, "et_short_crop")
    assert np.array_equal(rain.dates, et.dates) and rain.n_days == 31
    assert np.array_equal(rain_map.tile_index, et_map.tile_index) and rain.n_tiles == et.n_tiles
    assert np.all(np.nan_to_num(rain.values) >= 0.0) and np.all(np.nan_to_num(et.values) >= 0.0)
    assert 0.5 < np.nanmean(et.values) < 15.0, "January reference ET in mm/day should be a few mm"


def t2():
    """A grid of the wrong shape is rejected before any fetch."""
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    wrong = TerrainGrid(elevation=np.zeros((2, 2)), cell_size=10.0)
    try:
        load_silo_series(troi, wrong, "daily_rain", "rain", "mm")
    except ValueError as err:
        assert "does not match" in str(err)
    else:
        raise AssertionError("expected ValueError for grid shape mismatch")


def t():
    t1()
    t2()
