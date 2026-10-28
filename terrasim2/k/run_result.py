import numpy as np
import numpy.typing as npt


class RunResult:
    """What a model run produced.

    Parameters
    ----------
    dates : array_like of datetime64[D], dimensionless
        One entry per simulated day, length T.
    moisture_history : array_like, millimetres (mm)
        Shape (T, rows, cols). Store contents at the end of each day.
    flux_history : array_like, millimetres (mm)
        Shape (T, n_fluxes, rows, cols). What moved each day. Which index on
        axis 1 is which flux is fixed by the step's IntEnum, for example
        ``BucketFlux``; ``flux_history[:, BucketFlux.RUNOFF]`` is daily runoff.

    Attributes
    ----------
    dates : ndarray (T,), datetime64[D]
    moisture_history : ndarray (T, rows, cols), mm
    flux_history : ndarray (T, n_fluxes, rows, cols), mm
    n_days, n_fluxes : int, dimensionless
    shape : tuple[int, int], dimensionless
    """

    def __init__(self, dates: npt.ArrayLike, moisture_history: npt.ArrayLike, flux_history: npt.ArrayLike):
        dates_arr = np.asarray(dates, dtype="datetime64[D]")
        moisture = np.array(moisture_history, dtype=np.float64)
        fluxes = np.array(flux_history, dtype=np.float64)
        if dates_arr.ndim != 1 or moisture.ndim != 3 or moisture.shape[0] != dates_arr.size:
            raise ValueError(f"need dates (T,) and moisture_history (T, rows, cols), got {dates_arr.shape} and {moisture.shape}")
        if fluxes.ndim != 4 or fluxes.shape[0] != dates_arr.size or fluxes.shape[2:] != moisture.shape[1:]:
            raise ValueError(f"flux_history must be (T, n_fluxes, rows, cols) matching moisture, got {fluxes.shape}")
        self.dates: np.ndarray = dates_arr
        self.moisture_history: np.ndarray = moisture
        self.flux_history: np.ndarray = fluxes

    @property
    def n_days(self) -> int:
        return self.dates.size

    @property
    def n_fluxes(self) -> int:
        return self.flux_history.shape[1]

    @property
    def shape(self) -> tuple[int, int]:
        return self.moisture_history.shape[1:]

    def get_moisture(self, t: int) -> np.ndarray:
        """Store contents at the end of day t, mm, shape (rows, cols)."""
        return self.moisture_history[t]

    def get_flux_total(self, flux: int) -> np.ndarray:
        """One flux summed over every day, mm, shape (rows, cols)."""
        return self.flux_history[:, flux].sum(axis=0)


def t1():
    """Holds the run and answers shape questions; totals sum over days."""
    fluxes = np.ones((2, 3, 3, 4))
    fluxes[1, 2] = 5.0
    r = RunResult(["2024-01-01", "2024-01-02"], np.zeros((2, 3, 4)), fluxes)
    assert r.n_days == 2 and r.n_fluxes == 3 and r.shape == (3, 4)
    assert r.get_moisture(1).shape == (3, 4)
    assert np.all(r.get_flux_total(2) == 6.0) and np.all(r.get_flux_total(0) == 2.0)


def t2():
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
