from unittest import SkipTest

import numpy as np
import rioxarray  # noqa: F401  (registers the .rio accessor on xarray objects)
from affine import Affine
from pycopdem.store import Store
from pysentinel2 import grid as s2
from rasterio.enums import Resampling
from troi import Troi

from troi_ingest.f.compute_window import compute_window


def load_elevation(troi: Troi) -> np.ndarray:
    """Elevation on the Sentinel-2 window that fits a Troi's bbox.

    Reads the Copernicus GLO-30 DEM from the lab store located by the
    Troi's config (downloading any missing chunks on first use), then
    reprojects it from its native 1 arc-second lat/lon lattice onto the
    10 m EPSG:6933 window with bilinear resampling.

    Parameters
    ----------
    troi : Troi
        Uses ``bbox`` (degrees, EPSG:4326) and ``config`` (store location).
        Dates are ignored; elevation does not change.

    Returns
    -------
    ndarray, metres (m)
        float64 of shape ``(rows, cols)`` for ``compute_window(troi.bbox)``,
        row 0 at the north edge. NaN where the DEM has no data.
    """
    row0, row1, col0, col1 = compute_window(troi.bbox)
    rows, cols = row1 - row0, col1 - col0
    transform = Affine(s2.RES, 0, s2.X0 + col0 * s2.RES, 0, -s2.RES, s2.Y_TOP - row0 * s2.RES)

    source = Store(config=troi.config).get_ds(troi.bbox)["elevation"]
    source = source.rio.set_spatial_dims(x_dim="lon", y_dim="lat").rio.write_crs("EPSG:4326")
    target = source.rio.reproject(
        s2.CRS,
        transform=transform,
        shape=(rows, cols),
        resampling=Resampling.bilinear,
        nodata=np.nan,
    )
    return target.values.astype(np.float64)


def _load_or_skip(troi: Troi) -> np.ndarray:
    try:
        return load_elevation(troi)
    except (OSError, ConnectionError, TimeoutError) as err:
        raise SkipTest(f"DEM store unavailable: {err}") from err


def t1():
    """Shape matches the window and values are plausible for the test region."""
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    row0, row1, col0, col1 = compute_window(troi.bbox)
    elev = _load_or_skip(troi)
    assert elev.shape == (row1 - row0, col1 - col0), elev.shape
    assert elev.dtype == np.float64
    assert np.isfinite(elev).all(), "expected full DEM coverage over land"
    assert 100 < elev.min() < elev.max() < 1500, (elev.min(), elev.max())


def t2():
    """Neighbouring cells differ by at most a few metres: resampling produced a continuous surface."""
    from troi_ingest.f.make_test_troi import make_test_troi

    elev = _load_or_skip(make_test_troi())
    assert np.abs(np.diff(elev, axis=0)).max() < 20
    assert np.abs(np.diff(elev, axis=1)).max() < 20


def t3():
    """A bbox one pixel east gives a window whose first column equals the original's second column."""
    import pyproj

    from troi_ingest.f.make_test_troi import make_test_troi

    base = make_test_troi("shift_base")
    to_4326 = pyproj.Transformer.from_crs(s2.CRS, "EPSG:4326", always_xy=True)
    x0, y0, x1, y1 = s2.bbox_to_6933(base.bbox)
    west, south = to_4326.transform(x0 + s2.RES, y0)
    east, north = to_4326.transform(x1 + s2.RES, y1)
    shifted = Troi(bbox=[west, south, east, north], start=base.start, end=base.end, stub="shift_east", config=base.config)
    a = _load_or_skip(base)
    b = _load_or_skip(shifted)
    assert np.allclose(a[:, 1:], b[:, :-1], atol=1e-3)


def t():
    t1()
    t2()
    t3()
