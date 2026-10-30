from pathlib import Path

import numpy as np
import zarr

from terrasim2.k.model_inputs import ModelInputs
from terrasim2.k.run_store_params import RunStoreParams

RUN_STORE_VERSION = 1


def create_run_store(inputs: ModelInputs, n_fluxes: int, folder: Path, params: RunStoreParams) -> zarr.Group:
    """Create an empty zarr store for a run's histories.

    Layout of the group at ``folder``:

        moisture   float64 (T, rows, cols), mm, chunked (chunk_days, chunk_rows, chunk_cols)
        fluxes     float64 (T, n_fluxes, rows, cols), mm, same chunking with all fluxes
                   together; absent when ``params.record_fluxes`` is False
        attrs      version, dates (ISO strings), complete (False until the run
                   finishes), units, store params as applied, and the inputs' meta

    Any existing store at ``folder`` is replaced.

    Parameters
    ----------
    inputs : ModelInputs
        Gives T, rows, cols, dates and meta.
    n_fluxes : int, dimensionless
        Length of the flux axis the step produces. Ignored when fluxes are not recorded.
    folder : Path
    params : RunStoreParams

    Returns
    -------
    zarr.Group
        Open for writing.
    """
    rows, cols = inputs.shape
    chunk_rows, chunk_cols = min(params.chunk_rows, rows), min(params.chunk_cols, cols)
    chunk_days = min(params.chunk_days, inputs.n_days)

    group = zarr.open_group(Path(folder), mode="w")
    group.create_array("moisture", shape=(inputs.n_days, rows, cols), chunks=(chunk_days, chunk_rows, chunk_cols), dtype="float64", fill_value=np.nan)
    if params.record_fluxes:
        group.create_array("fluxes", shape=(inputs.n_days, n_fluxes, rows, cols), chunks=(chunk_days, n_fluxes, chunk_rows, chunk_cols), dtype="float64", fill_value=np.nan)
    group.attrs.update(
        {
            "version": RUN_STORE_VERSION,
            "complete": False,
            "days_written": 0,
            "dates": [str(d) for d in inputs.dates],
            "units": "mm",
            "store_params": {
                "chunk_days": chunk_days,
                "chunk_rows": chunk_rows,
                "chunk_cols": chunk_cols,
                "write_every_days": params.write_every_days,
                "record_fluxes": params.record_fluxes,
            },
            "meta": inputs.meta,
        }
    )
    return group


def t1():
    """Creates the arrays with the requested chunking, clipped to the grid, marked incomplete."""
    import tempfile

    from terrasim2.f.run_model import _inputs

    folder = Path(tempfile.mkdtemp()) / "run.zarr"
    g = create_run_store(_inputs(), 3, folder, RunStoreParams(chunk_days=2, chunk_rows=100, chunk_cols=2))
    assert g["moisture"].shape == (3, 2, 3) and g["moisture"].chunks == (2, 2, 2)
    assert g["fluxes"].shape == (3, 3, 2, 3) and g["fluxes"].chunks == (2, 3, 2, 2)
    assert g.attrs["complete"] is False and g.attrs["dates"] == ["2024-01-01", "2024-01-02", "2024-01-03"]
    assert np.isnan(g["moisture"][0]).all()


def t2():
    """Without record_fluxes there is no fluxes array."""
    import tempfile

    from terrasim2.f.run_model import _inputs

    g = create_run_store(_inputs(), 3, Path(tempfile.mkdtemp()) / "run.zarr", RunStoreParams(record_fluxes=False))
    assert "moisture" in g and "fluxes" not in g


def t():
    t1()
    t2()
