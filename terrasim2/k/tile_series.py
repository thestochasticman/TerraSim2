import numpy as np
import numpy.typing as npt


class TileSeries:
    """One variable's daily values at a set of tiles.

    The data exactly as a coarse source gave it: one column per tile,
    one row per day. Which terrain cells read which column is a separate
    CellToTileMap, so the same series can be laid onto any grid.

    Parameters
    ----------
    name : str
        What the variable is, for example ``"rain"``.
    units : str
        Units of ``values``, for example ``"mm"``.
    dates : array_like of datetime64[D], dimensionless
        One entry per day, length T, strictly ascending.
    values : array_like, in ``units``
        Shape (T, n_tiles). NaN marks a missing value.

    Attributes
    ----------
    name, units : str
    dates : ndarray (T,), datetime64[D]
    values : ndarray (T, n_tiles), float64, in ``units``
    n_days, n_tiles : int, dimensionless
    """

    def __init__(self, name: str, units: str, dates: npt.ArrayLike, values: npt.ArrayLike):
        dates_arr = np.asarray(dates, dtype="datetime64[D]")
        values_arr = np.array(values, dtype=np.float64)
        if dates_arr.ndim != 1 or dates_arr.size == 0:
            raise ValueError(f"dates must be a non-empty 1-D array, got shape {dates_arr.shape}")
        if np.any(np.diff(dates_arr) <= np.timedelta64(0, "D")):
            raise ValueError("dates must be strictly ascending")
        if values_arr.ndim != 2 or values_arr.shape[0] != dates_arr.size:
            raise ValueError(f"values must have shape (T, n_tiles) with T={dates_arr.size}, got {values_arr.shape}")
        if values_arr.shape[1] == 0:
            raise ValueError("values must have at least one tile column")
        self.name = name
        self.units = units
        self.dates: np.ndarray = dates_arr
        self.values: np.ndarray = values_arr

    @property
    def n_days(self) -> int:
        return self.dates.size

    @property
    def n_tiles(self) -> int:
        return self.values.shape[1]


def t1():
    """Holds what it was given, as datetime64 days and float64 values."""
    s = TileSeries("rain", "mm", dates=["2024-01-01", "2024-01-02"], values=[[5, 20], [0, 1.5]])
    assert s.name == "rain" and s.units == "mm"
    assert s.n_days == 2 and s.n_tiles == 2
    assert s.dates.dtype == np.dtype("datetime64[D]")
    assert s.values.dtype == np.float64
    assert np.array_equal(s.values, [[5.0, 20.0], [0.0, 1.5]])


def t2():
    """Missing values are allowed as NaN."""
    s = TileSeries("rain", "mm", dates=["2024-01-01"], values=[[np.nan, 2.0]])
    assert np.isnan(s.values[0, 0]) and s.values[0, 1] == 2.0


def t3():
    """Empty, unordered or duplicated dates and mismatched values are rejected."""
    for bad in (
        dict(dates=[], values=np.zeros((0, 1))),
        dict(dates=["2024-01-02", "2024-01-01"], values=[[1.0], [2.0]]),
        dict(dates=["2024-01-01", "2024-01-01"], values=[[1.0], [2.0]]),
        dict(dates=["2024-01-01"], values=[[1.0], [2.0]]),
        dict(dates=["2024-01-01"], values=[1.0, 2.0]),
        dict(dates=["2024-01-01"], values=np.zeros((1, 0))),
    ):
        try:
            TileSeries("rain", "mm", **bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")


def t():
    t1()
    t2()
    t3()
