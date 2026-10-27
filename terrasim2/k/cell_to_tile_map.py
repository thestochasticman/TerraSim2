import numpy as np
import numpy.typing as npt

from terrasim2.k.terrain_grid import TerrainGrid


class CellToTileMap:
    """Which tile each terrain cell belongs to.

    A tile is one column of some coarse data source: a SILO point, a radar
    pixel, anything that gives one value per tile per time. This map says
    nothing about the source; it only records, for each cell, which column
    to read. One map per source lattice, reused for every variable on it.

    Parameters
    ----------
    grid : TerrainGrid
        The terrain this map is laid out on. Fixes the shape of tile_index.
    tile_index : array_like, dimensionless
        Shape (rows, cols), integers in [0, n_tiles). Column each cell reads.
    n_tiles : int, dimensionless
        Number of tiles (columns) in the source. Given explicitly so a tile
        that no cell happens to fall in still counts.

    Attributes
    ----------
    grid : TerrainGrid
    tile_index : ndarray (rows, cols), int
    n_tiles : int, dimensionless
    shape : tuple[int, int], dimensionless
    """

    def __init__(self, grid: TerrainGrid, tile_index: npt.ArrayLike, n_tiles: int):
        index = np.array(tile_index)
        if not np.issubdtype(index.dtype, np.integer):
            raise ValueError(f"tile_index must be integers, got dtype {index.dtype}")
        if index.shape != grid.shape:
            raise ValueError(f"tile_index shape {index.shape} does not match grid shape {grid.shape}")
        if n_tiles < 1:
            raise ValueError(f"n_tiles must be at least 1, got {n_tiles}")
        if index.min() < 0 or index.max() >= n_tiles:
            raise ValueError(f"tile_index values must lie in [0, {n_tiles}), got [{index.min()}, {index.max()}]")
        self.grid = grid
        self.tile_index: np.ndarray = index.astype(np.intp)
        self.n_tiles: int = int(n_tiles)

    @property
    def shape(self) -> tuple[int, int]:
        return self.grid.shape

    def spread_to_cells(self, per_tile: npt.ArrayLike) -> np.ndarray:
        """Lay one value per tile out over the cells.

        Parameters
        ----------
        per_tile : array_like
            Shape (n_tiles,), any units. One value per tile.

        Returns
        -------
        ndarray
            Shape (rows, cols), same units. Each cell holds its tile's value.
        """
        values = np.asarray(per_tile)
        if values.shape != (self.n_tiles,):
            raise ValueError(f"expected {self.n_tiles} values, one per tile, got shape {values.shape}")
        return values[self.tile_index]


def _grid() -> TerrainGrid:
    return TerrainGrid(elevation=np.zeros((2, 3)), cell_size=10.0)


def t1():
    """Each cell takes its tile's value."""
    m = CellToTileMap(_grid(), tile_index=[[0, 0, 1], [0, 1, 1]], n_tiles=2)
    assert m.shape == (2, 3) and m.n_tiles == 2
    out = m.spread_to_cells([5.0, 20.0])
    assert np.array_equal(out, [[5.0, 5.0, 20.0], [5.0, 20.0, 20.0]])


def t2():
    """A tile with no cells is allowed when n_tiles says it exists."""
    m = CellToTileMap(_grid(), tile_index=np.zeros((2, 3), dtype=int), n_tiles=3)
    assert np.all(m.spread_to_cells([7.0, 8.0, 9.0]) == 7.0)


def t3():
    """Wrong shape, non-integers, out-of-range indices and a wrong-length vector are rejected."""
    for bad in (
        dict(tile_index=[[0, 1], [1, 0]], n_tiles=2),
        dict(tile_index=[[0.0, 0.0, 1.0], [0.0, 1.0, 1.0]], n_tiles=2),
        dict(tile_index=[[0, 0, 2], [0, 1, 1]], n_tiles=2),
        dict(tile_index=[[0, 0, -1], [0, 1, 1]], n_tiles=2),
        dict(tile_index=np.zeros((2, 3), dtype=int), n_tiles=0),
    ):
        try:
            CellToTileMap(_grid(), **bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
    m = CellToTileMap(_grid(), tile_index=[[0, 0, 1], [0, 1, 1]], n_tiles=2)
    try:
        m.spread_to_cells([1.0, 2.0, 3.0])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for wrong-length vector")


def t():
    t1()
    t2()
    t3()
