import numpy as np
import numpy.typing as npt


class RunResult:
    """What a model run produced.

    The history arrays may be in-memory NumPy arrays or on-disk zarr arrays;
    they are used only through indexing and are never copied here, so a run
    far larger than memory can still be held and read a day or a cell at a
    time.

    Parameters
    ----------
    dates : array_like of datetime64[D], dimensionless
        One entry per simulated day, length T.
    moisture_history : array-like, millimetres (mm)
        Shape (T, rows, cols). Store contents at the end of each day.
    flux_history : array-like or None, millimetres (mm)
        Shape (T, n_fluxes, rows, cols), or None when fluxes were not
        recorded. Which index on axis 1 is which flux is fixed by the step's
        IntEnum, for example ``BucketFlux``.

    Attributes
    ----------
    dates : ndarray (T,), datetime64[D]
    moisture_history : (T, rows, cols), mm
    flux_history : (T, n_fluxes, rows, cols) or None, mm
    n_days, n_fluxes : int, dimensionless
    shape : tuple[int, int], dimensionless
    """

    def __init__(self, dates: npt.ArrayLike, moisture_history, flux_history=None):
        dates_arr = np.asarray(dates, dtype="datetime64[D]")
        moisture = _as_array(moisture_history)
        fluxes = None if flux_history is None else _as_array(flux_history)
        if dates_arr.ndim != 1 or moisture.ndim != 3 or moisture.shape[0] != dates_arr.size:
            raise ValueError(f"need dates (T,) and moisture_history (T, rows, cols), got {dates_arr.shape} and {moisture.shape}")
        if fluxes is not None and (fluxes.ndim != 4 or fluxes.shape[0] != dates_arr.size or tuple(fluxes.shape[2:]) != tuple(moisture.shape[1:])):
            raise ValueError(f"flux_history must be (T, n_fluxes, rows, cols) matching moisture, got {fluxes.shape}")
        self.dates: np.ndarray = dates_arr
        self.moisture_history = moisture
        self.flux_history = fluxes

    @property
    def n_days(self) -> int:
        return self.dates.size

    @property
    def n_fluxes(self) -> int:
        return 0 if self.flux_history is None else self.flux_history.shape[1]

    @property
    def shape(self) -> tuple[int, int]:
        return tuple(self.moisture_history.shape[1:])

    def get_moisture(self, t: int) -> np.ndarray:
        """Store contents at the end of day t, mm, shape (rows, cols)."""
        return np.asarray(self.moisture_history[t])

    def get_fluxes(self, t: int) -> np.ndarray:
        """All fluxes on day t, mm, shape (n_fluxes, rows, cols)."""
        if self.flux_history is None:
            raise ValueError("fluxes were not recorded for this run")
        return np.asarray(self.flux_history[t])

    def get_flux_total(self, flux: int, block_days: int = 64) -> np.ndarray:
        """One flux summed over every day, mm, shape (rows, cols). Reads the history a block of days at a time."""
        if self.flux_history is None:
            raise ValueError("fluxes were not recorded for this run")
        total = np.zeros(self.shape, dtype=np.float64)
        for t0 in range(0, self.n_days, block_days):
            total += np.asarray(self.flux_history[t0 : t0 + block_days, flux]).sum(axis=0)
        return total


def _as_array(x):
    """Keep array-likes with shape, dtype and ndim (NumPy, zarr) as they are; convert anything else."""
    return x if hasattr(x, "shape") and hasattr(x, "dtype") and hasattr(x, "ndim") else np.asarray(x, dtype=np.float64)


def t1():
    """Holds the run and answers shape questions; totals sum over days, in blocks."""
    fluxes = np.ones((5, 3, 3, 4))
    fluxes[1, 2] = 5.0
    r = RunResult([f"2024-01-0{d}" for d in range(1, 6)], np.zeros((5, 3, 4)), fluxes)
    assert r.n_days == 5 and r.n_fluxes == 3 and r.shape == (3, 4)
    assert r.get_moisture(1).shape == (3, 4) and r.get_fluxes(1).shape == (3, 3, 4)
    assert np.all(r.get_flux_total(2) == 9.0) and np.all(r.get_flux_total(0, block_days=2) == 5.0)


def t2():
    """Arrays are held as given, not copied; a run without fluxes reports zero fluxes and refuses flux queries."""
    m = np.zeros((2, 3, 4))
    r = RunResult(["2024-01-01", "2024-01-02"], m)
    assert r.moisture_history is m and r.n_fluxes == 0 and r.flux_history is None
    for call in (lambda: r.get_fluxes(0), lambda: r.get_flux_total(0)):
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError without fluxes")


def t3():
    """Mismatched day counts, dimensions or grid shapes are rejected."""
    for dates, moisture, fluxes in (
        (["2024-01-01"], np.zeros((2, 3, 4)), np.zeros((2, 3, 3, 4))),
        (["2024-01-01"], np.zeros((3, 4)), np.zeros((1, 3, 3, 4))),
        (["2024-01-01"], np.zeros((1, 3, 4)), np.zeros((1, 3, 4))),
        (["2024-01-01"], np.zeros((1, 3, 4)), np.zeros((1, 3, 2, 2))),
        (["2024-01-01", "2024-01-02"], np.zeros((2, 3, 4)), np.zeros((1, 3, 3, 4))),
    ):
        try:
            RunResult(dates, moisture, fluxes)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def t():
    t1()
    t2()
    t3()
