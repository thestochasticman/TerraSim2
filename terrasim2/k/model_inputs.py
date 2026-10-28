import numpy as np

from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.terrain_grid import TerrainGrid
from terrasim2.k.tile_series import TileSeries


class ModelInputs:
    """Everything a model run needs, checked for consistency once.

    Built in memory by ``troi_ingest.ingest`` or read from disk by
    ``load_model_inputs``; written by ``write_model_inputs``. The on-disk
    layout is versioned by ``FORMAT_VERSION``.

    Parameters
    ----------
    grid : TerrainGrid
        Elevation, capacity and the initial moisture.
    cell_map : CellToTileMap
        On ``grid``. Which tile each cell reads for every series.
    rain : TileSeries, millimetres (mm)
        Daily rain per tile.
    pet : TileSeries, millimetres (mm)
        Daily reference evapotranspiration per tile, same tiles and dates as rain.
    meta : dict
        Free-form provenance from the producer (stub, bbox, window, sources).
        Carried to and from disk unchanged; never read by the model.

    Attributes
    ----------
    grid, cell_map, rain, pet, meta : as given
    dates : ndarray (T,), datetime64[D]
    n_days, n_tiles : int, dimensionless
    shape : tuple[int, int], dimensionless
    """

    FORMAT_VERSION = 1

    def __init__(self, grid: TerrainGrid, cell_map: CellToTileMap, rain: TileSeries, pet: TileSeries, meta: dict | None = None):
        if cell_map.grid is not grid:
            raise ValueError("cell_map must be built on grid")
        if rain.n_tiles != cell_map.n_tiles or pet.n_tiles != cell_map.n_tiles:
            raise ValueError(f"rain ({rain.n_tiles}) and pet ({pet.n_tiles}) must have the map's {cell_map.n_tiles} tiles")
        if not np.array_equal(rain.dates, pet.dates):
            raise ValueError("rain and pet must cover the same dates")
        self.grid = grid
        self.cell_map = cell_map
        self.rain = rain
        self.pet = pet
        self.meta: dict = dict(meta or {})

    @property
    def dates(self) -> np.ndarray:
        return self.rain.dates

    @property
    def n_days(self) -> int:
        return self.rain.n_days

    @property
    def n_tiles(self) -> int:
        return self.cell_map.n_tiles

    @property
    def shape(self) -> tuple[int, int]:
        return self.grid.shape


def _parts(n_tiles=2, dates=("2024-01-01", "2024-01-02")):
    grid = TerrainGrid(elevation=np.zeros((2, 3)), cell_size=10.0)
    cell_map = CellToTileMap(grid, tile_index=np.zeros((2, 3), dtype=int), n_tiles=n_tiles)
    rain = TileSeries("rain", "mm", list(dates), np.ones((len(dates), n_tiles)))
    pet = TileSeries("pet", "mm", list(dates), np.ones((len(dates), n_tiles)))
    return grid, cell_map, rain, pet


def t1():
    """Consistent parts are accepted and summarised."""
    grid, cell_map, rain, pet = _parts()
    m = ModelInputs(grid, cell_map, rain, pet, meta={"stub": "x"})
    assert m.shape == (2, 3) and m.n_tiles == 2 and m.n_days == 2
    assert m.dates[0] == np.datetime64("2024-01-01") and m.meta == {"stub": "x"}
    assert ModelInputs(grid, cell_map, rain, pet).meta == {}


def t2():
    """A map on another grid, a tile-count mismatch, or different dates are rejected."""
    grid, cell_map, rain, pet = _parts()
    other_grid = TerrainGrid(elevation=np.zeros((2, 3)), cell_size=10.0)
    other_map = CellToTileMap(other_grid, cell_map.tile_index, n_tiles=2)
    wide = TileSeries("pet", "mm", rain.dates, np.ones((2, 3)))
    shifted = TileSeries("pet", "mm", ["2024-01-02", "2024-01-03"], np.ones((2, 2)))
    for args in ((grid, other_map, rain, pet), (grid, cell_map, rain, wide), (grid, cell_map, rain, shifted)):
        try:
            ModelInputs(*args)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def t():
    t1()
    t2()
