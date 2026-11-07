import numpy as np
import pyproj
from pysentinel2 import grid as s2

from troi_ingest.f.compute_window import compute_window


def locate_points_on_window(lon: np.ndarray, lat: np.ndarray, bbox: list[float]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Which cell of a bbox's Sentinel-2 window each point falls in.

    Points are projected to EPSG:6933 and floored to the 10 m pixel they
    lie in, then expressed relative to ``compute_window(bbox)``, so the
    result indexes a ``TerrainGrid`` built for the same bbox.

    Parameters
    ----------
    lon, lat : array_like, degrees
        EPSG:4326, any shape, broadcast together.
    bbox : list of float, degrees
        ``[west, south, east, north]`` in EPSG:4326.

    Returns
    -------
    row, col : ndarray of int, dimensionless
        Relative to the window; outside it they fall below 0 or beyond
        the window's shape.
    inside : ndarray of bool
        Whether each point lies within the window.
    """
    row0, row1, col0, col1 = compute_window(bbox)
    to_6933 = pyproj.Transformer.from_crs("EPSG:4326", s2.CRS, always_xy=True)
    x, y = to_6933.transform(np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))
    col = np.floor((np.asarray(x) - s2.X0) / s2.RES).astype(np.int64) - col0
    row = np.floor((s2.Y_TOP - np.asarray(y)) / s2.RES).astype(np.int64) - row0
    inside = (row >= 0) & (row < row1 - row0) & (col >= 0) & (col < col1 - col0)
    return row, col, inside


_BBOX = [148.36265, -33.52606, 148.38265, -33.50606]


def t1():
    """The bbox's corners land in the window's corner cells, its centre near the middle, and a point a kilometre
    outside is flagged, with rows growing southward and columns eastward."""
    west, south, east, north = _BBOX
    row0, row1, col0, col1 = compute_window(_BBOX)
    rows, cols = row1 - row0, col1 - col0
    row, col, inside = locate_points_on_window([west, east, west, east, (west + east) / 2, west - 0.01], [north, north, south, south, (south + north) / 2, north], _BBOX)
    assert inside.tolist() == [True, True, True, True, True, False]
    assert (row[0], col[0]) == (0, 0), "north-west corner is the first cell"
    assert row[1] == 0 and col[1] == cols - 1, "north-east corner is the last column"
    assert row[2] == rows - 1 and col[2] == 0, "south-west corner is the last row"
    assert abs(row[4] - rows / 2) <= 1 and abs(col[4] - cols / 2) <= 1
    assert col[5] < 0


def t2():
    """Shifting a point by one pixel moves it by one cell; shapes are preserved."""
    import pyproj as pp

    to_4326 = pp.Transformer.from_crs(s2.CRS, "EPSG:4326", always_xy=True)
    to_6933 = pp.Transformer.from_crs("EPSG:4326", s2.CRS, always_xy=True)
    x, y = to_6933.transform(148.37, -33.515)
    lon2, lat2 = to_4326.transform(x + s2.RES, y - s2.RES)
    row, col, inside = locate_points_on_window(np.array([[148.37, lon2]]), np.array([[-33.515, lat2]]), _BBOX)
    assert row.shape == (1, 2) and inside.all()
    assert col[0, 1] - col[0, 0] == 1 and row[0, 1] - row[0, 0] == 1


def t():
    t1()
    t2()
