import numpy as np

from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.tile_series import TileSeries


def get_values_on_cells(cell_map: CellToTileMap, series: TileSeries, t: int) -> np.ndarray:
    """A series' values on every terrain cell for one day.

    Each cell takes the value of the tile it belongs to. No scaling or
    interpolation: tiles come out as flat patches with hard edges.

    Parameters
    ----------
    cell_map : CellToTileMap
        Which tile each cell reads.
    series : TileSeries
        The variable, with one column per tile. Must have the same number
        of tiles as cell_map.
    t : int, dimensionless
        Day index into ``series.dates``.

    Returns
    -------
    ndarray, in ``series.units``
        Shape (rows, cols).
    """
    if series.n_tiles != cell_map.n_tiles:
        raise ValueError(f"series has {series.n_tiles} tiles but the map has {cell_map.n_tiles}")
    if not 0 <= t < series.n_days:
        raise IndexError(f"day index {t} outside [0, {series.n_days})")
    return cell_map.spread_to_cells(series.values[t])


def _fixture() -> tuple[CellToTileMap, TileSeries]:
    from terrasim2.k.terrain_grid import TerrainGrid

    grid = TerrainGrid(elevation=np.zeros((2, 3)), cell_size=10.0)
    cell_map = CellToTileMap(grid, tile_index=[[0, 0, 1], [0, 1, 1]], n_tiles=2)
    series = TileSeries("rain", "mm", dates=["2024-01-01", "2024-01-02"], values=[[5.0, 20.0], [0.0, 1.5]])
    return cell_map, series


def t1():
    """Day t comes out as patches of that day's tile values."""
    cell_map, series = _fixture()
    assert np.array_equal(get_values_on_cells(cell_map, series, 0), [[5.0, 5.0, 20.0], [5.0, 20.0, 20.0]])
    assert np.array_equal(get_values_on_cells(cell_map, series, 1), [[0.0, 0.0, 1.5], [0.0, 1.5, 1.5]])


def t2():
    """Depth is preserved: every cell in a tile gets the tile's full value, not a share of it."""
    cell_map, series = _fixture()
    out = get_values_on_cells(cell_map, series, 0)
    assert np.all(out[cell_map.tile_index == 1] == 20.0)


def t3():
    """A series with a different tile count, or a day out of range, is rejected."""
    cell_map, series = _fixture()
    three = TileSeries("rain", "mm", dates=series.dates, values=np.zeros((2, 3)))
    try:
        get_values_on_cells(cell_map, three, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for tile count mismatch")
    for bad_t in (-1, 2):
        try:
            get_values_on_cells(cell_map, series, bad_t)
        except IndexError:
            pass
        else:
            raise AssertionError(f"expected IndexError for t={bad_t}")


def t():
    t1()
    t2()
    t3()
