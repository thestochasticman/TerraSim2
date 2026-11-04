import json
import sys
from pathlib import Path

from app.api.k.run_request import RunRequest
from terrasim2.f.load_model_inputs import load_model_inputs
from terrasim2.f.run_model import run_model
from terrasim2.f.step_bucket_model import step_bucket_model
from terrasim2.f.step_routed_bucket_model import step_routed_bucket_model
from terrasim2.k.bucket_flux import BucketFlux
from terrasim2.k.bucket_model_params import BucketModelParams
from terrasim2.k.routed_bucket_flux import RoutedBucketFlux
from terrasim2.k.run_store_params import RunStoreParams

# The step each request name runs, and the enum that names its fluxes.
STEPS = {"bucket": (step_bucket_model, BucketFlux), "routed": (step_routed_bucket_model, RoutedBucketFlux)}


def execute_run(request: RunRequest, inputs_folder: Path, store_folder: Path) -> Path:
    """Run the requested step for a request, writing the store as it goes.

    This is the worker the service launches in its own process, and the
    same function a notebook can call directly.

    Usage as a process:
        python -m app.api.f.execute_run <request.json> <inputs_folder> <store_folder>

    Parameters
    ----------
    request : RunRequest
    inputs_folder : Path
        A prepared ``model_inputs`` folder.
    store_folder : Path
        Where the zarr store goes. Replaced if present.

    Returns
    -------
    Path
        ``store_folder``.
    """
    inputs = load_model_inputs(inputs_folder)
    if inputs.soil is not None:
        inputs.grid.capacity = inputs.soil.compute_capacity(request.root_depth)
    inputs.grid.moisture[:] = request.initial_fullness * inputs.grid.capacity
    step, flux_enum = STEPS[request.step]
    run_model(
        step,
        inputs,
        BucketModelParams(stress_exponent=request.stress_exponent),
        folder=Path(store_folder),
        store_params=RunStoreParams(
            chunk_days=request.chunk_days,
            write_every_days=request.write_every_days,
            record_fluxes=request.record_fluxes,
        ),
        flux_names=[f.name.lower() for f in flux_enum],
    )
    return Path(store_folder)


def t():
    """A run on the example site writes a complete store that starts from the requested fullness."""
    import tempfile

    import numpy as np

    from app.api.f.find_inputs import find_inputs
    from terrasim2.f.load_run_result import load_run_result

    store = execute_run(RunRequest(stub="example", initial_fullness=0.25, write_every_days=7), find_inputs("example"), Path(tempfile.mkdtemp()) / "store.zarr")
    result = load_run_result(store)
    assert result.n_days == 31
    first = result.get_moisture(0)
    assert np.isfinite(first).all()
    assert 0 < first.mean() < 40, "day 0 should sit near a quarter of a 30 cm capacity, moved by one day of forcing"
    deep = execute_run(RunRequest(stub="example", initial_fullness=0.25, root_depth=1.0, write_every_days=31), find_inputs("example"), Path(tempfile.mkdtemp()) / "deep.zarr")
    assert load_run_result(deep).get_moisture(0).mean() > 2 * first.mean(), "deeper roots mean a larger capacity and a larger start"
    import zarr

    routed = execute_run(RunRequest(stub="example", step="routed", write_every_days=31), find_inputs("example"), Path(tempfile.mkdtemp()) / "routed.zarr")
    assert load_run_result(routed).n_fluxes == 4
    assert zarr.open_group(routed, mode="r").attrs["flux_names"] == ["infiltration", "inflow", "runoff", "evaporation"]


if __name__ == "__main__":
    req_path, inputs_folder, store_folder = sys.argv[1:4]
    execute_run(RunRequest.model_validate_json(Path(req_path).read_text()), Path(inputs_folder), Path(store_folder))
