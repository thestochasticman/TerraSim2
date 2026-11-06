import numpy as np
import numpy.typing as npt


class SiteObservations:
    """Point measurements of soil water content, laid on a terrain grid's cells.

    What a validation site measured, as the model can meet it: each
    observation is a volumetric water content over a depth interval, on a
    date, at a cell of the grid, from a named station. Several readings of
    one station on one day may have been averaged into one observation;
    ``n`` says how many. Built by ``troi_ingest`` from the lab's observation
    files, or read from disk by ``load_site_observations``; written by
    ``write_site_observations``.

    Parameters
    ----------
    shape : tuple[int, int], dimensionless
        ``(rows, cols)`` of the grid the cells index.
    dates : array_like of datetime64[D], dimensionless
        When each observation was taken, length N.
    row, col : array_like of int, dimensionless
        The cell of each observation, within ``shape``.
    station : array_like of int, dimensionless
        Index into ``stations`` per observation.
    stations : list of str
        The distinct station names.
    depth_top, depth_bottom : array_like, m
        The interval each observation represents, ``0 <= top < bottom``.
    vwc : array_like, m3 m-3
        Volumetric water content, finite and within [0, 1].
    n : array_like of int, dimensionless, optional
        Readings averaged into each observation, positive. Ones by default.
    meta : dict, optional
        Free-form provenance (stub, source file, what was dropped).

    Attributes
    ----------
    shape : tuple[int, int]
    dates : ndarray (N,), datetime64[D]
    row, col, station, n : ndarray (N,), int
    stations : list of str
    depth_top, depth_bottom, vwc : ndarray (N,), float64
    meta : dict
    n_points, n_stations : int, dimensionless
    survey_dates : ndarray, datetime64[D], the distinct dates in order
    """

    FORMAT_VERSION = 1

    def __init__(
        self,
        shape: tuple[int, int],
        dates: npt.ArrayLike,
        row: npt.ArrayLike,
        col: npt.ArrayLike,
        station: npt.ArrayLike,
        stations: list[str],
        depth_top: npt.ArrayLike,
        depth_bottom: npt.ArrayLike,
        vwc: npt.ArrayLike,
        n: npt.ArrayLike | None = None,
        meta: dict | None = None,
    ):
        rows, cols = (int(v) for v in shape)
        if rows <= 0 or cols <= 0:
            raise ValueError(f"shape must be positive, got {shape}")
        self.shape = (rows, cols)
        self.dates = np.asarray(dates, dtype="datetime64[D]")
        count = self.dates.size
        if self.dates.ndim != 1 or count == 0:
            raise ValueError("dates must be a non-empty 1-D array")
        self.row = _column(row, count, "row", int)
        self.col = _column(col, count, "col", int)
        self.station = _column(station, count, "station", int)
        self.depth_top = _column(depth_top, count, "depth_top", float)
        self.depth_bottom = _column(depth_bottom, count, "depth_bottom", float)
        self.vwc = _column(vwc, count, "vwc", float)
        self.n = np.ones(count, dtype=np.int64) if n is None else _column(n, count, "n", int)
        self.stations = [str(s) for s in stations]
        self.meta: dict = dict(meta or {})

        if np.any(self.row < 0) or np.any(self.row >= rows) or np.any(self.col < 0) or np.any(self.col >= cols):
            raise ValueError(f"every row and col must lie within the grid shape {self.shape}")
        if np.any(self.station < 0) or np.any(self.station >= len(self.stations)):
            raise ValueError(f"station indices must index the {len(self.stations)} station names")
        if np.any(self.depth_top < 0) or np.any(self.depth_bottom <= self.depth_top):
            raise ValueError("depths must satisfy 0 <= depth_top < depth_bottom")
        if not np.isfinite(self.vwc).all() or np.any(self.vwc < 0) or np.any(self.vwc > 1):
            raise ValueError("vwc must be finite and within [0, 1]")
        if np.any(self.n <= 0):
            raise ValueError("n must be positive")

    @property
    def n_points(self) -> int:
        return self.dates.size

    @property
    def n_stations(self) -> int:
        return len(self.stations)

    @property
    def survey_dates(self) -> np.ndarray:
        return np.unique(self.dates)

    def select_day(self, date) -> np.ndarray:
        """Indices of the observations taken on a date, in stored order."""
        return np.flatnonzero(self.dates == np.datetime64(date, "D"))

    def select_layer(self, depth_top: float, depth_bottom: float) -> np.ndarray:
        """Indices of the observations over exactly this depth interval, m."""
        return np.flatnonzero(np.isclose(self.depth_top, depth_top) & np.isclose(self.depth_bottom, depth_bottom))


def _column(values: npt.ArrayLike, count: int, name: str, kind: type) -> np.ndarray:
    arr = np.asarray(values, dtype=np.int64 if kind is int else np.float64)
    if arr.shape != (count,):
        raise ValueError(f"{name} must have shape ({count},), got {arr.shape}")
    return arr


def _example() -> SiteObservations:
    return SiteObservations(
        shape=(3, 4),
        dates=["2024-01-02", "2024-01-02", "2024-01-05"],
        row=[0, 2, 0],
        col=[1, 3, 1],
        station=[0, 1, 0],
        stations=["a", "b"],
        depth_top=[0.0, 0.0, 0.0],
        depth_bottom=[0.3, 0.3, 0.3],
        vwc=[0.25, 0.31, 0.2],
        n=[1, 3, 1],
        meta={"stub": "unit"},
    )


def t1():
    """Holds what it was given with the declared dtypes, counts points and stations, and lists survey dates."""
    obs = _example()
    assert obs.n_points == 3 and obs.n_stations == 2 and obs.shape == (3, 4)
    assert obs.dates.dtype == np.dtype("datetime64[D]") and obs.row.dtype == np.int64 and obs.vwc.dtype == np.float64
    assert np.array_equal(obs.survey_dates, np.array(["2024-01-02", "2024-01-05"], dtype="datetime64[D]"))
    assert np.array_equal(obs.select_day("2024-01-02"), [0, 1]) and np.array_equal(obs.select_day("2024-01-03"), [])
    assert np.array_equal(obs.select_layer(0.0, 0.3), [0, 1, 2]) and obs.select_layer(0.3, 0.6).size == 0
    assert obs.meta == {"stub": "unit"} and obs.n[1] == 3
    bare = SiteObservations((1, 1), ["2024-01-01"], [0], [0], [0], ["s"], [0.0], [0.1], [0.5])
    assert bare.n.tolist() == [1] and bare.meta == {}


def t2():
    """A cell outside the grid, a station index past the names, a bad depth interval, a vwc outside [0, 1],
    a non-positive n and a length mismatch are each refused."""
    good = dict(shape=(3, 4), dates=["2024-01-02"], row=[0], col=[1], station=[0], stations=["a"], depth_top=[0.0], depth_bottom=[0.3], vwc=[0.25])
    for bad in (
        dict(row=[3]),
        dict(col=[-1]),
        dict(station=[1]),
        dict(depth_top=[0.3]),
        dict(depth_top=[-0.1]),
        dict(vwc=[1.5]),
        dict(vwc=[np.nan]),
        dict(n=[0]),
        dict(vwc=[0.2, 0.3]),
        dict(dates=[]),
    ):
        try:
            SiteObservations(**{**good, **bad})
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")


def t():
    t1()
    t2()
