import numpy as np
import pyproj
from pysentinel2 import grid as s2
from pysilo import grid as silo

from troi_ingest.f.compute_window import compute_window


def compute_silo_tiles(bbox: list[float]) -> tuple[np.ndarray, list[tuple[float, float]]]:
    """Which SILO point each cell of a bbox's Sentinel-2 window belongs to.

    Each cell centre is transformed to lat/lon and snapped to the nearest
    point on SILO's 0.05 degree lattice using pysilo's own rule. EPSG:6933
    is cylindrical, so latitude depends only on the row and longitude only
    on the column; the snap is done once per row and once per column.

    Parameters
    ----------
    bbox : list of float, degrees
        ``[west, south, east, north]`` in EPSG:4326.

    Returns
    -------
    tile_index : ndarray, dimensionless
        int, shape ``(rows, cols)`` for ``compute_window(bbox)``. Index into
        ``points`` for each cell.
    points : list of (lat, lon), degrees
        The distinct SILO points, sorted by (lat, lon). ``len(points)`` is
        the number of tiles.
    """
    row0, row1, col0, col1 = compute_window(bbox)
    x = s2.X0 + (np.arange(col0, col1) + 0.5) * s2.RES
    y = s2.Y_TOP - (np.arange(row0, row1) + 0.5) * s2.RES

    to_4326 = pyproj.Transformer.from_crs(s2.CRS, "EPSG:4326", always_xy=True)
    lon, _ = to_4326.transform(x, np.full_like(x, y[0]))
    _, lat = to_4326.transform(np.full_like(y, x[0]), y)

    lat_snapped = np.round([silo.snap(v, 0.0)[0] for v in lat], 6)
    lon_snapped = np.round([silo.snap(0.0, v)[1] for v in lon], 6)

    pairs = np.stack(np.meshgrid(lat_snapped, lon_snapped, indexing="ij"), axis=-1).reshape(-1, 2)
    unique, inverse = np.unique(pairs, axis=0, return_inverse=True)
    tile_index = inverse.reshape(len(lat_snapped), len(lon_snapped)).astype(np.intp)
    points = [(float(p[0]), float(p[1])) for p in unique]
    return tile_index, points


_BBOX = [148.36265, -33.52606, 148.38265, -33.50606]


def t1():
    """Shape matches the window, indices cover every point, points sit on the 0.05 degree lattice."""
    row0, row1, col0, col1 = compute_window(_BBOX)
    tile_index, points = compute_silo_tiles(_BBOX)
    assert tile_index.shape == (row1 - row0, col1 - col0)
    assert 1 <= len(points) <= 4, points
    assert set(np.unique(tile_index)) == set(range(len(points)))
    for lat, lon in points:
        assert abs(lat / 0.05 - round(lat / 0.05)) < 1e-6 and abs(lon / 0.05 - round(lon / 0.05)) < 1e-6, (lat, lon)


def t2():
    """Tiles are rectangles aligned to rows and columns: each row and each column reads a fixed set of points."""
    tile_index, points = compute_silo_tiles(_BBOX)
    for r in range(tile_index.shape[0]):
        row = tile_index[r]
        changes = np.flatnonzero(np.diff(row))
        assert len(changes) <= 1, "a row crosses at most one longitude boundary"
    for c in range(tile_index.shape[1]):
        col = tile_index[:, c]
        changes = np.flatnonzero(np.diff(col))
        assert len(changes) <= 1, "a column crosses at most one latitude boundary"


def t3():
    """A bbox well inside one SILO cell gives exactly one tile; one straddling a boundary gives two."""
    one, pts1 = compute_silo_tiles([148.3651, -33.5249, 148.3749, -33.5151])
    assert len(pts1) == 1 and np.all(one == 0)
    two, pts2 = compute_silo_tiles([148.3701, -33.5249, 148.3799, -33.5151])
    assert len(pts2) == 2 and np.all(two[:, 0] == two[0, 0]) and np.all(two[:, -1] == two[0, -1])
    assert two[0, 0] != two[0, -1]


def t():
    t1()
    t2()
    t3()
