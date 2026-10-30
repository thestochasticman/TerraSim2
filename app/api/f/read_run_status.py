import json
import time
from pathlib import Path

import zarr


def read_run_status(store_folder: Path) -> dict:
    """What state a run store is in, safe to call while the run is writing it.

    Parameters
    ----------
    store_folder : Path
        A zarr store written by ``run_model``. May not exist yet.

    Returns
    -------
    dict
        ``status``: ``"missing"`` (no store), ``"running"`` (store exists,
        run not finished) or ``"complete"``. For an existing store also
        ``days_written``, ``n_days``, ``rows``, ``cols``, ``dates`` (ISO
        strings), ``has_fluxes`` and ``meta``.
    """
    store_folder = Path(store_folder)
    if not (store_folder / "zarr.json").exists():
        return {"status": "missing"}
    group = _open_with_retry(store_folder)
    attrs = dict(group.attrs)
    moisture = group["moisture"]
    return {
        "status": "complete" if attrs.get("complete") else "running",
        "days_written": int(attrs.get("days_written", 0)),
        "n_days": int(moisture.shape[0]),
        "rows": int(moisture.shape[1]),
        "cols": int(moisture.shape[2]),
        "dates": attrs.get("dates", []),
        "has_fluxes": "fluxes" in group,
        "meta": attrs.get("meta", {}),
    }


def _open_with_retry(folder: Path, attempts: int = 5) -> zarr.Group:
    """The writer rewrites the group's metadata after each block; retry briefly if we catch it mid-write."""
    for i in range(attempts):
        try:
            return zarr.open_group(folder, mode="r")
        except (json.JSONDecodeError, FileNotFoundError, KeyError, ValueError):
            if i == attempts - 1:
                raise
            time.sleep(0.05)
    raise RuntimeError("unreachable")


def t():
    """Missing, running and complete stores are told apart, and the counts come from the store."""
    import tempfile

    import numpy as np

    from terrasim2.f.create_run_store import create_run_store
    from terrasim2.f.run_model import _inputs
    from terrasim2.f.write_run_block import write_run_block
    from terrasim2.k.run_store_params import RunStoreParams

    folder = Path(tempfile.mkdtemp()) / "run.zarr"
    assert read_run_status(folder) == {"status": "missing"}
    g = create_run_store(_inputs(), 3, folder, RunStoreParams())
    s = read_run_status(folder)
    assert s["status"] == "running" and s["days_written"] == 0 and s["n_days"] == 3 and (s["rows"], s["cols"]) == (2, 3)
    write_run_block(g, 0, np.zeros((2, 2, 3)), np.zeros((2, 3, 2, 3)))
    assert read_run_status(folder)["days_written"] == 2
    g.attrs["complete"] = True
    s = read_run_status(folder)
    assert s["status"] == "complete" and s["has_fluxes"] and s["dates"][0] == "2024-01-01"
