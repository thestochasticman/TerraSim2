from pathlib import Path

import numpy as np

from app.api.f.find_inputs import DEV_SITES
from app.api.f.find_vegetation import find_vegetation
from app.api.k.run_request import RunRequest
from terrasim2.f.load_vegetation_map import load_vegetation_map


def compute_demand_factor(request: RunRequest, inputs_roots: tuple[Path, ...] = (DEV_SITES,)) -> np.ndarray | None:
    """What a request multiplies each cell's reference evapotranspiration by, or None for the reference itself.

    With ``cover_strength`` above 0 and a vegetation map prepared for the
    site, each cell's crop coefficient from its persistent greenness,
    divided by the grid's mean coefficient, is raised to that power; cells
    the map did not see take 1. The division keeps the site's mean demand
    at the reference, so the strength moves only the pattern: which cells
    go on transpiring through the dry season relative to the site's usual
    cover. Otherwise the reference demand stands everywhere, and a
    strength without a map is simply not used.

    Parameters
    ----------
    request : RunRequest
    inputs_roots : tuple of Path
        Where ``find_vegetation`` looks.

    Returns
    -------
    ndarray or None, dimensionless
        A field of the site's shape, positive everywhere, or None.
    """
    if request.cover_strength == 0:
        return None
    folder = find_vegetation(request.stub, inputs_roots)
    if folder is None:
        return None
    coefficient = load_vegetation_map(folder).compute_crop_coefficient()
    relative = coefficient / np.nanmean(coefficient)
    return np.where(np.isfinite(relative), relative**request.cover_strength, 1.0)


def t():
    """No strength or no map gives None; with both, the factor averages 1 over the grid, trees demand more than
    pasture, nothing is NaN, and the strength is a power."""
    from terrasim2.k.vegetation_map import VegetationMap

    assert compute_demand_factor(RunRequest(stub="tarrawarra")) is None
    assert compute_demand_factor(RunRequest(stub="example", cover_strength=1.0)) is None, "the example region has no map"
    factor = compute_demand_factor(RunRequest(stub="tarrawarra", cover_strength=1.0))
    vegetation = load_vegetation_map(find_vegetation("tarrawarra"))
    assert isinstance(factor, np.ndarray) and factor.shape == vegetation.shape and np.isfinite(factor).all() and np.all(factor > 0)
    assert abs(factor.mean() - 1.0) < 1e-6, "the site's mean demand stays at the reference"
    assert factor[vegetation.class_index == 1].mean() > factor[vegetation.class_index == 0].mean()
    assert np.allclose(compute_demand_factor(RunRequest(stub="tarrawarra", cover_strength=0.5)), np.sqrt(factor))
    assert isinstance(vegetation, VegetationMap)
