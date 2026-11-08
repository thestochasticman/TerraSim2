import numpy as np

from terrasim2.f.compute_water_content import compute_water_content
from terrasim2.k.run_result import RunResult
from terrasim2.k.site_observations import SiteObservations
from terrasim2.k.soil_hydraulics import SoilHydraulics


def pair_run_with_observations(
    result: RunResult,
    observations: SiteObservations,
    soil_hydraulics: SoilHydraulics,
    days_available: int | None = None,
    block_days: int = 64,
) -> np.ndarray:
    """What the run says at the cell and on the day of each observation.

    Each observation is matched to the run's day with its date and read at
    its cell as a volumetric water content over the root depth, by
    ``compute_water_content``. The run's history is read in blocks of
    days so a store on disk is decompressed once per block, not once per
    observation.

    Parameters
    ----------
    result : RunResult
        Its ``moisture_history`` may be a zarr array.
    observations : SiteObservations
        On the run's grid.
    soil_hydraulics : SoilHydraulics
        The run's soil, with a curve and the root depth.
    days_available : int, optional, dimensionless
        How many leading days of the history are safe to read, for a run
        still writing. All of them by default.
    block_days : int, dimensionless
        Days read from the history at a time.

    Returns
    -------
    ndarray (N,), m3 m-3
        The modelled content per observation; NaN where the observation's
        date is outside the run or not yet written, or its soil is unknown.
    """
    if observations.shape != result.shape:
        raise ValueError(f"observations on {observations.shape} do not sit on the run's grid {result.shape}")
    available = result.n_days if days_available is None else min(days_available, result.n_days)
    day = np.searchsorted(result.dates, observations.dates)
    found = (day < result.n_days) & (result.dates[np.minimum(day, result.n_days - 1)] == observations.dates) & (day < available)

    modelled = np.full(observations.n_points, np.nan)
    if not found.any():
        return modelled
    first, last = int(day[found].min()), int(day[found].max())
    for t0 in range(first, last + 1, block_days):
        t1 = min(t0 + block_days, last + 1)
        here = found & (day >= t0) & (day < t1)
        if not here.any():
            continue
        theta = compute_water_content(np.asarray(result.moisture_history[t0:t1]), soil_hydraulics)
        modelled[here] = theta[day[here] - t0, observations.row[here], observations.col[here]]
    return modelled


def _parts():
    from terrasim2.f.compute_water_content import _hydraulics

    dates = np.arange("2024-01-01", "2024-01-11", dtype="datetime64[D]")
    history = np.arange(10, dtype=float)[:, None, None] * np.ones((1, 2, 3)) * 3.0
    history[:, 1, 2] += 6.0
    result = RunResult(dates, history)
    obs = SiteObservations(
        shape=(2, 3),
        dates=["2024-01-01", "2024-01-05", "2024-01-05", "2024-01-10", "2023-12-31", "2024-01-11"],
        row=[0, 1, 1, 0, 0, 0],
        col=[0, 2, 0, 1, 0, 0],
        station=[0, 1, 2, 0, 0, 0],
        stations=["a", "b", "c"],
        depth_top=[0.0] * 6,
        depth_bottom=[0.3] * 6,
        vwc=[0.2] * 6,
    )
    return result, obs, _hydraulics()


def t1():
    """Each observation reads the run at its own day and cell as a content; dates outside the run are NaN;
    small blocks give the same answer as one block."""
    result, obs, h = _parts()
    modelled = pair_run_with_observations(result, obs, h)
    expected_mm = np.array([0.0, 4 * 3.0 + 6.0, 4 * 3.0, 9 * 3.0, np.nan, np.nan])
    assert np.allclose(modelled, 0.10 + expected_mm / 300.0, equal_nan=True), modelled
    assert np.allclose(pair_run_with_observations(result, obs, h, block_days=2), modelled, equal_nan=True)
    assert np.allclose(pair_run_with_observations(result, obs, h, block_days=1), modelled, equal_nan=True)


def t2():
    """Days beyond those available are NaN, observations on another grid are refused, and nothing available gives all NaN."""
    result, obs, h = _parts()
    partial = pair_run_with_observations(result, obs, h, days_available=5)
    assert np.isfinite(partial[0]) and np.isfinite(partial[1]) and np.isnan(partial[3])
    assert np.isnan(pair_run_with_observations(result, obs, h, days_available=0)).all()
    other = SiteObservations((3, 3), ["2024-01-01"], [0], [0], [0], ["a"], [0.0], [0.3], [0.2])
    try:
        pair_run_with_observations(result, other, h)
    except ValueError as err:
        assert "grid" in str(err)
    else:
        raise AssertionError("expected ValueError for observations on another grid")


def t():
    t1()
    t2()
