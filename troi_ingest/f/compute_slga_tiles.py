import numpy as np
import pyproj
from pysentinel2 import grid as s2

from troi_ingest.f.compute_window import compute_window


def compute_slga_tiles(bbox: list[float], lat_axis: np.ndarray, lon_axis: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Which SLGA pixel each cell of a bbox's Sentinel-2 window reads.

    Each cell centre is transformed to lat/lon and matched to the nearest
    coordinate on each axis of an SLGA window. EPSG:6933 is cylindrical,
    so latitude depends only on the row and longitude only on the column.

    Parameters
    ----------
    bbox : list of float, degrees
        ``[west, south, east, north]`` in EPSG:4326.
    lat_axis, lon_axis : ndarray, degrees
        The coordinate axes of the SLGA window that covers the bbox, as
        pyslga returns them (latitude descending, longitude ascending).

    Returns
    -------
    tile_index : ndarray, dimensionless
        int, shape ``(rows, cols)`` for ``compute_window(bbox)``; index into
        ``pixels`` for each cell.
    pixels : ndarray, dimensionless
        int, shape ``(n_tiles, 2)``: the ``(lat_index, lon_index)`` into the
        axes of each distinct pixel, sorted.
    """
    row0, row1, col0, col1 = compute_window(bbox)
    x = s2.X0 + (np.arange(col0, col1) + 0.5) * s2.RES
    y = s2.Y_TOP - (np.arange(row0, row1) + 0.5) * s2.RES
    to_4326 = pyproj.Transformer.from_crs(s2.CRS, "EPSG:4326", always_xy=True)
    lon, _ = to_4326.transform(x, np.full_like(x, y[0]))
    _, lat = to_4326.transform(np.full_like(y, x[0]), y)

    lat_axis = np.asarray(lat_axis, dtype=np.float64)
    lon_axis = np.asarray(lon_axis, dtype=np.float64)
    lat_i = np.abs(lat_axis[None, :] - lat[:, None]).argmin(axis=1)
    lon_i = np.abs(lon_axis[None, :] - lon[:, None]).argmin(axis=1)

    pairs = np.stack(np.meshgrid(lat_i, lon_i, indexing="ij"), axis=-1).reshape(-1, 2)
    pixels, inverse = np.unique(pairs, axis=0, return_inverse=True)
    return inverse.reshape(len(lat_i), len(lon_i)).astype(np.intp), pixels


_BBOX = [148.36265, -33.52606, 148.38265, -33.50606]


def _axes(step: float = 1 / 1200) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic SLGA axes over one degree, as pyslga lays them out."""
    return -33.0 - np.arange(1200) * step, 148.0 + np.arange(1200) * step


def t1():
    """Shape matches the window, every tile is used, and the example bbox spans a few dozen 90 m pixels each way."""
    row0, row1, col0, col1 = compute_window(_BBOX)
    lat_axis, lon_axis = _axes()
    tile_index, pixels = compute_slga_tiles(_BBOX, lat_axis, lon_axis)
    assert tile_index.shape == (row1 - row0, col1 - col0)
    assert set(np.unique(tile_index)) == set(range(len(pixels)))
    assert 15 <= len(np.unique(pixels[:, 0])) <= 40 and 15 <= len(np.unique(pixels[:, 1])) <= 40, pixels.shape
    assert len(pixels) == len(np.unique(pixels[:, 0])) * len(np.unique(pixels[:, 1]))


def t2():
    """Tiles are rectangles: along a row the pixel changes only as longitude crosses a pixel edge, and
    roughly every nine 10 m cells, which is a 90 m pixel."""
    tile_index, pixels = compute_slga_tiles(_BBOX, *_axes())
    row = tile_index[0]
    runs = np.diff(np.flatnonzero(np.diff(row)))
    assert 7 <= np.median(runs) <= 10, np.median(runs)
    col = tile_index[:, 0]
    assert np.all(np.diff(col) >= 0) or np.all(np.diff(col) <= 0)
    assert np.all(pixels[:, 0] >= 0) and np.all(pixels[:, 1] < 1200)


def t():
    t1()
    t2()
