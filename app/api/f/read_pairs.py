from pathlib import Path

import numpy as np
import zarr

from terrasim2.f.load_model_inputs import load_model_inputs
from terrasim2.f.load_run_result import load_run_result
from terrasim2.f.load_site_observations import load_site_observations
from terrasim2.f.pair_run_with_observations import pair_run_with_observations

# The columns of the byte layout, in order.
PAIR_COLUMNS = ("t", "row", "col", "station", "observed", "modelled")


def read_pairs(inputs_folder: Path, observations_folder: Path, store_folder: Path, root_depth: float) -> bytes:
    """Every observation with the run's value at it, as little-endian float32 columns.

    The layout is ``PAIR_COLUMNS`` one after another, each of length N, so
    a reader splits the bytes into six equal runs: the run's day index
    (NaN when the date is outside the run or not yet written), the cell's
    row and column, the station index, the observed content and the
    modelled content (NaN when unavailable), contents in m3 m-3.

    Parameters
    ----------
    inputs_folder, observations_folder, store_folder : Path
        As for ``read_comparison``.
    root_depth : float, m

    Returns
    -------
    bytes
        ``6 * N * 4`` bytes.
    """
    inputs = load_model_inputs(inputs_folder)
    if inputs.soil is None:
        raise ValueError(f"model inputs at {inputs_folder} carry no soil, so a run cannot be read as a water content")
    hydraulics = inputs.soil.compute_hydraulics(root_depth)
    observations = load_site_observations(observations_folder)
    group = zarr.open_group(Path(store_folder), mode="r")
    written = int(group.attrs.get("days_written", 0))
    result = load_run_result(store_folder, allow_incomplete=True)
    modelled = pair_run_with_observations(result, observations, hydraulics, days_available=written)

    day = np.searchsorted(result.dates, observations.dates).astype(np.float64)
    day[~np.isfinite(modelled)] = np.nan
    columns = np.stack([day, observations.row, observations.col, observations.station, observations.vwc, modelled]).astype("<f4")
    return columns.tobytes(order="C")


def t():
    """The bytes split into six columns of one length; day indices and cells decode exactly; the modelled column
    matches the comparison's pairing."""
    import tempfile

    from app.api.f.execute_run import execute_run
    from app.api.f.find_inputs import find_inputs
    from app.api.f.find_observations import find_observations
    from app.api.k.run_request import RunRequest

    inputs_folder = find_inputs("tarrawarra")
    store = execute_run(RunRequest(stub="tarrawarra", write_every_days=64, record_fluxes=False), inputs_folder, Path(tempfile.mkdtemp()) / "store.zarr")
    raw = read_pairs(inputs_folder, find_observations("tarrawarra"), store, 0.3)
    n = len(raw) // (4 * len(PAIR_COLUMNS))
    assert n == 8644 and len(raw) == 6 * n * 4
    columns = np.frombuffer(raw, dtype="<f4").reshape(len(PAIR_COLUMNS), n)
    observations = load_site_observations(find_observations("tarrawarra"))
    assert np.array_equal(columns[1], observations.row) and np.array_equal(columns[2], observations.col) and np.array_equal(columns[3], observations.station)
    assert columns[0][0] == 0 and columns[0][-1] == 431 and np.isfinite(columns[0]).all()
    assert np.allclose(columns[4], observations.vwc, atol=1e-6) and np.isfinite(columns[5]).all()
    assert 0 < columns[5].mean() < columns[4].mean()
