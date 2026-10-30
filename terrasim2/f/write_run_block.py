import numpy as np
import zarr


def write_run_block(group: zarr.Group, t0: int, moisture_block: np.ndarray, flux_block: np.ndarray | None) -> None:
    """Write a block of consecutive days into a run store.

    After the arrays are written the group's ``days_written`` attribute is
    set to ``t0 + n``, so a reader that opens the store while the run is
    still going knows how many leading days are safe to read.

    Parameters
    ----------
    group : zarr.Group
        From ``create_run_store``, open for writing.
    t0 : int, dimensionless
        Day index of the block's first day.
    moisture_block : ndarray, millimetres (mm)
        Shape (n, rows, cols) for days t0 to t0 + n - 1.
    flux_block : ndarray or None, millimetres (mm)
        Shape (n, n_fluxes, rows, cols), or None when the store has no fluxes array.
    """
    n = moisture_block.shape[0]
    if flux_block is not None:
        if "fluxes" not in group:
            raise ValueError("this run store was created without a fluxes array")
        if flux_block.shape[0] != n:
            raise ValueError(f"flux block has {flux_block.shape[0]} days but moisture block has {n}")
    group["moisture"][t0 : t0 + n] = moisture_block
    if flux_block is not None:
        group["fluxes"][t0 : t0 + n] = flux_block
    group.attrs["days_written"] = t0 + n


def t1():
    """Blocks land at their day indices and read back, including across a chunk boundary."""
    import tempfile
    from pathlib import Path

    from terrasim2.f.create_run_store import create_run_store
    from terrasim2.f.run_model import _inputs
    from terrasim2.k.run_store_params import RunStoreParams

    g = create_run_store(_inputs(), 1, Path(tempfile.mkdtemp()) / "run.zarr", RunStoreParams(chunk_days=2))
    write_run_block(g, 0, np.full((2, 2, 3), 1.0), np.full((2, 1, 2, 3), 10.0))
    write_run_block(g, 2, np.full((1, 2, 3), 2.0), np.full((1, 1, 2, 3), 20.0))
    assert np.array_equal(g["moisture"][:, 0, 0], [1.0, 1.0, 2.0])
    assert np.array_equal(g["fluxes"][:, 0, 0, 0], [10.0, 10.0, 20.0])
    assert g.attrs["days_written"] == 3


def t2():
    """A flux block for a store without fluxes, or of the wrong length, is rejected."""
    import tempfile
    from pathlib import Path

    from terrasim2.f.create_run_store import create_run_store
    from terrasim2.f.run_model import _inputs
    from terrasim2.k.run_store_params import RunStoreParams

    base = Path(tempfile.mkdtemp())
    no_flux = create_run_store(_inputs(), 1, base / "a.zarr", RunStoreParams(record_fluxes=False))
    with_flux = create_run_store(_inputs(), 1, base / "b.zarr", RunStoreParams())
    for g, fb in ((no_flux, np.zeros((1, 1, 2, 3))), (with_flux, np.zeros((2, 1, 2, 3)))):
        try:
            write_run_block(g, 0, np.zeros((1, 2, 3)), fb)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def t():
    t1()
    t2()
