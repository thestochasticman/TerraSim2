from pathlib import Path

import numpy as np
import zarr


def read_moisture_day(store_folder: Path, t: int) -> bytes:
    """One day's moisture field as little-endian float32 bytes, row-major.

    Only days the writer has marked as written can be read, so this is safe
    while the run is still going.

    Parameters
    ----------
    store_folder : Path
        A zarr store written by ``run_model``.
    t : int, dimensionless
        Day index.

    Returns
    -------
    bytes
        ``rows * cols * 4`` bytes, millimetres (mm) as float32.

    Raises
    ------
    IndexError
        If ``t`` is negative or not yet written.
    """
    group = zarr.open_group(Path(store_folder), mode="r")
    written = int(group.attrs.get("days_written", 0))
    if not 0 <= t < written:
        raise IndexError(f"day {t} is not available: {written} of {group['moisture'].shape[0]} days written")
    return np.asarray(group["moisture"][t], dtype="<f4").tobytes(order="C")


def t():
    """Bytes decode back to the stored field; days beyond days_written are refused."""
    import tempfile

    from terrasim2.f.create_run_store import create_run_store
    from terrasim2.f.run_model import _inputs
    from terrasim2.f.write_run_block import write_run_block
    from terrasim2.k.run_store_params import RunStoreParams

    folder = Path(tempfile.mkdtemp()) / "run.zarr"
    g = create_run_store(_inputs(), 1, folder, RunStoreParams())
    day = np.arange(6, dtype=np.float64).reshape(1, 2, 3) * 1.5
    write_run_block(g, 0, day, np.zeros((1, 1, 2, 3)))
    raw = read_moisture_day(folder, 0)
    assert len(raw) == 2 * 3 * 4
    assert np.array_equal(np.frombuffer(raw, dtype="<f4").reshape(2, 3), day[0].astype(np.float32))
    for bad in (1, -1):
        try:
            read_moisture_day(folder, bad)
        except IndexError:
            pass
        else:
            raise AssertionError(f"expected IndexError for day {bad}")
