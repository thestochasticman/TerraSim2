import warnings
from datetime import date
from unittest import SkipTest

import numpy as np
from pysentinel2.cube import Cube
from troi import Troi

from terrasim2.k.terrain_grid import TerrainGrid

# The NDVI statistics a vegetation map is classified from, in the order they are stored.
FEATURES = ("low", "median", "high")


def load_ndvi_features(troi: Troi, grid: TerrainGrid, start: date, end: date, min_clear: int = 8) -> dict[str, np.ndarray]:
    """What NDVI did at each cell over a period, from the lab's Sentinel-2 cube.

    Every cloud-free look between ``start`` and ``end`` is read (the cube
    downloads what it lacks), NDVI is computed on read, and per cell the
    10th, 50th and 90th percentiles over time are taken: the greenness
    the cell keeps through its brownest season, its typical greenness,
    and its peak. Cells seen clearly fewer than ``min_clear`` times are
    NaN.

    Parameters
    ----------
    troi : Troi
        Uses ``bbox`` (degrees) and ``config`` (the cube's location).
    grid : TerrainGrid
        The terrain the features are laid on; must have the bbox's window shape.
    start, end : date
        The period, inclusive.
    min_clear : int, dimensionless
        Clear looks a cell needs for its statistics to count.

    Returns
    -------
    dict of str to ndarray
        ``low``, ``median``, ``high``: float32 (rows, cols), dimensionless
        NDVI; ``n_clear``: int16 (rows, cols), clear looks per cell.
    """
    cube = Cube(config=troi.config)
    ds = cube.get_ds(troi.bbox, start, end, indices=("NDVI",), bands=("nbart_red", "nbart_nir_1"))
    ndvi = np.asarray(ds["NDVI"].values, dtype=np.float32)
    if ndvi.ndim != 3 or ndvi.shape[1:] != grid.shape:
        raise ValueError(f"the cube's window {ndvi.shape[1:]} does not match the grid {grid.shape}")
    n_clear = np.isfinite(ndvi).sum(axis=0).astype(np.int16)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        low, median, high = (np.nanpercentile(ndvi, q, axis=0).astype(np.float32) for q in (10, 50, 90))
    few = n_clear < min_clear
    for arr in (low, median, high):
        arr[few] = np.nan
    return {"low": low, "median": median, "high": high, "n_clear": n_clear}


def _load_or_skip(troi: Troi, grid: TerrainGrid, start: date, end: date) -> dict[str, np.ndarray]:
    try:
        return load_ndvi_features(troi, grid, start, end)
    except (OSError, ConnectionError, TimeoutError) as err:
        raise SkipTest(f"Sentinel-2 cube unavailable: {err}") from err


def t():
    """The example region over a cached half year: statistics on the grid, ordered low <= median <= high, NDVI within
    its range, most cells seen clearly many times."""
    from troi_ingest.f.compute_window import compute_window
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    row0, row1, col0, col1 = compute_window(troi.bbox)
    grid = TerrainGrid(elevation=np.zeros((row1 - row0, col1 - col0)), cell_size=10.0)
    f = _load_or_skip(troi, grid, date(2022, 8, 2), date(2023, 1, 30))
    assert set(f) == {"low", "median", "high", "n_clear"} and all(f[k].shape == grid.shape for k in f)
    assert f["low"].dtype == np.float32 and f["n_clear"].dtype == np.int16
    known = np.isfinite(f["median"])
    assert known.mean() > 0.9, "a cleared half year should see nearly every cell"
    assert np.all(f["low"][known] <= f["median"][known]) and np.all(f["median"][known] <= f["high"][known])
    assert -0.5 < np.nanmin(f["low"]) and np.nanmax(f["high"]) <= 1.0
    assert f["n_clear"][known].min() >= 8 and f["n_clear"].max() > 15
    try:
        load_ndvi_features(troi, TerrainGrid(elevation=np.zeros((3, 3)), cell_size=10.0), date(2022, 8, 2), date(2023, 1, 30))
    except ValueError as err:
        assert "grid" in str(err)
    else:
        raise AssertionError("expected ValueError for a grid of the wrong shape")
