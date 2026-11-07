import json
import sys
from pathlib import Path

from app.api.f.compute_root_depth_field import compute_root_depth_field
from app.api.k.run_request import RunRequest
from terrasim2.f.load_model_inputs import load_model_inputs
from terrasim2.f.run_model import run_model
from terrasim2.f.step_bucket_model import step_bucket_model
from terrasim2.f.step_routed_bucket_model import step_routed_bucket_model
from terrasim2.f.step_subsurface_bucket_model import step_subsurface_bucket_model
from terrasim2.k.bucket_flux import BucketFlux
from terrasim2.k.bucket_model_params import BucketModelParams
from terrasim2.k.routed_bucket_flux import RoutedBucketFlux
from terrasim2.k.run_store_params import RunStoreParams
from terrasim2.k.subsurface_bucket_flux import SubsurfaceBucketFlux
from terrasim2.k.subsurface_bucket_params import SubsurfaceBucketParams

# The step each request name runs, and the enum that names its fluxes.
STEPS = {
    "bucket": (step_bucket_model, BucketFlux),
    "routed": (step_routed_bucket_model, RoutedBucketFlux),
    "subsurface": (step_subsurface_bucket_model, SubsurfaceBucketFlux),
}


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
    inputs = _prepare_inputs(request, inputs_folder)
    step, flux_enum = STEPS[request.step]
    if request.step == "subsurface":
        params = SubsurfaceBucketParams(stress_exponent=request.stress_exponent, leak_fraction=request.leak_fraction, rain_hours=request.rain_hours, lateral_multiplier=request.lateral_multiplier, aspect_strength=request.aspect_strength)
    else:
        params = BucketModelParams(stress_exponent=request.stress_exponent)
    run_model(
        step,
        inputs,
        params,
        folder=Path(store_folder),
        store_params=RunStoreParams(
            chunk_days=request.chunk_days,
            write_every_days=request.write_every_days,
            record_fluxes=request.record_fluxes,
        ),
        flux_names=[f.name.lower() for f in flux_enum],
    )
    return Path(store_folder)


def _prepare_inputs(request: RunRequest, inputs_folder: Path):
    """Load the inputs at the request's root depth, so capacity and the soil hydraulics agree, and set the start state.

    The depth is one value, or a field by vegetation class when the request
    names a tree depth and the site folder beside the inputs holds a map.
    """
    inputs = load_model_inputs(inputs_folder)
    if inputs.soil is not None:
        depth = compute_root_depth_field(request, (Path(inputs_folder).parents[1],))
        inputs.grid.capacity = inputs.soil.compute_capacity(depth)
        inputs.root_depth = depth
    inputs.grid.moisture[:] = request.initial_fullness * inputs.grid.capacity
    return inputs


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
    subsurface = execute_run(RunRequest(stub="example", step="subsurface", rain_hours=6, write_every_days=31), find_inputs("example"), Path(tempfile.mkdtemp()) / "subsurface.zarr")
    sub = load_run_result(subsurface)
    assert sub.n_fluxes == 6 and zarr.open_group(subsurface, mode="r").attrs["flux_names"][3] == "leak"
    assert np.isfinite(sub.get_moisture(30)).all()
    treed = _prepare_inputs(RunRequest(stub="tarrawarra", root_depth=0.3, tree_root_depth=1.0), find_inputs("tarrawarra"))
    assert isinstance(treed.root_depth, np.ndarray) and set(np.unique(treed.root_depth)) == {0.3, 1.0}, "tree cells take the tree depth"
    assert np.nanmean(treed.grid.capacity[treed.root_depth == 1.0]) > np.nanmean(treed.grid.capacity[treed.root_depth == 0.3])
    prepared = _prepare_inputs(RunRequest(stub="example", root_depth=1.0), find_inputs("example"))
    assert prepared.root_depth == 1.0, "the soil hydraulics must be built at the request's depth, not the manifest's"
    assert prepared.grid.capacity.mean() > 2 * np.load(find_inputs("example") / "capacity.npy").mean()


if __name__ == "__main__":
    req_path, inputs_folder, store_folder = sys.argv[1:4]
    execute_run(RunRequest.model_validate_json(Path(req_path).read_text()), Path(inputs_folder), Path(store_folder))
