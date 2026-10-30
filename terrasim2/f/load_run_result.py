from pathlib import Path

import zarr

from terrasim2.f.create_run_store import RUN_STORE_VERSION
from terrasim2.k.run_result import RunResult


def load_run_result(folder: Path, allow_incomplete: bool = False) -> RunResult:
    """Open a run store read-only as a RunResult backed by its zarr arrays.

    Nothing is read into memory until indexed. A store whose run did not
    finish is refused unless ``allow_incomplete`` is set; its unfilled days
    are NaN.

    Parameters
    ----------
    folder : Path
        A group written by ``create_run_store`` and ``write_run_block``.
    allow_incomplete : bool
        Open a store whose ``complete`` attribute is False.

    Returns
    -------
    RunResult
    """
    group = zarr.open_group(Path(folder), mode="r")
    version = group.attrs.get("version")
    if version != RUN_STORE_VERSION:
        raise ValueError(f"run store at {folder} is version {version}; this reader needs {RUN_STORE_VERSION}")
    if not group.attrs.get("complete", False) and not allow_incomplete:
        raise ValueError(f"run store at {folder} is incomplete: the run did not finish")
    fluxes = group["fluxes"] if "fluxes" in group else None
    return RunResult(group.attrs["dates"], group["moisture"], fluxes)


def t1():
    """An incomplete store is refused by default and opened on request with NaN where nothing was written."""
    import tempfile

    import numpy as np

    from terrasim2.f.create_run_store import create_run_store
    from terrasim2.f.run_model import _inputs
    from terrasim2.f.write_run_block import write_run_block
    from terrasim2.k.run_store_params import RunStoreParams

    folder = Path(tempfile.mkdtemp()) / "run.zarr"
    g = create_run_store(_inputs(), 1, folder, RunStoreParams())
    write_run_block(g, 0, np.full((1, 2, 3), 7.0), np.full((1, 1, 2, 3), 1.0))
    try:
        load_run_result(folder)
    except ValueError as err:
        assert "incomplete" in str(err)
    else:
        raise AssertionError("expected ValueError for an incomplete store")
    r = load_run_result(folder, allow_incomplete=True)
    assert r.n_days == 3 and np.all(r.get_moisture(0) == 7.0) and np.isnan(r.get_moisture(1)).all()


def t2():
    """A completed store opens, is read-only, and answers through the RunResult interface."""
    import tempfile

    import numpy as np

    from terrasim2.f.create_run_store import create_run_store
    from terrasim2.f.run_model import _inputs
    from terrasim2.f.write_run_block import write_run_block
    from terrasim2.k.run_store_params import RunStoreParams

    folder = Path(tempfile.mkdtemp()) / "run.zarr"
    g = create_run_store(_inputs(), 2, folder, RunStoreParams(chunk_days=2))
    write_run_block(g, 0, np.full((3, 2, 3), 1.0), np.full((3, 2, 2, 3), 2.0))
    g.attrs["complete"] = True
    r = load_run_result(folder)
    assert r.n_days == 3 and r.n_fluxes == 2 and r.shape == (2, 3)
    assert r.dates[2] == np.datetime64("2024-01-03")
    assert np.all(r.get_flux_total(1) == 6.0)
    try:
        r.moisture_history[0] = 0.0
    except Exception:
        pass
    else:
        raise AssertionError("expected the loaded store to be read-only")


def t():
    t1()
    t2()
