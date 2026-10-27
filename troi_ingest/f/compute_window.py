import math

from pysentinel2 import grid as s2


def compute_window(bbox: list[float]) -> tuple[int, int, int, int]:
    """Pixel window on the Sentinel-2 grid that fits a bbox.

    The bbox corners are projected to EPSG:6933 and snapped outward to
    the nearest 10 m pixel edges, so every cell of the window is exactly
    one Sentinel-2 pixel and the window is the smallest such set that
    covers the bbox. Unlike pysentinel2's own window, this is not snapped
    to 256-pixel chunks.

    Parameters
    ----------
    bbox : list of float, degrees
        ``[west, south, east, north]`` in EPSG:4326.

    Returns
    -------
    tuple of int, dimensionless
        ``(row0, row1, col0, col1)``, half-open, on the global grid.
        Rows increase southward from the grid's top edge.
    """
    west, south, east, north = bbox
    if not (west < east and south < north):
        raise ValueError(f"bbox must satisfy west < east and south < north, got {bbox}")
    x0, y0, x1, y1 = s2.bbox_to_6933(bbox)
    col0 = math.floor((x0 - s2.X0) / s2.RES)
    col1 = math.ceil((x1 - s2.X0) / s2.RES)
    row0 = math.floor((s2.Y_TOP - y1) / s2.RES)
    row1 = math.ceil((s2.Y_TOP - y0) / s2.RES)
    return (row0, row1, col0, col1)


_BBOX = [148.36265, -33.52606, 148.38265, -33.50606]


def t1():
    """The window contains the bbox with less than one pixel of slack per edge."""
    row0, row1, col0, col1 = compute_window(_BBOX)
    x0, y0, x1, y1 = s2.bbox_to_6933(_BBOX)
    left, right = s2.X0 + col0 * s2.RES, s2.X0 + col1 * s2.RES
    top, bottom = s2.Y_TOP - row0 * s2.RES, s2.Y_TOP - row1 * s2.RES
    assert left <= x0 < left + s2.RES
    assert right - s2.RES < x1 <= right
    assert top - s2.RES < y1 <= top
    assert bottom <= y0 < bottom + s2.RES


def t2():
    """A ~2 km bbox at -33.5 degrees is roughly 190 x 230 cells, and the window is inside pysentinel2's chunk window."""
    row0, row1, col0, col1 = compute_window(_BBOX)
    assert 150 < col1 - col0 < 260, (col1 - col0)
    assert 150 < row1 - row0 < 260, (row1 - row0)
    c_row0, c_row1, c_col0, c_col1 = s2.window_for_bbox(_BBOX)
    assert c_row0 <= row0 < row1 <= c_row1
    assert c_col0 <= col0 < col1 <= c_col1


def t3():
    """Shifting the bbox east by exactly one pixel shifts the window by one column."""
    import pyproj

    to_4326 = pyproj.Transformer.from_crs(s2.CRS, "EPSG:4326", always_xy=True)
    x0, y0, x1, y1 = s2.bbox_to_6933(_BBOX)
    west, south = to_4326.transform(x0 + s2.RES, y0)
    east, north = to_4326.transform(x1 + s2.RES, y1)
    a = compute_window(_BBOX)
    b = compute_window([west, south, east, north])
    assert b[2] - a[2] == 1 and b[3] - a[3] == 1, (a, b)
    assert b[0] == a[0] and b[1] == a[1]


def t4():
    """A degenerate bbox is rejected."""
    for bad in ([148.4, -33.5, 148.3, -33.4], [148.3, -33.4, 148.4, -33.5]):
        try:
            compute_window(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")


def t():
    t1()
    t2()
    t3()
    t4()
